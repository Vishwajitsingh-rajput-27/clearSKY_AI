from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import settings
from app.core.exceptions import AppError
from app.services.metadata_service import build_raster_metadata

GEOSPATIAL_EXTENSIONS = {".tif", ".tiff", ".jp2", ".j2k"}


@dataclass(frozen=True)
class RasterReadResult:
    rgb: np.ndarray
    bands: np.ndarray | None
    metadata: dict[str, Any]
    profile: dict[str, Any] | None
    crs: Any | None
    transform: Any | None
    is_geospatial: bool
    reader: str


def read_raster(path: Path) -> RasterReadResult:
    suffix = path.suffix.lower()

    if suffix in GEOSPATIAL_EXTENSIONS:
        try:
            return read_with_rasterio(path)
        except ImportError as exc:
            if suffix in {".jp2", ".j2k"}:
                raise AppError(
                    "JP2 support requires Rasterio/GDAL in the runtime.",
                    code="geospatial_runtime_missing",
                ) from exc
        except AppError:
            raise
        except Exception as exc:
            raise AppError(
                "Could not read geospatial raster.",
                code="invalid_geospatial_raster",
                details=str(exc),
            ) from exc

    return read_with_pillow(path)


def read_with_rasterio(path: Path) -> RasterReadResult:
    import rasterio
    from rasterio.enums import Resampling

    with rasterio.open(path) as dataset:
        if dataset.width * dataset.height > settings.max_inference_pixels:
            raise AppError(
                "Image is too large for CPU inference.",
                code="image_too_large",
                details={
                    "pixels": dataset.width * dataset.height,
                    "max_pixels": settings.max_inference_pixels,
                },
            )

        band_indexes = select_preview_bands(dataset.count)
        bands = dataset.read()
        preview = dataset.read(
            band_indexes,
            out_dtype="float32",
            resampling=Resampling.nearest,
        )
        rgb = bands_to_rgb(preview)
        metadata = build_raster_metadata(
            path=path,
            width=dataset.width,
            height=dataset.height,
            band_count=dataset.count,
            dtype=dataset.dtypes[0] if dataset.dtypes else None,
            driver=dataset.driver,
            crs=dataset.crs,
            transform=dataset.transform,
            bounds=dataset.bounds,
            nodata=dataset.nodata,
            is_geospatial=dataset.crs is not None or dataset.transform is not None,
        ).to_public_dict()
        metadata.update(
            {
                "reader": "rasterio",
                "preview_bands": list(band_indexes),
                "descriptions": [description for description in dataset.descriptions],
            }
        )

        return RasterReadResult(
            rgb=rgb,
            bands=bands,
            metadata=metadata,
            profile=dataset.profile.copy(),
            crs=dataset.crs,
            transform=dataset.transform,
            is_geospatial=bool(metadata["is_geospatial"]),
            reader="rasterio",
        )


def read_with_pillow(path: Path) -> RasterReadResult:
    try:
        image = Image.open(path)
        image = ImageOps.exif_transpose(image)
        if image.width * image.height > settings.max_inference_pixels:
            raise AppError(
                "Image is too large for CPU inference.",
                code="image_too_large",
                details={
                    "pixels": image.width * image.height,
                    "max_pixels": settings.max_inference_pixels,
                },
            )

        rgb_image = image.convert("RGB")
        metadata = build_raster_metadata(
            path=path,
            width=image.width,
            height=image.height,
            band_count=len(image.getbands()),
            dtype=str(np.array(image).dtype),
            driver=image.format,
            is_geospatial=False,
        ).to_public_dict()
        metadata.update({"reader": "pillow", "mode": image.mode})
        return RasterReadResult(
            rgb=np.array(rgb_image),
            bands=None,
            metadata=metadata,
            profile=None,
            crs=None,
            transform=None,
            is_geospatial=False,
            reader="pillow",
        )
    except UnidentifiedImageError as exc:
        raise AppError("Could not read uploaded image.", code="invalid_image") from exc
    except Image.DecompressionBombError as exc:
        raise AppError("Image is too large for safe processing.", code="image_too_large") from exc


def select_preview_bands(band_count: int) -> tuple[int, int, int]:
    if band_count >= 3:
        return (1, 2, 3)

    return (1, 1, 1)


def bands_to_rgb(bands: np.ndarray) -> np.ndarray:
    if bands.ndim != 3:
        raise AppError("Raster bands must be three-dimensional.", code="invalid_raster_shape")

    rgb = np.stack([normalize_band(band) for band in bands[:3]], axis=-1)
    return rgb.astype(np.uint8)


def normalize_band(band: np.ndarray) -> np.ndarray:
    band = np.nan_to_num(band.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    low, high = np.percentile(band, [2, 98])
    if high <= low:
        high = float(np.max(band)) or 1.0
        low = float(np.min(band))

    scaled = (band - low) / max(high - low, 1e-6)
    return (scaled.clip(0, 1) * 255).round().astype(np.uint8)
