from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class GeospatialExportResult:
    path: Path | None
    qgis_folder: Path
    manifest_path: Path
    fallback_reason: str | None


def export_analysis_ready_geotiff(
    *,
    image_rgb: np.ndarray,
    output_path: Path,
    reference_profile: dict[str, Any] | None,
    crs: Any | None,
    transform: Any | None,
) -> Path | None:
    try:
        import rasterio
    except ImportError:
        return None

    output_path.parent.mkdir(parents=True, exist_ok=True)
    height, width = image_rgb.shape[:2]
    profile = build_output_profile(
        reference_profile=reference_profile,
        width=width,
        height=height,
        crs=crs,
        transform=transform,
    )
    data = image_rgb.transpose(2, 0, 1).astype(np.uint8)

    with rasterio.open(output_path, "w", **profile) as dataset:
        dataset.write(data)
        dataset.set_band_description(1, "red")
        dataset.set_band_description(2, "green")
        dataset.set_band_description(3, "blue")

    return output_path


def scale_transform_for_resize(
    transform: Any | None,
    *,
    original_width: int,
    original_height: int,
    output_width: int,
    output_height: int,
) -> Any | None:
    if transform is None:
        return None

    if original_width == output_width and original_height == output_height:
        return transform

    try:
        from affine import Affine

        scale_x = original_width / output_width
        scale_y = original_height / output_height
        return transform * Affine.scale(scale_x, scale_y)
    except Exception:
        return transform


def create_qgis_output_folder(
    *,
    qgis_folder: Path,
    metadata: dict[str, Any],
    products: dict[str, Path | str],
    analysis_geotiff_path: Path | None,
) -> GeospatialExportResult:
    qgis_folder.mkdir(parents=True, exist_ok=True)
    styles_dir = qgis_folder / "styles"
    styles_dir.mkdir(exist_ok=True)
    write_qgis_rgb_style(styles_dir / "rgb_preview.qml")
    manifest = {
        "metadata": metadata,
        "products": {key: str(path) for key, path in products.items()},
        "analysis_geotiff": str(analysis_geotiff_path) if analysis_geotiff_path else None,
        "qgis_notes": [
            "Open analysis_ready_reconstruction.tif in QGIS when available.",
            "Use styles/rgb_preview.qml for RGB raster display.",
        ],
    }
    manifest_path = qgis_folder / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (qgis_folder / "README.txt").write_text(
        "\n".join(
            [
                "clearSKY AI QGIS Output",
                "",
                "Files in this folder are generated for desktop GIS inspection.",
                "Load analysis_ready_reconstruction.tif in QGIS when present.",
                "Apply styles/rgb_preview.qml for RGB preview styling.",
            ]
        ),
        encoding="utf-8",
    )
    return GeospatialExportResult(
        path=analysis_geotiff_path,
        qgis_folder=qgis_folder,
        manifest_path=manifest_path,
        fallback_reason=(
            None
            if analysis_geotiff_path
            else "rasterio_unavailable_or_non_geospatial_input"
        ),
    )


def build_output_profile(
    *,
    reference_profile: dict[str, Any] | None,
    width: int,
    height: int,
    crs: Any | None,
    transform: Any | None,
) -> dict[str, Any]:
    profile = dict(reference_profile or {})
    profile.update(
        {
            "driver": "GTiff",
            "height": height,
            "width": width,
            "count": 3,
            "dtype": "uint8",
            "compress": "lzw",
            "tiled": True,
            "blockxsize": 256,
            "blockysize": 256,
            "interleave": "pixel",
            "BIGTIFF": "IF_SAFER",
        }
    )

    if crs is not None:
        profile["crs"] = crs
    else:
        profile.pop("crs", None)

    if transform is not None:
        profile["transform"] = transform
    else:
        profile.pop("transform", None)

    profile.pop("nodata", None)
    return profile


def write_qgis_rgb_style(path: Path) -> None:
    path.write_text(
        """<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.34">
  <pipe>
    <rasterrenderer type="multibandcolor" redBand="1" greenBand="2" blueBand="3">
      <rasterTransparency/>
    </rasterrenderer>
  </pipe>
</qgis>
""",
        encoding="utf-8",
    )
