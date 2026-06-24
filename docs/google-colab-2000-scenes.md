# Google Colab 2000-Scene Training

This workflow builds a 2,000-scene fusion dataset and trains all clearSKY AI
models from Google Colab.

If you need speed and do not need real Earth Engine scenes yet, use the synthetic
1000-scene path in `docs/fast-1000-scenes.md` first.

## Colab Runtime

Use:

```text
Runtime > Change runtime type > T4 GPU or better
```

Mount Google Drive because the dataset and checkpoints are too large for the
temporary Colab filesystem.

## One-Time Cell Order

### 1. Mount Drive

```python
from google.colab import drive
drive.mount("/content/drive")
```

### 2. Clone Or Update Repo

```bash
cd /content
if [ ! -d clearSKY_AI ]; then
  git clone https://github.com/Vishwajitsingh-rajput-27/clearSKY_AI.git
else
  cd clearSKY_AI && git pull
fi
```

### 3. Install Dependencies

```bash
cd /content/clearSKY_AI/apps/api
pip install -r requirements.txt
pip install -r requirements-dataset.txt
```

### 4. Authenticate Earth Engine

```python
import ee
ee.Authenticate()
ee.Initialize(project="YOUR_GOOGLE_CLOUD_PROJECT")
```

If your account does not require a project:

```python
ee.Initialize()
```

### 5. Dry Run Dataset Search

```bash
cd /content/clearSKY_AI/apps/api
python -m app.ai.datasets.build_fusion_100 \
  --config configs/fusion_dataset_2000_colab.json \
  --project YOUR_GOOGLE_CLOUD_PROJECT \
  --dry-run
```

### 6. Build 2,000 Scenes

```bash
cd /content/clearSKY_AI/apps/api
python -m app.ai.datasets.build_fusion_100 \
  --config configs/fusion_dataset_2000_colab.json \
  --project YOUR_GOOGLE_CLOUD_PROJECT
```

Output:

```text
/content/drive/MyDrive/clearSKY_AI/data/raw/scene-0001...
/content/drive/MyDrive/clearSKY_AI/data/manifests/train.json
/content/drive/MyDrive/clearSKY_AI/data/manifests/val.json
/content/drive/MyDrive/clearSKY_AI/data/manifests/test.json
```

### 7. Quick One-Epoch Training Test

```bash
cd /content/clearSKY_AI/apps/api
python -m app.ai.training.train_all \
  --profile fast \
  --device auto \
  --epochs 1 \
  --train-manifest /content/drive/MyDrive/clearSKY_AI/data/manifests/train.json \
  --val-manifest /content/drive/MyDrive/clearSKY_AI/data/manifests/val.json \
  --checkpoint-dir /content/drive/MyDrive/clearSKY_AI/models/checkpoints \
  --summary-path /content/drive/MyDrive/clearSKY_AI/models/checkpoints/train_all_smoke_summary.json \
  --skip-best-validation
```

### 8. Full All-Model Training

```bash
cd /content/clearSKY_AI/apps/api
python -m app.ai.training.train_all \
  --device auto \
  --train-manifest /content/drive/MyDrive/clearSKY_AI/data/manifests/train.json \
  --val-manifest /content/drive/MyDrive/clearSKY_AI/data/manifests/val.json \
  --checkpoint-dir /content/drive/MyDrive/clearSKY_AI/models/checkpoints \
  --summary-path /content/drive/MyDrive/clearSKY_AI/models/checkpoints/train_all_summary.json
```

This trains:

```text
1. unet-cloud-segmentation
2. attention-unet
3. swin-unet
4. multi-sensor-fusion
```

## Resume Behavior

The dataset builder skips completed scenes by default. If Colab disconnects,
rerun the build command. It continues from existing scene folders.

Training currently starts each model from scratch. Checkpoints are saved to
Drive so the best outputs are not lost.

## Recommended First Run

Before 2,000 scenes, test:

```bash
python -m app.ai.datasets.build_fusion_100 \
  --config configs/fusion_dataset_2000_colab.json \
  --project YOUR_GOOGLE_CLOUD_PROJECT \
  --target-count 20
```

Then:

```bash
python -m app.ai.training.train_all --profile fast --device auto --epochs 1 \
  --train-manifest /content/drive/MyDrive/clearSKY_AI/data/manifests/train.json \
  --val-manifest /content/drive/MyDrive/clearSKY_AI/data/manifests/val.json \
  --checkpoint-dir /content/drive/MyDrive/clearSKY_AI/models/checkpoints \
  --skip-best-validation
```
