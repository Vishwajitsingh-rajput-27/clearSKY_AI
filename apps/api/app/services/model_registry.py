from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.model_registry import (
    ExperimentMetric,
    ExperimentRun,
    ModelCheckpoint,
    ModelRegistry,
)
from app.schemas.model_registry import (
    ExperimentMetricResponse,
    ExperimentRunResponse,
    ModelCheckpointResponse,
    ModelRegistryResponse,
    ModelRegistrySummaryResponse,
)

SEED_DATE = datetime(2026, 6, 15, tzinfo=UTC)


def ensure_model_registry_seeded(db: Session) -> None:
    model_count = db.scalar(select(func.count()).select_from(ModelRegistry)) or 0

    if model_count > 0:
        return

    models = [
        ModelRegistry(
            name="opencv-inpaint-telea",
            version="0.1.0",
            architecture="Traditional masking + OpenCV Telea inpainting",
            runtime_type="opencv",
            input_modalities={"modalities": ["LISS-IV RGB preview"], "requires_gpu": False},
            dataset_version="synthetic-liss-iv-cloud-demo-v1",
            training_date=None,
            metrics={
                "no_reference_quality_score": 72.4,
                "cloud_reduction_score": 88.1,
                "spectral_consistency_score": 76.8,
                "ssim_proxy": 0.74,
                "metric_mode": "no_reference_proxy",
                "trained_weights_required": False,
            },
            checkpoint_path="not_required/opencv-inpaint-telea",
            checkpoint_status="available",
            stage="operational-baseline",
            is_active=True,
            is_best=True,
        ),
        ModelRegistry(
            name="unet-cloud-segmentation",
            version="0.1.0",
            architecture="U-Net cloud segmentation",
            runtime_type="pytorch",
            input_modalities={"modalities": ["LISS-IV cloudy image"], "requires_gpu": False},
            dataset_version="liss4-curated-training-v0",
            training_date=None,
            metrics={"training_ready": True, "validated_weights_available": False},
            checkpoint_path="models/checkpoints/unet-cloud-segmentation/best.pt",
            checkpoint_status="missing",
            stage="training-ready",
            is_active=True,
            is_best=False,
        ),
        ModelRegistry(
            name="attention-unet-reconstruction",
            version="0.1.0",
            architecture="Attention U-Net reconstruction",
            runtime_type="pytorch",
            input_modalities={
                "modalities": ["LISS-IV cloudy image", "cloud mask", "shadow mask"],
                "requires_gpu": False,
            },
            dataset_version="liss4-curated-training-v0",
            training_date=None,
            metrics={"training_ready": True, "validated_weights_available": False},
            checkpoint_path="models/checkpoints/attention-unet-reconstruction/best.pt",
            checkpoint_status="missing",
            stage="training-ready",
            is_active=True,
            is_best=False,
        ),
        ModelRegistry(
            name="swin-unet-reconstruction",
            version="0.1.0",
            architecture="Swin-UNet reconstruction",
            runtime_type="pytorch",
            input_modalities={
                "modalities": ["LISS-IV cloudy image", "cloud mask", "temporal reference"],
                "requires_gpu": False,
            },
            dataset_version="liss4-curated-training-v0",
            training_date=None,
            metrics={"training_ready": True, "validated_weights_available": False},
            checkpoint_path="models/checkpoints/swin-unet-reconstruction/best.pt",
            checkpoint_status="missing",
            stage="training-ready",
            is_active=True,
            is_best=False,
        ),
        ModelRegistry(
            name="multi-sensor-fusion",
            version="0.1.0",
            architecture="Multi-sensor LISS-IV + Sentinel-1 + Sentinel-2 + DEM fusion network",
            runtime_type="pytorch",
            input_modalities={
                "modalities": [
                    "LISS-IV",
                    "Sentinel-1 SAR",
                    "Sentinel-2 optical",
                    "DEM",
                    "temporal references",
                ],
                "requires_gpu": False,
            },
            dataset_version="liss4-s1-s2-dem-fusion-v0",
            training_date=None,
            metrics={"training_ready": True, "validated_weights_available": False},
            checkpoint_path="models/checkpoints/multi-sensor-fusion/best.pt",
            checkpoint_status="missing",
            stage="research-candidate",
            is_active=True,
            is_best=False,
        ),
    ]

    db.add_all(models)
    db.flush()

    by_name = {model.name: model for model in models}
    experiments = [
        ExperimentRun(
            model_id=by_name["opencv-inpaint-telea"].id,
            experiment_name="baseline-public-cpu-smoke",
            model_name="opencv-inpaint-telea",
            version="0.1.0",
            status="completed",
            training_date=SEED_DATE,
            dataset_version="synthetic-liss-iv-cloud-demo-v1",
            metrics={
                "no_reference_quality_score": 72.4,
                "cloud_reduction_score": 88.1,
                "spectral_consistency_score": 76.8,
                "processing_time_seconds": 1.8,
            },
            hyperparameters={"inpaint_radius": 5, "mask_method": "brightness_saturation_threshold"},
            checkpoint_path="not_required/opencv-inpaint-telea",
            checkpoint_score=72.4,
            is_best=True,
            notes="Deterministic CPU fallback baseline; no trained weights are required.",
            started_at=SEED_DATE,
            completed_at=SEED_DATE,
        ),
        ExperimentRun(
            model_id=by_name["unet-cloud-segmentation"].id,
            experiment_name="cloud-mask-supervised-training-plan",
            model_name="unet-cloud-segmentation",
            version="0.1.0",
            status="planned",
            training_date=None,
            dataset_version="liss4-curated-training-v0",
            metrics={},
            hyperparameters={"patch_size": 256, "batch_size": 8, "optimizer": "AdamW"},
            checkpoint_path="models/checkpoints/unet-cloud-segmentation/best.pt",
            checkpoint_score=None,
            is_best=False,
            notes=(
                "Training scaffold is available; checkpoint will be registered after "
                "validated weights exist."
            ),
        ),
        ExperimentRun(
            model_id=by_name["attention-unet-reconstruction"].id,
            experiment_name="attention-unet-reconstruction-training-plan",
            model_name="attention-unet-reconstruction",
            version="0.1.0",
            status="planned",
            training_date=None,
            dataset_version="liss4-curated-training-v0",
            metrics={},
            hyperparameters={
                "patch_size": 256,
                "losses": ["L1", "SSIM", "edge", "spectral_consistency"],
            },
            checkpoint_path="models/checkpoints/attention-unet-reconstruction/best.pt",
            checkpoint_score=None,
            is_best=False,
            notes=(
                "Designed for supervised cloud-free reconstruction once paired targets "
                "are curated."
            ),
        ),
        ExperimentRun(
            model_id=by_name["swin-unet-reconstruction"].id,
            experiment_name="swin-unet-temporal-ablation-plan",
            model_name="swin-unet-reconstruction",
            version="0.1.0",
            status="planned",
            training_date=None,
            dataset_version="liss4-curated-training-v0",
            metrics={},
            hyperparameters={"patch_size": 256, "window_size": 8, "temporal_refs": 2},
            checkpoint_path="models/checkpoints/swin-unet-reconstruction/best.pt",
            checkpoint_score=None,
            is_best=False,
            notes=(
                "Prepared for temporal reference ablations and transformer reconstruction "
                "benchmarks."
            ),
        ),
        ExperimentRun(
            model_id=by_name["multi-sensor-fusion"].id,
            experiment_name="multi-sensor-fusion-training-plan",
            model_name="multi-sensor-fusion",
            version="0.1.0",
            status="planned",
            training_date=None,
            dataset_version="liss4-s1-s2-dem-fusion-v0",
            metrics={},
            hyperparameters={
                "patch_size": 256,
                "modalities": ["liss4", "sentinel1", "sentinel2", "dem"],
            },
            checkpoint_path="models/checkpoints/multi-sensor-fusion/best.pt",
            checkpoint_score=None,
            is_best=False,
            notes=(
                "Fusion inputs and loaders are scaffolded; validated multi-sensor "
                "weights are not bundled."
            ),
        ),
    ]

    db.add_all(experiments)
    db.flush()

    experiment_by_model = {experiment.model_name: experiment for experiment in experiments}
    checkpoints = [
        ModelCheckpoint(
            model_id=by_name["opencv-inpaint-telea"].id,
            experiment_id=experiment_by_model["opencv-inpaint-telea"].id,
            model_name="opencv-inpaint-telea",
            version="0.1.0",
            checkpoint_path="not_required/opencv-inpaint-telea",
            storage_uri=None,
            status="available",
            epoch=None,
            metric_name="no_reference_quality_score",
            metric_value=72.4,
            metrics={"no_reference_quality_score": 72.4, "checkpoint_required": False},
            file_size_bytes=None,
            is_best=True,
        ),
        *[
            ModelCheckpoint(
                model_id=by_name[name].id,
                experiment_id=experiment_by_model[name].id,
                model_name=name,
                version="0.1.0",
                checkpoint_path=by_name[name].checkpoint_path or "",
                storage_uri=None,
                status="missing",
                epoch=None,
                metric_name=None,
                metric_value=None,
                metrics={"checkpoint_required": True, "validated_weights_available": False},
                file_size_bytes=None,
                is_best=False,
            )
            for name in [
                "unet-cloud-segmentation",
                "attention-unet-reconstruction",
                "swin-unet-reconstruction",
                "multi-sensor-fusion",
            ]
        ],
    ]
    db.add_all(checkpoints)

    db.add_all(
        [
            ExperimentMetric(
                experiment_id=experiment_by_model["opencv-inpaint-telea"].id,
                model_name="opencv-inpaint-telea",
                version="0.1.0",
                split="demo",
                epoch=None,
                step=1,
                loss=None,
                metrics={
                    "no_reference_quality_score": 72.4,
                    "cloud_reduction_score": 88.1,
                    "spectral_consistency_score": 76.8,
                },
                recorded_at=SEED_DATE,
            ),
            ExperimentMetric(
                experiment_id=experiment_by_model["unet-cloud-segmentation"].id,
                model_name="unet-cloud-segmentation",
                version="0.1.0",
                split="config",
                epoch=0,
                step=0,
                loss=None,
                metrics={"training_ready": True, "validated_weights_available": False},
                recorded_at=SEED_DATE,
            ),
        ]
    )

    db.commit()


def model_to_response(row: ModelRegistry) -> ModelRegistryResponse:
    return ModelRegistryResponse(
        id=row.id,
        model_name=row.name,
        version=row.version,
        architecture=row.architecture,
        runtime_type=row.runtime_type,
        input_modalities=row.input_modalities,
        dataset_version=row.dataset_version,
        training_date=row.training_date,
        metrics=row.metrics or {},
        checkpoint_path=row.checkpoint_path,
        checkpoint_status=row.checkpoint_status or "missing",
        stage=row.stage or "research",
        is_active=row.is_active,
        is_best=row.is_best,
        created_at=row.created_at,
    )


def experiment_to_response(row: ExperimentRun) -> ExperimentRunResponse:
    return ExperimentRunResponse(
        id=row.id,
        model_id=row.model_id,
        experiment_name=row.experiment_name,
        model_name=row.model_name,
        version=row.version,
        status=row.status,
        training_date=row.training_date,
        dataset_version=row.dataset_version,
        metrics=row.metrics or {},
        hyperparameters=row.hyperparameters or {},
        checkpoint_path=row.checkpoint_path,
        checkpoint_score=row.checkpoint_score,
        is_best=row.is_best,
        notes=row.notes,
        started_at=row.started_at,
        completed_at=row.completed_at,
        created_at=row.created_at,
    )


def checkpoint_to_response(row: ModelCheckpoint) -> ModelCheckpointResponse:
    return ModelCheckpointResponse(
        id=row.id,
        model_id=row.model_id,
        experiment_id=row.experiment_id,
        model_name=row.model_name,
        version=row.version,
        checkpoint_path=row.checkpoint_path,
        storage_uri=row.storage_uri,
        status=row.status,
        epoch=row.epoch,
        metric_name=row.metric_name,
        metric_value=row.metric_value,
        metrics=row.metrics or {},
        file_size_bytes=row.file_size_bytes,
        is_best=row.is_best,
        created_at=row.created_at,
    )


def metric_to_response(row: ExperimentMetric) -> ExperimentMetricResponse:
    return ExperimentMetricResponse(
        id=row.id,
        experiment_id=row.experiment_id,
        model_name=row.model_name,
        version=row.version,
        split=row.split,
        epoch=row.epoch,
        step=row.step,
        loss=row.loss,
        metrics=row.metrics or {},
        recorded_at=row.recorded_at,
        created_at=row.created_at,
    )


def select_best_model(models: list[ModelRegistry]) -> ModelRegistry | None:
    best_flagged = [model for model in models if model.is_best and model.is_active]
    if best_flagged:
        return sorted(best_flagged, key=_model_quality_score, reverse=True)[0]

    active_available = [
        model for model in models if model.is_active and model.checkpoint_status == "available"
    ]
    if active_available:
        return sorted(active_available, key=_model_quality_score, reverse=True)[0]

    return sorted(models, key=_model_quality_score, reverse=True)[0] if models else None


def build_summary(db: Session) -> ModelRegistrySummaryResponse:
    models = list(db.scalars(select(ModelRegistry)).all())
    experiments = list(db.scalars(select(ExperimentRun)).all())
    checkpoint_count = db.scalar(select(func.count()).select_from(ModelCheckpoint)) or 0
    best_model = select_best_model(models)

    training_dates = [
        experiment.training_date
        for experiment in experiments
        if experiment.training_date is not None
    ]

    return ModelRegistrySummaryResponse(
        registered_models=len(models),
        active_models=sum(1 for model in models if model.is_active),
        experiment_count=len(experiments),
        checkpoint_count=checkpoint_count,
        best_model=model_to_response(best_model) if best_model else None,
        latest_training_date=max(training_dates) if training_dates else None,
        best_quality_score=_model_quality_score(best_model) if best_model else None,
    )


def _model_quality_score(model: ModelRegistry | None) -> float:
    if model is None:
        return 0.0

    metrics: dict[str, Any] = model.metrics or {}
    for key in (
        "no_reference_quality_score",
        "quality_score",
        "spectral_consistency_score",
        "ssim_proxy",
    ):
        value = metrics.get(key)
        if isinstance(value, int | float):
            return float(value if key != "ssim_proxy" else value * 100)

    return 0.0
