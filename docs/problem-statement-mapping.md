# Problem Statement Mapping

Problem statement: **Generative AI-Based Cloud Removal and Reconstruction for LISS-IV Satellite Imagery**.

This document maps required ISRO/NRSC expectations to implemented or scaffolded ClearSky AI capabilities.

## Exact Required Term Checklist

- LISS-IV imagery
- cloud removal
- reconstruction
- spatial consistency
- spectral consistency
- temporal information
- Sentinel-1
- Sentinel-2
- DEM
- evaluation
- operational deployment
- comparative model assessment

| Requirement | ClearSky AI Mapping | Status |
| --- | --- | --- |
| LISS-IV imagery | Primary domain is LISS-IV-style optical imagery. Upload validation accepts TIFF/GeoTIFF/JP2 and normal preview images. AI dataset loader is named and structured for LISS-IV manifests. | Implemented foundation, training data required for official validation |
| Cloud removal | Baseline detects bright/low-saturation cloud pixels, cleans the mask, and reconstructs masked regions. | Implemented CPU baseline |
| Reconstruction | OpenCV Telea inpainting fallback reconstructs cloud/shadow regions. Attention U-Net and Swin-UNet reconstruction modules are scaffolded for training. | Baseline implemented, AI training-ready |
| Spatial consistency | Morphological mask cleanup, patch tiling/merge, edge loss, difference maps, and QGIS outputs support spatial continuity review. | Implemented/scaffolded |
| Spectral consistency | Spectral Angle Mapper, spectral consistency score, and spectral consistency loss are included. Evaluation reports expose spectral metrics. | Implemented evaluation, training loss scaffolded |
| Temporal information | Dataset and model architecture support optional temporal references for fusion. Methodology defines temporal co-registration and feature fusion workflow. | Training-ready scaffold |
| Sentinel-1 | Multi-sensor fusion network and dataset schema include optional Sentinel-1 SAR inputs. Methodology defines SAR preprocessing and fusion workflow. | Training-ready scaffold |
| Sentinel-2 | Multi-sensor fusion network and dataset schema include optional Sentinel-2 inputs. Methodology defines co-registration and optical auxiliary fusion. | Training-ready scaffold |
| DEM | Dataset schema and fusion support include optional DEM. Methodology defines elevation/slope/aspect use for terrain-aware shadow and reconstruction. | Training-ready scaffold |
| Evaluation | Full-reference metrics: PSNR, SSIM, RMSE, MAE, SAM, spectral consistency, runtime. No-reference/proxy metrics: quality score, cloud reduction, spectral proxy, runtime. | Implemented |
| Operational deployment | Vercel frontend, Render backend, Neon PostgreSQL, Cloudinary/Supabase storage, CPU-safe fallback, environment-driven configuration. | Implemented deployment-ready foundation |
| Comparative model assessment | Benchmark rows compare Traditional masking, OpenCV inpainting, Attention U-Net, Swin-UNet, and Multi-sensor fusion with used/simulated/fallback flags. | Implemented framework |

## Detailed Mapping

### LISS-IV Imagery

ClearSky AI is designed around LISS-IV workflows:

- Upload and inference support TIFF/GeoTIFF/JP2 where runtime libraries support them.
- Raster metadata extraction preserves CRS, transform, bounds, driver, dtype, and band count.
- Dataset loader expects LISS-IV cloudy image, cloud mask, and target cloud-free image.
- Documentation and UI use LISS-IV as the primary operational sensor context.

### Cloud Removal

The baseline removes cloud contamination through:

- Brightness/saturation cloud detection.
- Mask morphology.
- Invalid-region reconstruction.
- Difference-map QA.

This is a CPU-safe baseline, not a final trained generative model.

### Reconstruction

Implemented:

- OpenCV Telea inpainting.
- Enhancement and difference map.
- Persisted reconstructed output URL.

Training-ready:

- Attention U-Net reconstruction.
- Swin-UNet reconstruction.
- Multi-sensor fusion reconstruction.

### Spatial Consistency

Spatial consistency is addressed through:

- Cleaned contiguous masks.
- Patch tiling and merge service.
- Edge loss.
- Difference maps.
- QGIS-compatible outputs.

### Spectral Consistency

Spectral preservation is addressed through:

- SAM metric.
- Spectral consistency score.
- Spectral consistency loss.
- Full-reference scoring when target imagery exists.

### Temporal Information

Temporal references are supported as optional dataset/model inputs. The intended operational flow is cloud-filtered neighboring acquisitions co-registered to the LISS-IV target grid.

### Sentinel-1

Sentinel-1 SAR support is represented through:

- Optional dataset field.
- SAR fusion module.
- Multi-sensor fusion network.
- Methodology for VV/VH terrain-corrected feature alignment.

### Sentinel-2

Sentinel-2 support is represented through:

- Optional dataset field.
- Sentinel-2 fusion module.
- Multi-sensor fusion network.
- Co-registration and resampling methodology.

### DEM

DEM support is represented through:

- Optional DEM dataset field.
- DEM fusion support.
- Terrain-aware methodology for elevation, slope, and aspect.

### Evaluation

Full-reference evaluation is used when a clear target is available:

- PSNR.
- SSIM.
- RMSE.
- MAE.
- SAM.
- Spectral consistency score.

No-reference evaluation is used otherwise:

- No-reference quality score.
- Cloud reduction score.
- Spectral consistency proxy.
- Runtime.

### Operational Deployment

The platform is deployable with:

- Vercel.
- Render.
- Neon PostgreSQL.
- Cloudinary or Supabase.
- CPU-safe baseline inference.
- Demo mode for public validation without GPU.

### Comparative Model Assessment

The benchmark framework compares:

- Traditional masking.
- OpenCV inpainting.
- Attention U-Net.
- Swin-UNet.
- Multi-sensor fusion.

The UI/API marks which model was actually used and which rows are research estimates.
