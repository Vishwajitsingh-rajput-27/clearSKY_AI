# Dataset Strategy

## Target Sensor

The primary target is LISS-IV imagery. The platform is structured to support LISS-IV optical scenes, cloud masks, cloud-free targets, temporal references, Sentinel-1 SAR, Sentinel-2 optical data, and DEM features.

## Required Training Records

Each training sample should be represented by a manifest row containing:

```text
cloudy_liss4_path
cloud_mask_path
target_cloud_free_path
optional_shadow_mask_path
optional_sentinel1_path
optional_sentinel2_path
optional_dem_path
optional_temporal_reference_paths
scene_id
sensor
acquisition_date
region
cloud_percent
split=train|validation|test
```

## LISS-IV Data

Purpose:

- Primary cloudy optical input.
- Target output grid for reconstruction.
- Evaluation against cloud-free reference where available.

Preprocessing:

- Validate raster.
- Preserve CRS and transform.
- Select preview/analysis bands.
- Tile into patches with overlap.
- Normalize per band.

## Cloud and Shadow Labels

Ideal labels:

- Thick cloud.
- Thin cloud.
- Cloud shadow.
- Clear land/water.

Sources:

- Manual annotation.
- QA masks where available.
- Synthetic cloud overlay for pretraining.
- Weak labels from brightness/saturation and temporal differences.

## Temporal References

Temporal references should include nearby acquisitions with lower cloud cover. They support:

- Recovery of land-cover patterns under cloud.
- Vegetation continuity.
- Reduced hallucination.

Risks:

- Seasonal changes.
- Crop-stage differences.
- Registration errors.

## Sentinel-1

Sentinel-1 SAR supports cloud-penetrating structure:

- VV/VH channels.
- Terrain correction.
- Speckle filtering.
- Co-registration to LISS-IV grid.

Useful for:

- Water boundaries.
- Urban edges.
- Floodplain structure.
- Terrain-visible features under cloud.

## Sentinel-2

Sentinel-2 supports auxiliary optical information:

- RGB/NIR/SWIR features.
- Cloud-filtered reference dates.
- Co-registration and resampling to LISS-IV grid.

Risks:

- Resolution mismatch.
- Spectral response mismatch.
- Cloud contamination in reference imagery.

## DEM

DEM features:

- Elevation.
- Slope.
- Aspect.

Use cases:

- Terrain-aware shadow detection.
- Mountain region reconstruction.
- Spatial consistency in high-relief regions.

## Splits

Recommended split strategy:

- Train: multiple regions and seasons.
- Validation: held-out dates from known regions.
- Test: held-out regions.
- Demo: synthetic sample only, not counted as scientific validation.

## Benchmark Dataset

Benchmark samples should include:

- Cloudy input.
- Cloud mask.
- Shadow mask.
- Cloud-free target where available.
- Auxiliary S1/S2/DEM references.
- Expected metadata.

Metrics should be reported per region, land cover, cloud fraction, and sensor availability.
