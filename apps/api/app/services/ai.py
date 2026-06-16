from app.schemas.health import DependencyStatus


def get_ai_runtime_status() -> DependencyStatus:
    try:
        import torch

        detail = f"torch {torch.__version__}; cuda_available={torch.cuda.is_available()}"
        return DependencyStatus(name="pytorch", ok=True, detail=detail)
    except Exception as exc:  # pragma: no cover - environment-specific diagnostic
        return DependencyStatus(name="pytorch", ok=False, detail=str(exc))

