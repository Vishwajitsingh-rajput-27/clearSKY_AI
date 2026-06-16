from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RasterMetadata:
    file_type: str
    driver: str | None
    width: int
    height: int
    band_count: int
    dtype: str | None
    crs: str | None
    transform: list[float] | None
    bounds: list[float] | None
    nodata: float | int | None
    is_geospatial: bool

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "file_type": self.file_type,
            "driver": self.driver,
            "width": self.width,
            "height": self.height,
            "band_count": self.band_count,
            "dtype": self.dtype,
            "crs": self.crs,
            "transform": self.transform,
            "bounds": self.bounds,
            "nodata": self.nodata,
            "is_geospatial": self.is_geospatial,
        }


def build_raster_metadata(
    *,
    path: Path,
    width: int,
    height: int,
    band_count: int,
    dtype: str | None = None,
    driver: str | None = None,
    crs: Any | None = None,
    transform: Any | None = None,
    bounds: Any | None = None,
    nodata: float | int | None = None,
    is_geospatial: bool = False,
) -> RasterMetadata:
    return RasterMetadata(
        file_type=path.suffix.lower().lstrip(".") or "unknown",
        driver=driver,
        width=int(width),
        height=int(height),
        band_count=int(band_count),
        dtype=str(dtype) if dtype is not None else None,
        crs=stringify_crs(crs),
        transform=transform_to_list(transform),
        bounds=bounds_to_list(bounds),
        nodata=normalize_number(nodata),
        is_geospatial=bool(is_geospatial),
    )


def stringify_crs(crs: Any | None) -> str | None:
    if crs is None:
        return None

    try:
        epsg = crs.to_epsg()
        if epsg:
            return f"EPSG:{epsg}"
    except Exception:
        pass

    return str(crs)


def transform_to_list(transform: Any | None) -> list[float] | None:
    if transform is None:
        return None

    try:
        return [float(value) for value in transform.to_gdal()]
    except Exception:
        try:
            return [float(value) for value in transform]
        except Exception:
            return None


def bounds_to_list(bounds: Any | None) -> list[float] | None:
    if bounds is None:
        return None

    if hasattr(bounds, "left"):
        return [
            float(bounds.left),
            float(bounds.bottom),
            float(bounds.right),
            float(bounds.top),
        ]

    try:
        return [float(value) for value in bounds]
    except Exception:
        return None


def normalize_number(value: float | int | None) -> float | int | None:
    if value is None:
        return None

    numeric = float(value)
    return int(numeric) if numeric.is_integer() else numeric
