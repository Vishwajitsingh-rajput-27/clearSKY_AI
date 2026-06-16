# Model Training

## Training Package

Training code is scaffolded under:

```text
apps/api/app/ai/
  models/
  datasets/
  training/
  inference/
  preprocessing/
  metrics/
```

Configuration:

```text
apps/api/configs/ai_training.json
```

## Models

### U-Net Cloud Segmentation

Purpose:

- Predict cloud masks.
- Replace threshold-based cloud detection when labeled masks are available.

Inputs:

- LISS-IV cloudy image patches.

Outputs:

- Cloud probability mask.

### Attention U-Net Reconstruction

Purpose:

- Reconstruct cloud-covered pixels using attention-gated skip connections.

Inputs:

- Cloudy RGB/LISS-IV patch.
- Cloud mask.
- Shadow mask.

Outputs:

- Reconstructed cloud-free patch.

### Swin-UNet Reconstruction

Purpose:

- Capture broader context using shifted-window attention.

Inputs:

- Cloudy patch.
- Invalid mask.
- Optional auxiliary feature maps.

Outputs:

- Reconstructed patch.

### Multi-Sensor Fusion

Purpose:

- Fuse LISS-IV, temporal references, Sentinel-1, Sentinel-2, and DEM features.

Inputs:

- LISS-IV cloudy patch.
- Mask channels.
- Optional temporal stack.
- Optional Sentinel-1 VV/VH.
- Optional Sentinel-2 bands.
- Optional DEM/slope/aspect.

Outputs:

- Cloud-free reconstruction.

## Losses

- L1 or Charbonnier reconstruction loss.
- SSIM loss for structural similarity.
- Spectral consistency loss.
- Edge loss for spatial continuity.
- Mask-weighted loss to focus on cloud/shadow regions.

## Metrics

Full-reference:

- PSNR.
- SSIM.
- RMSE.
- MAE.
- Spectral Angle Mapper.
- Spectral consistency score.

No-reference/proxy:

- No-reference quality score.
- Cloud reduction score.
- Runtime.

## Training Command

After installing the full runtime:

```bash
cd apps/api
pip install -r requirements.txt
python -m app.ai.training.train --config configs/ai_training.json
```

## Validation Command

After training or registering a checkpoint:

```bash
cd apps/api
python -m app.ai.training.validate \
  --config configs/ai_training.json \
  --checkpoint models/checkpoints/<model-name>/best.pt
```

If `--checkpoint` is omitted, validation uses `checkpoint_dir/model_name/best.pt` from the config.

## Checkpoints

Place checkpoints under:

```text
MODEL_DIR
```

When a requested model checkpoint is unavailable, public inference falls back to OpenCV and reports fallback metadata. This protects deployment reliability.

## Recommended Research Plan

1. Start with synthetic cloud augmentation for pretraining.
2. Fine-tune U-Net cloud segmentation on labeled masks.
3. Train Attention U-Net on paired cloudy/cloud-free patches.
4. Add Swin-UNet for context-heavy scenes.
5. Add temporal references.
6. Add Sentinel-1 and Sentinel-2 fusion branches.
7. Add DEM features for terrain-aware shadow handling.
8. Benchmark on held-out regions and cloud fractions.
