# Automatic Sentinel Fusion Training With TeraBox Storage

This workflow avoids Google Drive for dataset and checkpoint storage.

It uses Colab's local `/content` disk while the job is running, then creates a
compact zip archive that you can upload to TeraBox.

Why this design:

```text
Colab local disk = faster for dataset writing and training
TeraBox = storage for final checkpoint/results archive
```

TeraBox is good for storing finished files, but it is not a reliable mounted
training filesystem in Colab. Do not train directly from a TeraBox web folder.

## What The Dataset Uses

The automatic builder uses public Earth Engine data:

```text
Sentinel-2 RGB proxy input and target
Sentinel-2 10-band optical stack
Sentinel-1 VV/VH SAR
SRTM DEM
Sentinel-2 before/after temporal references
Synthetic cloud and shadow masks over clear Sentinel-2 target
```

Important: this is Sentinel proxy pretraining. Final LISS-IV claims still need
Bhoonidhi LISS-IV fine-tuning and validation.

## Colab Setup

Run:

```bash
%%bash
cd /content
if [ ! -d clearSKY_AI ]; then
  git clone https://github.com/Vishwajitsingh-rajput-27/clearSKY_AI.git
else
  cd clearSKY_AI && git pull --ff-only
fi

cd /content/clearSKY_AI/apps/api
pip install -r requirements.txt
pip install -r requirements-dataset.txt
```

Authenticate Earth Engine once:

```bash
%%bash
cd /content/clearSKY_AI/apps/api
python -m app.ai.training.run_fusion_pipeline \
  --config configs/fusion_dataset_500_terabox_colab.json \
  --project YOUR_GOOGLE_CLOUD_PROJECT \
  --authenticate \
  --dry-run \
  --target-count 5
```

If Earth Engine works without a project for your account, remove this line:

```text
--project YOUR_GOOGLE_CLOUD_PROJECT
```

## 20-Scene Test

Always run this before 500 scenes:

```bash
%%bash
cd /content/clearSKY_AI/apps/api
python -m app.ai.training.run_fusion_pipeline \
  --config configs/fusion_dataset_500_terabox_colab.json \
  --project YOUR_GOOGLE_CLOUD_PROJECT \
  --target-count 20 \
  --profile fast \
  --device auto \
  --epochs 1 \
  --checkpoint-dir /content/clearsky_terabox_stage/sentinel_models/checkpoints_test \
  --summary-path /content/clearsky_terabox_stage/sentinel_models/checkpoints_test/fusion_pipeline_test_summary.json \
  --archive-path /content/clearsky_terabox_upload_test.zip \
  --skip-best-validation
```

This creates:

```text
/content/clearsky_terabox_stage/sentinel_fusion_data
/content/clearsky_terabox_stage/sentinel_models/checkpoints_test
/content/clearsky_terabox_upload_test.zip
```

Download `clearsky_terabox_upload_test.zip` from Colab, then upload it to
TeraBox.

## 500-Scene Automatic Run

After the 20-scene test passes:

```bash
%%bash
cd /content/clearSKY_AI/apps/api
python -m app.ai.training.run_fusion_pipeline \
  --config configs/fusion_dataset_500_terabox_colab.json \
  --project YOUR_GOOGLE_CLOUD_PROJECT \
  --profile fast \
  --device auto \
  --checkpoint-dir /content/clearsky_terabox_stage/sentinel_models/checkpoints_500_fast \
  --summary-path /content/clearsky_terabox_stage/sentinel_models/checkpoints_500_fast/fusion_pipeline_500_fast_summary.json \
  --archive-path /content/clearsky_terabox_upload_500_fast.zip \
  --skip-best-validation \
  --continue-on-error
```

This builds or reuses 500 Sentinel fusion scenes, trains all four models, then
creates:

```text
/content/clearsky_terabox_upload_500_fast.zip
```

That zip contains:

```text
checkpoints/
summaries/
manifests/
```

It does not include the full raw dataset by default, because that can be tens of
GB. The dataset can be regenerated from the same config.

## Include Raw Dataset In Archive

Only do this if Colab has enough free disk:

```bash
--archive-dataset
```

Example:

```bash
python -m app.ai.training.run_fusion_pipeline \
  --config configs/fusion_dataset_500_terabox_colab.json \
  --project YOUR_GOOGLE_CLOUD_PROJECT \
  --profile fast \
  --device auto \
  --checkpoint-dir /content/clearsky_terabox_stage/sentinel_models/checkpoints_500_fast \
  --summary-path /content/clearsky_terabox_stage/sentinel_models/checkpoints_500_fast/fusion_pipeline_500_fast_summary.json \
  --archive-path /content/clearsky_terabox_upload_500_fast_with_dataset.zip \
  --archive-dataset \
  --skip-best-validation \
  --continue-on-error
```

For 500 scenes, expect the raw-dataset archive to be very large.

## Full Serious Run

This can take many hours:

```bash
%%bash
cd /content/clearSKY_AI/apps/api
python -m app.ai.training.run_fusion_pipeline \
  --config configs/fusion_dataset_500_terabox_colab.json \
  --project YOUR_GOOGLE_CLOUD_PROJECT \
  --profile full \
  --device auto \
  --checkpoint-dir /content/clearsky_terabox_stage/sentinel_models/checkpoints_500_full \
  --summary-path /content/clearsky_terabox_stage/sentinel_models/checkpoints_500_full/fusion_pipeline_500_full_summary.json \
  --archive-path /content/clearsky_terabox_upload_500_full.zip \
  --continue-on-error
```

## Download And Upload To TeraBox

In Colab's file browser:

```text
/content/clearsky_terabox_upload_500_fast.zip
```

Download it to your computer, then upload it to TeraBox.

If the zip is too large, run the same pipeline without `--archive-dataset` and
store only checkpoints, summaries, and manifests in TeraBox.

## Resume Behavior

Completed scene folders are skipped. If Colab disconnects during dataset
creation, rerun the same command quickly. If Colab resets completely, local
`/content` data is lost unless you already downloaded/uploaded the archive.
