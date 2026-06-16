# ClearSky AI

Production-oriented platform for **Generative AI-Based Cloud Removal and Reconstruction for LISS-IV Satellite Imagery**.

ClearSky AI is built as an operational ISRO/NRSC-style product surface, not a notebook demo. Public users can upload cloudy satellite imagery, run a CPU-safe reconstruction workflow, inspect cloud and shadow masks, compare reconstruction outputs, review evaluation metrics, benchmark model families, and download generated products.

## Current Capabilities

- Next.js 14 research dashboard with shadcn/ui, TanStack Query, Zustand, Recharts, and dark/light mode.
- FastAPI backend with SQLAlchemy, SQLite local fallback, Neon PostgreSQL readiness, CORS, structured responses, logging, and safe upload validation.
- CPU-safe baseline inference: cloud mask, cloud shadow mask, OpenCV Telea inpainting, image enhancement, difference map, metrics, and persisted assets.
- GeoTIFF/TIFF/JP2-ready geospatial services using Rasterio/GDAL when available, with CRS/transform/metadata preservation and QGIS-compatible output manifests.
- PyTorch research package for U-Net cloud segmentation, Attention U-Net, Swin-UNet, temporal fusion, Sentinel-1, Sentinel-2, DEM, and multi-sensor fusion training.
- Evaluation and benchmarking engine with full-reference and no-reference metrics.
- Judge demo mode with a deterministic synthetic satellite-like sample and no GPU dependency.
- Authentication, user projects, user history, storage limits, model registry, research exports, and operational workflow views.
- Explainability outputs: attention maps, confidence maps, reconstruction confidence score, and AI recommendations.
- Public deployment path for Vercel, Render, Neon PostgreSQL, Cloudinary, and Supabase Storage.

## Monorepo Layout

```text
clearSKY_AI/
  apps/
    api/       FastAPI backend, AI, geospatial, inference, evaluation, demo services
    web/       Next.js frontend dashboard
  docs/        Architecture, methodology, API, datasets, deployment, judge pitch
  docker-compose.yml
  render.yaml
  deployment.md
```

## Quick Start

Backend:

```bash
cd apps/api
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

Open:

```text
Frontend: http://127.0.0.1:3000
Backend:  http://127.0.0.1:8000/api/health
Demo:     POST http://127.0.0.1:8000/api/demo/run
```

## Core Public Workflows

1. Upload PNG/JPG/TIFF/GeoTIFF/JP2 imagery.
2. Run reconstruction with `POST /api/inference/run`.
3. View original image, cloud mask, shadow mask, reconstruction, and difference map.
4. Review geospatial metadata and evaluation metrics.
5. Compare Traditional masking, OpenCV inpainting, Attention U-Net, Swin-UNet, and Multi-sensor fusion.
6. Inspect attention maps, confidence maps, reconstruction confidence, and AI recommendations.
7. Download image products, QGIS manifest, analysis GeoTIFF where available, evaluation reports, research reports, CSV, and PDF exports.
8. Run Judge Demo Mode from the landing page or dashboard without uploading data.

## Documentation

- [Architecture](docs/architecture.md)
- [Methodology](docs/methodology.md)
- [API](docs/api.md)
- [Dataset Strategy](docs/dataset.md)
- [Deployment](docs/deployment.md)
- [Model Training](docs/model-training.md)
- [Demo Flow](docs/demo-flow.md)
- [Problem Statement Mapping](docs/problem-statement-mapping.md)
- [Judge Pitch](docs/judge-pitch.md)

## Validation Commands

```bash
cd apps/api
.venv/Scripts/python.exe -m ruff check .
.venv/Scripts/python.exe -m pytest

cd ../web
npm run typecheck
npm run lint
npm run build
```

## Honesty Note

The public deployment is designed to run without trained weights. When trained AI checkpoints are unavailable, requested AI models fall back to the CPU-safe OpenCV pipeline and the API returns `fallback_used=true` where applicable. Judge Demo Mode uses a synthetic satellite-like scene and clearly labels it as synthetic; it is a workflow demonstration, not a claim of trained-model accuracy on official LISS-IV scenes.

## Known Limitations

- Trained U-Net, Attention U-Net, Swin-UNet, and multi-sensor fusion weights are not bundled.
- Sentinel-1, Sentinel-2, DEM, and temporal fusion modules are training-ready, but public demo inference uses OpenCV fallback unless checkpoints are configured.
- Auto-created database tables are acceptable for hackathon deployment; Alembic migrations should replace auto-create for long-term production governance.
- Demo imagery is synthetic and deterministic, not an official ISRO/NRSC LISS-IV scene.

## Future Upgrades

- Train and publish validated model checkpoints on curated LISS-IV cloudy/cloud-free pairs.
- Add automated auxiliary data discovery for Sentinel-1, Sentinel-2, DEM, and temporal references.
- Add signed private storage URLs and stricter per-project access policies.
- Add background job orchestration for long-running large-scene processing.
