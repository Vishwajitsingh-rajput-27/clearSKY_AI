from fastapi.testclient import TestClient

from app.main import app


def test_model_registry_endpoints_seed_tracking_data() -> None:
    with TestClient(app) as client:
        summary = client.get("/api/model-registry/summary")
        models = client.get("/api/model-registry/models")
        best = client.get("/api/model-registry/models/best")
        experiments = client.get("/api/model-registry/training-history")
        metrics = client.get("/api/model-registry/metrics-history")
        checkpoints = client.get("/api/model-registry/checkpoints")

    assert summary.status_code == 200
    summary_data = summary.json()["data"]
    assert summary_data["registered_models"] >= 5
    assert summary_data["best_model"]["model_name"] == "opencv-inpaint-telea"

    assert models.status_code == 200
    model_names = {model["model_name"] for model in models.json()["data"]}
    assert "attention-unet-reconstruction" in model_names
    assert "multi-sensor-fusion" in model_names

    assert best.status_code == 200
    assert best.json()["data"]["checkpoint_status"] == "available"

    assert experiments.status_code == 200
    assert len(experiments.json()["data"]) >= 5

    assert metrics.status_code == 200
    assert len(metrics.json()["data"]) >= 1

    assert checkpoints.status_code == 200
    assert len(checkpoints.json()["data"]) >= 5
