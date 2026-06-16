from app.schemas.health import DependencyStatus


def get_geospatial_runtime_status() -> DependencyStatus:
    try:
        import rasterio
        from osgeo import gdal

        detail = f"rasterio {rasterio.__version__}; gdal {gdal.VersionInfo('RELEASE_NAME')}"
        return DependencyStatus(name="geospatial", ok=True, detail=detail)
    except Exception as exc:  # pragma: no cover - environment-specific diagnostic
        return DependencyStatus(name="geospatial", ok=False, detail=str(exc))
