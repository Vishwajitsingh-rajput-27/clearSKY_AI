# Architecture

## Objective

ClearSky AI is an operational cloud detection, cloud shadow detection, and cloud-free reconstruction platform for LISS-IV-style satellite imagery. The system is designed for public deployment while preserving a research path for temporal, Sentinel-1, Sentinel-2, DEM, and deep learning fusion.

## System Architecture

```text
User browser
  -> Next.js 14 frontend on Vercel
  -> FastAPI backend on Render
  -> SQLAlchemy persistence
  -> Neon PostgreSQL in production or SQLite locally
  -> Cloudinary/Supabase/local asset storage
  -> CPU-safe OpenCV inference
  -> Optional PyTorch checkpoints when available
```

## Frontend Architecture

- App Router pages: landing, dashboard, upload, dataset explorer, cloud detection, reconstruction, evaluation, benchmarking, methodology, settings.
- shadcn/ui components for cards, buttons, tables, tabs, progress, dialogs, alerts, selects, inputs, sheets, skeletons, and tooltips.
- TanStack Query for API calls and mutations.
- Zustand for current project/result history and demo mode state.
- Recharts for evaluation and benchmark charts.
- Hydration-safe chart frame that avoids server/client mismatch for chart rendering.

## Backend Architecture

- FastAPI application with lifespan startup and table creation for local development.
- SQLAlchemy 2 models for scenes, jobs, assets, inference runs, and benchmark results.
- Uniform response envelope:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "message": null,
  "request_id": "..."
}
```

- Services:
  - `inference.py`: CPU-safe image processing pipeline.
  - `evaluation_engine.py`: full-reference and no-reference metrics.
  - `demo.py`: synthetic judge demo sample and cached demo runs.
  - `geotiff_reader.py`, `geotiff_writer.py`, `tiling_service.py`, `metadata_service.py`: geospatial workflow.
  - `storage.py`: local, Cloudinary, and Supabase persistence.
  - `inference_records.py`: shared persistence for normal and demo inference results.

## AI Research Architecture

The training-ready AI package lives under `apps/api/app/ai/`:

- `models/`: U-Net, Attention U-Net, Swin-UNet, temporal fusion, SAR/S2/DEM fusion modules.
- `datasets/`: patch-based LISS-IV manifest dataset loader.
- `training/`: config loading, patch training, validation, checkpoint saving.
- `inference/`: checkpoint loading and CPU fallback bridge.
- `metrics/`: spectral consistency, edge, SSIM, and reconstruction losses.
- `preprocessing/`: patch tiling and merge utilities.

## Geospatial Architecture

- TIFF/GeoTIFF/JP2 where GDAL supports the driver.
- Rasterio path preserves CRS, affine transform, bounds, dtype, band count, and raster profile.
- Pillow fallback preserves normal PNG/JPG workflows.
- Large rasters can be tiled into overlapping patches and merged.
- Reconstruction outputs can be exported as analysis-ready GeoTIFF when geospatial metadata exists.
- QGIS output folder includes a manifest and style-compatible preview products.

## Production Architecture

```text
Vercel
  NEXT_PUBLIC_API_BASE_URL=https://render-api

Render
  FastAPI Docker service
  DATABASE_URL=Neon
  STORAGE_PROVIDER=cloudinary|supabase
  ALLOWED_ORIGINS=https://vercel-domain

Neon PostgreSQL
  inference_runs
  benchmark_results
  assets
  scenes
  jobs

Cloudinary/Supabase
  original previews
  masks
  reconstructions
  difference maps
  reports
  QGIS manifests
```

## Operational Principles

- The public app must run on CPU.
- AI weights are optional and never required for uptime.
- Every output has a traceable asset row and public URL.
- Demo mode is synthetic and labeled.
- Evaluation reports are generated for reproducibility.
