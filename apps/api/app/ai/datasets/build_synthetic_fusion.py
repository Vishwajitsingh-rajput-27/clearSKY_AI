from __future__ import annotations

import argparse
import json
import math
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class SyntheticFusionConfig:
    output_dir: Path = Path("data")
    target_count: int = 1000
    image_size: int = 512
    train_fraction: float = 0.8
    val_fraction: float = 0.1
    min_mask_percent: float = 5.0
    max_mask_percent: float = 70.0
    seed: int = 2026
    skip_existing: bool = True


REGIONS = [
    "ner_hills",
    "brahmaputra_floodplain",
    "agriculture_grid",
    "coastal_delta",
    "dryland_mosaic",
    "urban_periurban",
    "forest_plantation",
    "river_valley",
]


def main() -> None:
    config = load_config(parse_args())
    started = time.perf_counter()
    rows = build_dataset(config)
    write_manifests(rows, config)
    elapsed = time.perf_counter() - started
    print(
        json.dumps(
            {
                "scene_count": len(rows),
                "output_dir": str(config.output_dir),
                "elapsed_seconds": round(elapsed, 3),
                "train_manifest": str(config.output_dir / "manifests" / "train.json"),
                "val_manifest": str(config.output_dir / "manifests" / "val.json"),
                "test_manifest": str(config.output_dir / "manifests" / "test.json"),
            },
            indent=2,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a fast synthetic multi-sensor fusion dataset."
    )
    parser.add_argument("--config", default="configs/synthetic_fusion_1000.json")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--target-count", type=int, default=None)
    parser.add_argument("--image-size", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def load_config(args: argparse.Namespace) -> SyntheticFusionConfig:
    payload: dict[str, Any] = {}
    config_path = Path(args.config)
    if config_path.exists():
        payload = json.loads(config_path.read_text(encoding="utf-8"))

    overrides = {
        "output_dir": args.output_dir,
        "target_count": args.target_count,
        "image_size": args.image_size,
        "seed": args.seed,
    }
    payload.update({key: value for key, value in overrides.items() if value is not None})

    if args.overwrite:
        payload["skip_existing"] = False

    if "output_dir" in payload:
        payload["output_dir"] = Path(payload["output_dir"])

    return SyntheticFusionConfig(**payload)


def build_dataset(config: SyntheticFusionConfig) -> list[dict[str, Any]]:
    raw_dir = config.output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []

    for index in range(1, config.target_count + 1):
        scene_id = f"scene-{index:04d}"
        scene_dir = raw_dir / scene_id
        if config.skip_existing and is_complete_scene(scene_dir):
            rows.append(manifest_row(scene_id))
            continue

        scene_dir.mkdir(parents=True, exist_ok=True)
        rng = np.random.default_rng(config.seed + index)
        region = REGIONS[(index - 1) % len(REGIONS)]
        clear = generate_clear_scene(config.image_size, rng=rng, region=region)
        before = generate_temporal_reference(clear, rng=rng, shift=-1)
        after = generate_temporal_reference(clear, rng=rng, shift=1)
        cloudy, mask, mask_percent = apply_clouds(clear, rng=rng, config=config)
        sentinel1 = generate_sentinel1_like(clear, mask, rng=rng)
        sentinel2 = generate_sentinel2_like(clear, rng=rng)
        dem = generate_dem_like(config.image_size, rng=rng, region=region)

        Image.fromarray(clear, mode="RGB").save(scene_dir / "clear.png")
        Image.fromarray(cloudy, mode="RGB").save(scene_dir / "cloudy.png")
        Image.fromarray((mask.astype(np.uint8) * 255), mode="L").save(scene_dir / "cloud_mask.png")
        Image.fromarray(before, mode="RGB").save(scene_dir / "ref-before.png")
        Image.fromarray(after, mode="RGB").save(scene_dir / "ref-after.png")
        write_multiband_tif(scene_dir / "sentinel1.tif", sentinel1)
        write_multiband_tif(scene_dir / "sentinel2.tif", sentinel2)
        write_multiband_tif(scene_dir / "dem.tif", dem[None, ...])
        write_metadata(scene_dir, scene_id=scene_id, region=region, mask_percent=mask_percent)

        rows.append(manifest_row(scene_id))
        if index == 1 or index % 50 == 0:
            print(f"built {index}/{config.target_count}: {scene_id}")

    return rows


def generate_clear_scene(size: int, *, rng: np.random.Generator, region: str) -> np.ndarray:
    import cv2

    y = np.linspace(0, 1, size, dtype=np.float32)[:, None]
    x = np.linspace(0, 1, size, dtype=np.float32)[None, :]
    base = np.zeros((size, size, 3), dtype=np.float32)

    if "hills" in region or "valley" in region:
        base[..., 0] = 58 + 45 * x + 20 * y
        base[..., 1] = 105 + 55 * y
        base[..., 2] = 75 + 35 * x
    elif "dryland" in region:
        base[..., 0] = 145 + 45 * x
        base[..., 1] = 126 + 25 * y
        base[..., 2] = 82 + 18 * x
    elif "coastal" in region or "floodplain" in region:
        base[..., 0] = 70 + 25 * x
        base[..., 1] = 118 + 35 * y
        base[..., 2] = 91 + 35 * x
    else:
        base[..., 0] = 82 + 45 * x
        base[..., 1] = 122 + 38 * y
        base[..., 2] = 70 + 24 * x

    draw_fields(base, rng=rng)
    draw_water(base, rng=rng, region=region)
    draw_roads_and_urban(base, rng=rng, region=region)
    draw_texture(base, rng=rng, region=region)

    noise = rng.normal(0, 4.5, size=base.shape)
    image = np.clip(base + noise, 0, 255).astype(np.uint8)
    return cv2.GaussianBlur(image, (3, 3), 0)


def draw_fields(base: np.ndarray, *, rng: np.random.Generator) -> None:
    import cv2

    height, width = base.shape[:2]
    palette = np.array(
        [
            [78, 130, 66],
            [111, 151, 78],
            [139, 142, 82],
            [93, 118, 89],
            [162, 151, 98],
            [70, 112, 72],
        ],
        dtype=np.float32,
    )
    rows = int(rng.integers(7, 14))
    cols = int(rng.integers(8, 16))
    for row in range(rows):
        for col in range(cols):
            x0 = col * width // cols
            x1 = (col + 1) * width // cols
            y0 = row * height // rows
            y1 = (row + 1) * height // rows
            margin = int(rng.integers(1, 4))
            color = palette[int(rng.integers(0, len(palette)))] + rng.normal(0, 10, 3)
            cv2.rectangle(
                base,
                (x0 + margin, y0 + margin),
                (x1 - margin, y1 - margin),
                color.clip(35, 210).tolist(),
                -1,
            )


def draw_water(base: np.ndarray, *, rng: np.random.Generator, region: str) -> None:
    import cv2

    height, width = base.shape[:2]
    if "dryland" in region and rng.random() < 0.7:
        return

    if "coastal" in region:
        water = np.array(
            [
                [0, int(height * 0.70)],
                [width, int(height * rng.uniform(0.58, 0.78))],
                [width, height],
                [0, height],
            ],
            dtype=np.int32,
        )
        cv2.fillPoly(base, [water], color=(43, 85, 105))
        return

    points = []
    for x_value in np.linspace(-width * 0.1, width * 1.1, 9):
        y_value = height * rng.uniform(0.35, 0.75) + math.sin(x_value / width * math.pi * 2) * 30
        points.append([int(x_value), int(y_value)])
    river = np.array(points, dtype=np.int32)
    cv2.polylines(base, [river], isClosed=False, color=(42, 82, 102), thickness=int(width * 0.035))


def draw_roads_and_urban(base: np.ndarray, *, rng: np.random.Generator, region: str) -> None:
    import cv2

    height, width = base.shape[:2]
    road_count = 2 if "urban" not in region else 6
    for _ in range(road_count):
        offset = int(rng.integers(-width // 4, width))
        color = tuple((rng.normal([124, 118, 98], [10, 8, 8])).clip(70, 170))
        cv2.line(base, (offset, 0), (offset + int(rng.integers(-120, 180)), height), color, 2)

    if "urban" in region:
        for _ in range(80):
            x0 = int(rng.integers(0, width - 12))
            y0 = int(rng.integers(0, height - 12))
            side = int(rng.integers(4, 13))
            color = tuple((rng.normal([150, 148, 139], [18, 18, 16])).clip(85, 210))
            cv2.rectangle(base, (x0, y0), (x0 + side, y0 + side), color, -1)


def draw_texture(base: np.ndarray, *, rng: np.random.Generator, region: str) -> None:
    import cv2

    height, width = base.shape[:2]
    count = 120 if "hills" in region or "forest" in region else 45
    for _ in range(count):
        center = (int(rng.integers(0, width)), int(rng.integers(0, height)))
        radius = int(rng.integers(2, 8))
        color = tuple((rng.normal([95, 116, 86], [25, 20, 16])).clip(45, 170))
        cv2.circle(base, center, radius, color, -1)


def generate_temporal_reference(
    clear: np.ndarray,
    *,
    rng: np.random.Generator,
    shift: int,
) -> np.ndarray:
    import cv2

    changed = clear.astype(np.float32)
    scale = 1.0 + shift * rng.uniform(0.015, 0.045)
    bias = shift * rng.uniform(1.0, 5.0)
    changed = changed * scale + bias
    changed[..., 1] *= 1.0 + shift * rng.uniform(0.01, 0.04)
    noise = rng.normal(0, 2.5, size=changed.shape)
    changed = np.clip(changed + noise, 0, 255).astype(np.uint8)
    return cv2.GaussianBlur(changed, (3, 3), 0)


def apply_clouds(
    clear: np.ndarray,
    *,
    rng: np.random.Generator,
    config: SyntheticFusionConfig,
) -> tuple[np.ndarray, np.ndarray, float]:
    import cv2

    height, width = clear.shape[:2]
    for _ in range(16):
        cloud_layer = np.zeros((height, width), dtype=np.uint8)
        for _blob in range(int(rng.integers(4, 12))):
            center = (int(rng.integers(0, width)), int(rng.integers(0, height)))
            axes = (
                int(rng.integers(width * 0.05, width * 0.23)),
                int(rng.integers(height * 0.04, height * 0.16)),
            )
            cv2.ellipse(cloud_layer, center, axes, float(rng.uniform(-40, 40)), 0, 360, 255, -1)
        kernel = max(25, int(width * rng.uniform(0.05, 0.11)) | 1)
        soft = cv2.GaussianBlur(cloud_layer, (kernel, kernel), sigmaX=kernel / 4)
        cloud_mask = soft > int(rng.integers(65, 135))
        shadow_mask = shift_mask(cloud_mask, dx=int(width * rng.uniform(0.035, 0.075)), dy=int(height * rng.uniform(0.04, 0.09)))
        invalid = np.logical_or(cloud_mask, shadow_mask)
        coverage = float(invalid.mean() * 100)
        if config.min_mask_percent <= coverage <= config.max_mask_percent:
            break
    else:
        raise RuntimeError("Could not synthesize valid cloud coverage")

    cloud_alpha = (soft.astype(np.float32) / 255.0 * rng.uniform(0.65, 0.9))[..., None]
    shadow_alpha = shadow_mask.astype(np.float32)[..., None] * rng.uniform(0.22, 0.42)
    cloudy = clear.astype(np.float32) * (1.0 - shadow_alpha)
    cloudy = cloudy * (1.0 - cloud_alpha) + np.array([242, 244, 238], dtype=np.float32) * cloud_alpha
    return np.clip(cloudy, 0, 255).astype(np.uint8), invalid, coverage


def generate_sentinel1_like(
    clear: np.ndarray,
    mask: np.ndarray,
    *,
    rng: np.random.Generator,
) -> np.ndarray:
    import cv2

    gray = cv2.cvtColor(clear, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
    edges = cv2.Canny((gray * 255).astype(np.uint8), 50, 140).astype(np.float32) / 255.0
    water = (clear[..., 2].astype(np.float32) > clear[..., 1].astype(np.float32) * 1.05).astype(np.float32)
    vv = 0.22 + gray * 0.48 + edges * 0.20 - water * 0.16 + rng.normal(0, 0.035, gray.shape)
    vh = 0.16 + gray * 0.32 + edges * 0.12 - water * 0.10 + rng.normal(0, 0.04, gray.shape)
    vv[mask] += rng.normal(0, 0.015, vv[mask].shape)
    vh[mask] += rng.normal(0, 0.015, vh[mask].shape)
    return (np.stack([vv, vh]).clip(0, 1) * 255).astype(np.uint8)


def generate_sentinel2_like(clear: np.ndarray, *, rng: np.random.Generator) -> np.ndarray:
    rgb = clear.astype(np.float32) / 255.0
    blue = rgb[..., 2]
    green = rgb[..., 1]
    red = rgb[..., 0]
    nir = (green * 0.62 + red * 0.18 + rng.normal(0.08, 0.035, green.shape)).clip(0, 1)
    red_edge1 = (red * 0.55 + nir * 0.28 + 0.04).clip(0, 1)
    red_edge2 = (red * 0.42 + nir * 0.42 + 0.05).clip(0, 1)
    red_edge3 = (red * 0.35 + nir * 0.50 + 0.05).clip(0, 1)
    narrow_nir = (nir * 0.92 + green * 0.08).clip(0, 1)
    swir1 = (red * 0.34 + green * 0.18 + 0.18 + rng.normal(0, 0.025, red.shape)).clip(0, 1)
    swir2 = (red * 0.28 + blue * 0.12 + 0.16 + rng.normal(0, 0.025, red.shape)).clip(0, 1)
    stack = np.stack([blue, green, red, red_edge1, red_edge2, red_edge3, nir, narrow_nir, swir1, swir2])
    return (stack.clip(0, 1) * 255).astype(np.uint8)


def generate_dem_like(
    size: int,
    *,
    rng: np.random.Generator,
    region: str,
) -> np.ndarray:
    import cv2

    y = np.linspace(0, 1, size, dtype=np.float32)[:, None]
    x = np.linspace(0, 1, size, dtype=np.float32)[None, :]
    relief = 0.25 * x + 0.25 * y
    if "hills" in region or "valley" in region:
        relief += 0.35 * np.sin(x * math.pi * 4) * np.cos(y * math.pi * 3)
    elif "coastal" in region or "floodplain" in region:
        relief *= 0.25
    else:
        relief += 0.10 * np.sin(x * math.pi * 2 + y * math.pi * 3)
    noise = cv2.GaussianBlur(rng.normal(0, 0.05, (size, size)).astype(np.float32), (21, 21), 0)
    dem = relief + noise
    dem = (dem - dem.min()) / max(1e-6, float(dem.max() - dem.min()))
    return (dem * 255).astype(np.uint8)


def shift_mask(mask: np.ndarray, *, dx: int, dy: int) -> np.ndarray:
    shifted = np.zeros_like(mask)
    source_y0 = max(0, -dy)
    source_y1 = mask.shape[0] - max(0, dy)
    source_x0 = max(0, -dx)
    source_x1 = mask.shape[1] - max(0, dx)
    target_y0 = max(0, dy)
    target_y1 = target_y0 + (source_y1 - source_y0)
    target_x0 = max(0, dx)
    target_x1 = target_x0 + (source_x1 - source_x0)
    shifted[target_y0:target_y1, target_x0:target_x1] = mask[source_y0:source_y1, source_x0:source_x1]
    return shifted


def write_multiband_tif(path: Path, array: np.ndarray) -> None:
    try:
        import rasterio
        from rasterio.transform import from_origin
    except ImportError as exc:
        raise SystemExit("rasterio is required. Install with: pip install rasterio") from exc

    count, height, width = array.shape
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=count,
        dtype=array.dtype,
        transform=from_origin(0, 0, 10, 10),
        compress="deflate",
    ) as dataset:
        dataset.write(array)


def is_complete_scene(scene_dir: Path) -> bool:
    required = [
        "cloudy.png",
        "cloud_mask.png",
        "clear.png",
        "sentinel1.tif",
        "sentinel2.tif",
        "dem.tif",
        "ref-before.png",
        "ref-after.png",
        "metadata.json",
    ]
    return scene_dir.exists() and all((scene_dir / name).exists() for name in required)


def manifest_row(scene_id: str) -> dict[str, Any]:
    base = f"../raw/{scene_id}"
    return {
        "scene_id": scene_id,
        "cloudy_liss4": f"{base}/cloudy.png",
        "cloud_mask": f"{base}/cloud_mask.png",
        "target": f"{base}/clear.png",
        "sentinel1": f"{base}/sentinel1.tif",
        "sentinel2": f"{base}/sentinel2.tif",
        "dem": f"{base}/dem.tif",
        "temporal_refs": [
            f"{base}/ref-before.png",
            f"{base}/ref-after.png",
        ],
    }


def write_manifests(rows: list[dict[str, Any]], config: SyntheticFusionConfig) -> None:
    manifest_dir = config.output_dir / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    train_end = int(len(rows) * config.train_fraction)
    val_end = train_end + int(len(rows) * config.val_fraction)
    splits = {
        "train": rows[:train_end],
        "val": rows[train_end:val_end],
        "test": rows[val_end:],
    }
    for split, split_rows in splits.items():
        (manifest_dir / f"{split}.json").write_text(
            json.dumps(split_rows, indent=2),
            encoding="utf-8",
        )


def write_metadata(
    scene_dir: Path,
    *,
    scene_id: str,
    region: str,
    mask_percent: float,
) -> None:
    metadata = {
        "scene_id": scene_id,
        "source": "synthetic-fast-generator",
        "purpose": "pipeline bootstrap and pretraining only",
        "region_style": region,
        "synthetic_invalid_mask_percent": round(mask_percent, 3),
        "cloudy_liss4_is_synthetic": True,
        "auxiliary_modalities_are_synthetic": True,
        "not_for_scientific_validation": True,
    }
    (scene_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
