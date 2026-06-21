# Fusion Dataset Automation

This guide builds a 100-scene multi-sensor training dataset for the
`multi-sensor-fusion` model.

The builder uses Google Earth Engine to collect matched Sentinel-2, Sentinel-1,
and DEM chips, then creates synthetic cloud/shadow masks from clear optical
targets. The generated data is saved under `apps/api/data`, which is ignored by
Git.

## What Each Scene Contains

Each completed scene has this layout:

```text
apps/api/data/raw/scene-001/
  cloudy.png
  cloud_mask.png
  clear.png
  sentinel1.tif
  sentinel2.tif
  dem.tif
  ref-before.png
  ref-after.png
  metadata.json
```

The manifest row looks like this:

```json
{
  "scene_id": "scene-001",
  "cloudy_liss4": "../raw/scene-001/cloudy.png",
  "cloud_mask": "../raw/scene-001/cloud_mask.png",
  "target": "../raw/scene-001/clear.png",
  "sentinel1": "../raw/scene-001/sentinel1.tif",
  "sentinel2": "../raw/scene-001/sentinel2.tif",
  "dem": "../raw/scene-001/dem.tif",
  "temporal_refs": [
    "../raw/scene-001/ref-before.png",
    "../raw/scene-001/ref-after.png"
  ]
}
```

## One-Time Setup

Install the full API and dataset tooling on your data/training machine:

```powershell
cd C:\Users\JAISINGH\Documents\clearSKY_AI\apps\api
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dataset.txt
```

Authenticate Earth Engine once:

```powershell
python -m app.ai.datasets.build_fusion_100 --authenticate --project YOUR_GOOGLE_CLOUD_PROJECT --dry-run
```

If your Earth Engine account does not require a project argument, omit
`--project`.

## Build The 100-Scene Dataset

First run a search-only check:

```powershell
python -m app.ai.datasets.build_fusion_100 --project YOUR_GOOGLE_CLOUD_PROJECT --dry-run
```

Then download and build the dataset:

```powershell
python -m app.ai.datasets.build_fusion_100 --project YOUR_GOOGLE_CLOUD_PROJECT
```

The default config is:

```text
apps/api/configs/fusion_dataset_100.json
```

Useful overrides:

```powershell
python -m app.ai.datasets.build_fusion_100 --target-count 20
python -m app.ai.datasets.build_fusion_100 --max-cloud-percent 15
python -m app.ai.datasets.build_fusion_100 --start-date 2021-01-01 --end-date 2025-12-31
python -m app.ai.datasets.build_fusion_100 --overwrite
```

## What The Builder Does Automatically

For each scene, it:

1. Selects a region chip from the configured India region list.
2. Finds a low-cloud Sentinel-2 target image.
3. Finds a clear Sentinel-2 image before the target date.
4. Finds a clear Sentinel-2 image after the target date.
5. Finds a Sentinel-1 VV/VH median image near the target date.
6. Downloads SRTM DEM for the same chip.
7. Exports all rasters to the same 512 x 512 footprint.
8. Creates synthetic clouds and shadows over the clear target.
9. Writes `cloudy.png`, `cloud_mask.png`, and `clear.png`.
10. Validates file existence, dimensions, and band counts.
11. Writes `train.json`, `val.json`, and `test.json`.

## Train Fusion

After the dataset exists:

```powershell
python -m app.ai.training.train --config configs/ai_training.fusion.json
```

The best checkpoint will be:

```text
apps/api/models/checkpoints/multi-sensor-fusion/best.pt
```

Validate it:

```powershell
python -m app.ai.training.validate --config configs/ai_training.fusion.json
```

To train every AI model from the same generated dataset:

```powershell
python -m app.ai.training.train_all --device auto
```

See `docs/train-all-models.md` for the full all-model workflow.

## Important Notes

- `cloudy_liss4` is a Sentinel-2 optical proxy until Bhoonidhi/NRSC API access
  is available for real LISS-IV downloads.
- `sentinel1.tif` has two normalized bands: VV and VH.
- `sentinel2.tif` has ten normalized optical bands.
- `dem.tif` has one normalized elevation band.
- `cloud_mask.png` includes synthetic cloud and shadow pixels because the fusion
  model treats it as the invalid reconstruction mask.
- Keep generated `data/` and `models/` folders out of Git.
