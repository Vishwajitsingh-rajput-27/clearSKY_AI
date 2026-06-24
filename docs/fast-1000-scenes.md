# Fast 1000-Scene Dataset

This is the fastest path when Earth Engine or Bhoonidhi access slows you down.

It creates a synthetic fusion-style dataset with:

```text
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

Use it for:

- quick heavy-AI pipeline testing
- pretraining
- demo checkpoints
- proving all model training code works

Do not use it as final scientific validation. For final claims, fine-tune and
validate on real LISS-IV scenes from Bhoonidhi.

## Fast Colab Version

Mount Drive and clone the repo, then run:

```bash
cd /content/clearSKY_AI/apps/api
pip install -r requirements.txt
python -m app.ai.datasets.build_synthetic_fusion \
  --config configs/synthetic_fusion_1000_colab.json
```

Output:

```text
/content/drive/MyDrive/clearSKY_AI/synthetic_data/raw/scene-0001...
/content/drive/MyDrive/clearSKY_AI/synthetic_data/manifests/train.json
/content/drive/MyDrive/clearSKY_AI/synthetic_data/manifests/val.json
/content/drive/MyDrive/clearSKY_AI/synthetic_data/manifests/test.json
```

Then do a one-epoch smoke test:

```bash
python -m app.ai.training.train_all \
  --profile fast \
  --device auto \
  --epochs 1 \
  --train-manifest /content/drive/MyDrive/clearSKY_AI/synthetic_data/manifests/train.json \
  --val-manifest /content/drive/MyDrive/clearSKY_AI/synthetic_data/manifests/val.json \
  --checkpoint-dir /content/drive/MyDrive/clearSKY_AI/synthetic_models/checkpoints \
  --summary-path /content/drive/MyDrive/clearSKY_AI/synthetic_models/checkpoints/train_all_smoke_summary.json \
  --skip-best-validation
```

Then the fastest useful all-model training run:

```bash
python -m app.ai.training.train_all \
  --profile fast \
  --device auto \
  --train-manifest /content/drive/MyDrive/clearSKY_AI/synthetic_data/manifests/train.json \
  --val-manifest /content/drive/MyDrive/clearSKY_AI/synthetic_data/manifests/val.json \
  --checkpoint-dir /content/drive/MyDrive/clearSKY_AI/synthetic_models/checkpoints \
  --summary-path /content/drive/MyDrive/clearSKY_AI/synthetic_models/checkpoints/train_all_fast_summary.json \
  --skip-best-validation
```

After that works, run the stronger version by changing `--profile fast` to
`--profile full`. The full profile is slower because it uses wider models and
more epochs.

## Local Version

```powershell
cd C:\Users\JAISINGH\Documents\clearSKY_AI\apps\api
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m app.ai.datasets.build_synthetic_fusion --config configs/synthetic_fusion_1000.json
```

Then:

```powershell
python -m app.ai.training.train_all --profile fast --device auto --epochs 1
```

## Expected Timing

On Colab:

```text
1000-scene synthetic generation: often 20-90 minutes
1-epoch all-model smoke test: 10-60 minutes
full all-model training: many hours
```

Actual time depends on GPU, Colab disconnects, and Drive write speed.

## Best Strategy

1. Generate 1000 synthetic scenes fast.
2. Run `train_all --profile fast` so all four models produce checkpoints.
3. Save checkpoints.
4. Later collect 50-200 real LISS-IV scenes.
5. Fine-tune on real LISS-IV.
6. Report real validation metrics only from real LISS-IV test scenes.
