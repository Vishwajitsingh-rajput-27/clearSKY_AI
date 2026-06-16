# Demo Flow

## Purpose

Judge Demo Mode lets reviewers test the public deployment without uploading private data and without GPU inference. The sample is synthetic, deterministic, and clearly labeled.

## Demo Endpoints

```text
GET  /api/demo/sample
POST /api/demo/run
```

`GET /api/demo/sample` returns the cached demo result or creates it if missing.

`POST /api/demo/run` runs the cached demo by default. Use `?force=true` to regenerate the sample outputs.

## What the Demo Shows

- Synthetic satellite-like cloudy scene.
- Generated cloud mask.
- Generated shadow mask.
- CPU-safe OpenCV reconstruction.
- Difference map.
- Attention map and confidence map.
- AI recommendations and reconstruction confidence score.
- Full-reference metrics against the synthetic clear reference.
- Benchmark table with honest labels for executed vs estimated models.
- Downloadable reports, PDF/CSV research exports, and output assets.

## What the Demo Does Not Claim

- It is not a real ISRO/NRSC LISS-IV acquisition.
- It is not proof of trained model accuracy.
- It does not claim Sentinel-1/Sentinel-2/DEM fusion ran unless those inputs and weights are configured.

## 3-Minute Demo Script

### 0:00-0:20 - Open Product

"This is ClearSky AI, an operational dashboard for cloud detection and reconstruction for LISS-IV-style satellite imagery. The app is publicly deployable with Vercel, Render, Neon, and Cloudinary or Supabase Storage."

Action:

- Open landing page.
- Point to `Run sample demo`.

### 0:20-0:45 - Run Sample Demo

"For judging, we provide a synthetic satellite-like sample so the workflow can be tested without private data or GPU hardware. The UI states clearly that this is synthetic and not a real LISS-IV acquisition."

Action:

- Click `Run sample demo`.
- Wait for dashboard state.

### 0:45-1:15 - Show Outputs

"The same CPU-safe inference pipeline used for uploads generates the cloud mask, shadow mask, reconstruction, difference map, attention map, and confidence map. The system persists every output as an asset with a public URL."

Action:

- Open Upload or Reconstruction page.
- Show original, cloud mask, shadow mask, reconstructed output, difference map, attention map, and confidence map.
- Mention downloads.

### 1:15-1:45 - Show Evaluation

"Because the demo has a synthetic clear reference, it returns full-reference metrics: PSNR, SSIM, RMSE, MAE, SAM, spectral consistency, cloud reduction, quality score, and runtime."

Action:

- Open Evaluation page.
- Show metric cards, charts, explanations, report download links.

### 1:45-2:10 - Show Operational Workflow

"The Operational Workflow page adds the innovation layer: explainability, confidence scoring, time-series review, multi-date comparison, and recommendations such as Sentinel-1 fusion when cloud cover is high."

Action:

- Open Operational Workflow page.
- Show recommendation cards and explainability maps.
- Move the time-series and comparison sliders if multiple runs exist.

### 2:10-2:35 - Show Benchmarking and Research Export

"The benchmark page compares traditional masking, OpenCV inpainting, Attention U-Net, Swin-UNet, and multi-sensor fusion. Rows that were not executed are labeled as research estimates; the actual used model is OpenCV inpainting unless trained weights are configured."

Action:

- Open Benchmarking page.
- Show used model, fallback labels, stored benchmark records.
- Open Research Dashboard and generate PDF + CSV export if time permits.

### 2:35-2:55 - Show Geospatial and Deployment Readiness

"For GeoTIFF inputs, the backend preserves CRS, transform, band metadata, creates QGIS-compatible output, and can export an analysis-ready GeoTIFF. The public deployment path is CPU-safe and storage-provider agnostic."

Action:

- Mention Dataset Explorer or geospatial metadata card.
- Mention Render/Vercel/Neon/Cloudinary or Supabase.

### 2:55-3:00 - Close

"The current deployment is operational with a CPU baseline, honest fallback behavior, public-user authentication, and a training-ready AI research path for temporal, Sentinel-1, Sentinel-2, DEM, and Swin/Attention fusion models."

Action:

- End on dashboard or benchmark page.
