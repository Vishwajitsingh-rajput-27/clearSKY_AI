from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset

from app.ai.preprocessing.patches import center_crop, random_crop


class LISS4CloudRemovalDataset(Dataset):
    """Patch-based dataset for LISS-IV cloud removal and multi-sensor fusion.

    Manifest rows support these keys:
    cloudy_liss4, cloud_mask, target, sentinel1, sentinel2, dem, temporal_refs.
    temporal_refs can be a JSON list, a semicolon-separated string, or a Python list.
    """

    def __init__(
        self,
        manifest_path: str | Path,
        *,
        patch_size: int = 256,
        split: str = "train",
        seed: int = 42,
    ) -> None:
        self.manifest_path = Path(manifest_path)
        self.root = self.manifest_path.parent
        self.rows = load_manifest(self.manifest_path)
        self.patch_size = patch_size
        self.split = split
        self.rng = np.random.default_rng(seed)

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor | str | None]:
        row = self.rows[index]
        arrays = {
            "cloudy": read_image(row["cloudy_liss4"], root=self.root, channels=3),
            "mask": read_image(row["cloud_mask"], root=self.root, channels=1),
            "target": read_image(row["target"], root=self.root, channels=3),
            "sentinel1": read_optional_image(row.get("sentinel1"), root=self.root, channels=2),
            "sentinel2": read_optional_image(row.get("sentinel2"), root=self.root, channels=10),
            "dem": read_optional_image(row.get("dem"), root=self.root, channels=1),
        }
        temporal_refs = read_temporal_refs(row.get("temporal_refs"), root=self.root)
        if temporal_refs is not None:
            arrays["temporal_refs"] = temporal_refs

        cropped = (
            random_crop(arrays, patch_size=self.patch_size, rng=self.rng)
            if self.split == "train"
            else center_crop(arrays, patch_size=self.patch_size)
        )
        sample: dict[str, torch.Tensor | str | None] = {
            "scene_id": row.get("scene_id", f"scene-{index}"),
            "cloudy": to_tensor(cropped["cloudy"]),
            "mask": to_tensor(cropped["mask"]),
            "target": to_tensor(cropped["target"]),
            "sentinel1": to_optional_tensor(cropped.get("sentinel1")),
            "sentinel2": to_optional_tensor(cropped.get("sentinel2")),
            "dem": to_optional_tensor(cropped.get("dem")),
            "temporal_refs": to_optional_temporal_tensor(cropped.get("temporal_refs")),
        }
        sample["mask"] = (sample["mask"] > 0.5).float()  # type: ignore[operator]
        sample["model_input"] = torch.cat([sample["cloudy"], sample["mask"]], dim=0)  # type: ignore[arg-type]
        return sample


def collate_liss4_batch(batch: list[dict[str, torch.Tensor | str | None]]) -> dict[str, Any]:
    output: dict[str, Any] = {
        "scene_id": [item["scene_id"] for item in batch],
        "cloudy": torch.stack([item["cloudy"] for item in batch]),  # type: ignore[list-item]
        "mask": torch.stack([item["mask"] for item in batch]),  # type: ignore[list-item]
        "target": torch.stack([item["target"] for item in batch]),  # type: ignore[list-item]
        "model_input": torch.stack([item["model_input"] for item in batch]),  # type: ignore[list-item]
    }

    for key in ("sentinel1", "sentinel2", "dem", "temporal_refs"):
        values = [item[key] for item in batch]
        output[key] = torch.stack(values) if all(value is not None for value in values) else None

    return output


def load_manifest(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("JSON manifest must contain a list of sample records")
        return [dict(item) for item in data]

    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            return [dict(row) for row in csv.DictReader(handle)]

    raise ValueError("Manifest must be .json or .csv")


def read_optional_image(path: str | None, *, root: Path, channels: int) -> np.ndarray | None:
    if not path:
        return None

    return read_image(path, root=root, channels=channels)


def read_image(path: str | Path, *, root: Path, channels: int) -> np.ndarray:
    resolved = resolve_path(path, root=root)

    if resolved.suffix.lower() in {".tif", ".tiff"}:
        try:
            return read_rasterio_image(resolved, channels=channels)
        except Exception:
            pass

    image = Image.open(resolved)
    if channels == 1:
        array = np.array(image.convert("L"), dtype=np.float32)[None, ...]
    else:
        array = np.array(image.convert("RGB"), dtype=np.float32).transpose(2, 0, 1)
        if channels > 3:
            padding = np.zeros((channels - 3, array.shape[1], array.shape[2]), dtype=np.float32)
            array = np.concatenate([array, padding], axis=0)
        array = array[:channels]

    return normalize_array(array)


def read_rasterio_image(path: Path, *, channels: int) -> np.ndarray:
    import rasterio

    with rasterio.open(path) as dataset:
        band_count = min(channels, dataset.count)
        array = dataset.read(list(range(1, band_count + 1))).astype(np.float32)

    if array.shape[0] < channels:
        padding = np.zeros(
            (channels - array.shape[0], array.shape[1], array.shape[2]),
            dtype=np.float32,
        )
        array = np.concatenate([array, padding], axis=0)

    return normalize_array(array[:channels])


def read_temporal_refs(value: Any, *, root: Path) -> np.ndarray | None:
    paths = parse_temporal_paths(value)
    if not paths:
        return None

    arrays = [read_image(path, root=root, channels=3) for path in paths]
    return np.stack(arrays, axis=0)


def parse_temporal_paths(value: Any) -> list[str]:
    if value is None or value == "":
        return []

    if isinstance(value, list):
        return [str(item) for item in value]

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            return [str(item) for item in json.loads(stripped)]
        return [item.strip() for item in stripped.split(";") if item.strip()]

    return []


def resolve_path(path: str | Path, *, root: Path) -> Path:
    resolved = Path(path)
    return resolved if resolved.is_absolute() else root / resolved


def normalize_array(array: np.ndarray) -> np.ndarray:
    array = array.astype(np.float32)
    max_value = float(np.nanmax(array)) if array.size else 1.0
    if max_value > 1.5:
        array = array / (65535.0 if max_value > 255 else 255.0)
    return np.nan_to_num(array, nan=0.0, posinf=1.0, neginf=0.0).clip(0, 1)


def to_tensor(array: np.ndarray | None) -> torch.Tensor:
    if array is None:
        raise ValueError("Required dataset array is missing")
    return torch.from_numpy(np.ascontiguousarray(array)).float()


def to_optional_tensor(array: np.ndarray | None) -> torch.Tensor | None:
    return None if array is None else to_tensor(array)


def to_optional_temporal_tensor(array: np.ndarray | None) -> torch.Tensor | None:
    return None if array is None else torch.from_numpy(np.ascontiguousarray(array)).float()
