# Methodology

## Problem

Clouds and cloud shadows obscure optical satellite imagery. For LISS-IV imagery, useful reconstruction must preserve both spatial structure and spectral behavior while remaining operationally deployable.

## Baseline Workflow

1. Validate upload extension and file size.
2. Read image safely with Rasterio/GDAL for geospatial rasters or Pillow for normal images.
3. Normalize to RGB preview for browser-safe processing.
4. Generate cloud mask using brightness and saturation thresholds.
5. Clean cloud mask with morphological open/close/dilation.
6. Generate cloud shadow mask using dark-region logic outside cloud pixels.
7. Combine cloud and shadow masks into an invalid-pixel mask.
8. Run trained model if requested weights exist.
9. Fall back to OpenCV Telea inpainting on CPU when weights are unavailable.
10. Enhance reconstruction with contrast and sharpening.
11. Generate a difference heatmap.
12. Compute metrics and benchmark rows.
13. Persist outputs, metadata, and evaluation reports.

## Cloud Detection

The operational baseline identifies cloud candidates using:

- High value/brightness.
- Low saturation for white cloud regions.
- Very bright pixel override for thick clouds.
- Morphological cleanup to reduce speckle and fill small gaps.

This is intentionally conservative and CPU-safe. Research extensions should replace this with trained U-Net segmentation when labeled masks are available.

## Cloud Shadow Detection

The baseline identifies candidate shadows using:

- Low brightness.
- Non-zero saturation.
- Exclusion of detected cloud pixels.

Research extensions should use sun-sensor geometry, cloud displacement, DEM slope/aspect, and temporal consistency.

## Reconstruction

Current public fallback:

- OpenCV Telea inpainting over cloud and shadow masks.
- Contrast and sharpening enhancement.
- Difference map generation for visual QA.

Research path:

- Attention U-Net for local masked reconstruction.
- Swin-UNet for broader contextual reconstruction.
- Multi-sensor fusion network using LISS-IV, Sentinel-1 SAR, Sentinel-2, DEM, and temporal references.

## Spatial Consistency

Spatial consistency is protected by:

- Mask morphology before reconstruction.
- Patch tiling and merge utilities for large images.
- Difference maps for edge/artifact inspection.
- Edge loss in the training package.

## Spectral Consistency

Spectral consistency is measured and trained through:

- Spectral Angle Mapper.
- Spectral consistency score.
- Channel distribution preservation.
- Spectral consistency loss in the PyTorch metrics package.

## Temporal Fusion

Temporal fusion is represented in the AI research pipeline as optional reference stacks. The intended workflow is:

1. Select cloud-free or lower-cloud neighboring acquisitions.
2. Co-register to the cloudy LISS-IV scene.
3. Build temporal feature tensors.
4. Fuse temporal information in reconstruction decoder blocks.
5. Evaluate temporal gains using full-reference metrics where cloud-free target imagery exists.

## Sentinel-1 Fusion

Sentinel-1 SAR is valuable because it penetrates clouds and captures structural backscatter. The intended workflow:

1. Preprocess SAR to terrain-corrected, co-registered VV/VH features.
2. Normalize SAR channels.
3. Fuse SAR features with optical LISS-IV features through a SAR fusion encoder.
4. Use SAR information to preserve water, urban, and vegetation boundaries under cloud cover.

## Sentinel-2 Fusion

Sentinel-2 provides complementary optical bands and revisit frequency. The intended workflow:

1. Co-register Sentinel-2 references to LISS-IV grid.
2. Select RGB/NIR/SWIR-compatible channels.
3. Normalize and resample to model patch size.
4. Use Sentinel-2 features as auxiliary optical context for reconstruction.

## DEM Integration

DEM support provides terrain context for shadow and reconstruction:

- Elevation, slope, and aspect features.
- Terrain-aware shadow interpretation.
- Improved mountainous-area consistency.

## Evaluation

If ground truth is available:

- PSNR.
- SSIM.
- RMSE.
- MAE.
- Spectral Angle Mapper.
- Spectral consistency score.
- Processing time.

If ground truth is unavailable:

- No-reference quality score.
- Cloud reduction score.
- Spectral consistency proxy against non-cloudy original regions.
- Difference maps and runtime.

## Benchmarking

The platform compares:

- Traditional masking.
- OpenCV inpainting.
- Attention U-Net.
- Swin-UNet.
- Multi-sensor fusion.

Rows that are not actually executed are marked as research estimates in the UI/API.
