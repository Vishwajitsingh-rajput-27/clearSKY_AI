# Judge Pitch

## One-Liner

ClearSky AI is a publicly deployable LISS-IV cloud removal platform that combines operational cloud/shadow masking, CPU-safe reconstruction, explainability, geospatial metadata preservation, evaluation, benchmarking, user project management, and a training-ready multi-sensor AI research pipeline.

## Why It Matters

Cloud contamination reduces the utility of optical satellite imagery for agriculture, disaster response, land-use monitoring, water bodies, forests, and urban planning. A useful solution must do more than generate a pretty image: it must preserve spatial structure, respect spectral behavior, quantify quality, and run reliably in public deployment.

## What Is Implemented

- Public Next.js dashboard.
- FastAPI backend.
- Upload validation and safe storage.
- Cloud mask and cloud shadow mask.
- OpenCV CPU reconstruction fallback.
- Difference map and downloadable outputs.
- Attention maps, confidence maps, reconstruction confidence score, and AI recommendations.
- GeoTIFF metadata preservation and QGIS manifest.
- Full-reference and no-reference evaluation.
- Model comparison framework.
- Authentication, user projects, history, and storage limits.
- Research dashboard with PDF/CSV/JSON/Markdown exports.
- Synthetic judge demo mode.
- Vercel/Render/Neon/Cloudinary/Supabase deployment path.

## Research Depth

The repository includes a training-ready PyTorch path for:

- U-Net cloud segmentation.
- Attention U-Net reconstruction.
- Swin-UNet reconstruction.
- Temporal fusion.
- Sentinel-1 SAR fusion.
- Sentinel-2 optical fusion.
- DEM fusion.
- Multi-sensor reconstruction.
- Spectral, edge, and SSIM losses.

## Honesty and Scientific Discipline

The current public app does not claim trained model performance without weights. If weights are unavailable, the API falls back to OpenCV and reports fallback status. Demo mode is synthetic and labeled as synthetic. Benchmark rows that are not executed are marked as research estimates.

## Why This Can Finish Top 3

- It looks and behaves like a deployable product, not a notebook.
- It directly maps to every requirement in the problem statement.
- It includes geospatial and operational concerns that many AI-only submissions miss.
- It has a clear research path for temporal, Sentinel-1, Sentinel-2, and DEM fusion.
- It has built-in metrics, benchmark reports, explainability, research exports, and a reliable judge demo.

## 3-Minute Pitch

### 0:00-0:30

"ClearSky AI solves generative cloud removal and reconstruction for LISS-IV-style satellite imagery as an operational product. Users can upload imagery, run reconstruction, inspect cloud and shadow masks, evaluate quality, compare models, and download outputs."

### 0:30-1:00

"The public deployment is CPU-safe. If trained weights are missing, it uses an OpenCV fallback and reports that honestly. This keeps the system reliable on Render while the PyTorch research path remains training-ready."

### 1:00-1:30

"The platform is geospatial-aware. GeoTIFF inputs preserve CRS, transform, bounds, band count, and metadata. Outputs include QGIS-compatible manifests and analysis-ready GeoTIFF support when geospatial metadata is available."

### 1:30-2:00

"Evaluation is first-class. With ground truth, we compute PSNR, SSIM, RMSE, MAE, SAM, spectral consistency, and runtime. Without ground truth, we compute no-reference quality, cloud reduction, spectral proxy metrics, and difference maps."

### 2:00-2:30

"The Operational Workflow page adds explainability and decision support: attention maps, confidence maps, time-series comparison, and recommendations such as Sentinel-1 fusion when cloud cover is high."

### 2:30-3:00

"The benchmark and research pages compare traditional masking, OpenCV inpainting, Attention U-Net, Swin-UNet, and multi-sensor fusion, then export PDF and CSV reports. One-click demo mode demonstrates the workflow without private imagery or GPU resources."
