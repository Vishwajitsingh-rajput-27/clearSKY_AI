# Train All AI Models

This guide trains every clearSKY AI model from the generated fusion dataset.

Required dataset files:

```text
apps/api/data/manifests/train.json
apps/api/data/manifests/val.json
```

Build them first with:

```powershell
cd C:\Users\JAISINGH\Documents\clearSKY_AI\apps\api
python -m app.ai.datasets.build_fusion_100 --project YOUR_GOOGLE_CLOUD_PROJECT
```

## One Command

Train all models:

```powershell
python -m app.ai.training.train_all --device auto
```

This trains, in order:

```text
1. unet-cloud-segmentation
2. attention-unet
3. swin-unet
4. multi-sensor-fusion
```

It writes checkpoints to:

```text
apps/api/models/checkpoints/<model-name>/latest.pt
apps/api/models/checkpoints/<model-name>/best.pt
```

It writes a summary to:

```text
apps/api/models/checkpoints/train_all_summary.json
```

## Quick Test

Before a real long run, test one epoch on all models:

```powershell
python -m app.ai.training.train_all --device auto --epochs 1
```

Train only selected models:

```powershell
python -m app.ai.training.train_all --models attention-unet,swin-unet --device auto
```

Keep going if one model fails:

```powershell
python -m app.ai.training.train_all --device auto --continue-on-error
```

Use Google Drive manifests/checkpoints, as in Colab:

```powershell
python -m app.ai.training.train_all `
  --device auto `
  --train-manifest /content/drive/MyDrive/clearSKY_AI/data/manifests/train.json `
  --val-manifest /content/drive/MyDrive/clearSKY_AI/data/manifests/val.json `
  --checkpoint-dir /content/drive/MyDrive/clearSKY_AI/models/checkpoints
```

## Individual Commands

```powershell
python -m app.ai.training.train --config configs/ai_training.unet_cloud.json
python -m app.ai.training.train --config configs/ai_training.attention_unet.json
python -m app.ai.training.train --config configs/ai_training.swin_unet.json
python -m app.ai.training.train --config configs/ai_training.fusion.json
```

## Configs

```text
apps/api/configs/ai_training.unet_cloud.json
apps/api/configs/ai_training.attention_unet.json
apps/api/configs/ai_training.swin_unet.json
apps/api/configs/ai_training.fusion.json
```

## Notes

- U-Net cloud segmentation uses BCE + Dice loss.
- Attention U-Net, Swin-UNet, and fusion use reconstruction loss.
- Use `--device auto` on a GPU machine to select CUDA automatically.
- Generated checkpoints are ignored by Git and should be uploaded to model storage
  after validation.
