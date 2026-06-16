from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


def test_health_check() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ok"


def test_rejects_unsupported_upload_type() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/scenes/upload",
            files={"file": ("notes.txt", b"not a geotiff", "text/plain")},
        )

    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "unsupported_upload_type"


def test_uploads_scene_and_serves_file() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/scenes/upload",
            files={"file": ("Cloudy Scene 01.tif", b"fake-tiff-content", "image/tiff")},
        )

        assert response.status_code == 201
        payload = response.json()
        assert payload["success"] is True
        assert payload["data"]["original_filename"] == "Cloudy Scene 01.tif"
        assert payload["data"]["safe_filename"].endswith(".tif")
        assert payload["data"]["storage_url"].startswith("/api/files/")

        download = client.get(payload["data"]["storage_url"])
        assert download.status_code == 200
        assert download.content == b"fake-tiff-content"


def test_baseline_inference_pipeline(tmp_path) -> None:
    image_path = tmp_path / "cloudy.png"
    image = Image.new("RGB", (80, 60), color=(45, 90, 80))

    for x in range(20, 45):
        for y in range(10, 35):
            image.putpixel((x, y), (245, 245, 240))

    for x in range(48, 62):
        for y in range(35, 48):
            image.putpixel((x, y), (25, 30, 28))

    image.save(image_path)

    with TestClient(app) as client:
        with image_path.open("rb") as handle:
            response = client.post(
                "/api/inference/run",
                data={"requested_model": "swin-unet"},
                files={"file": ("cloudy.png", handle, "image/png")},
            )

        assert response.status_code == 201
        payload = response.json()
        data = payload["data"]

        assert payload["success"] is True
        assert data["requested_model"] == "swin-unet"
        assert data["used_model"] == "opencv-inpaint-telea"
        assert data["fallback_used"] is True
        assert data["cloud_coverage_percent"] > 0
        assert data["shadow_coverage_percent"] > 0
        assert 0 <= data["quality_score"] <= 100
        assert 0 <= data["reconstruction_confidence_score"] <= 100
        assert data["processing_time_seconds"] >= 0
        assert data["attention_map_url"].startswith("/api/files/")
        assert data["confidence_map_url"].startswith("/api/files/")
        assert data["recommendations"]
        assert data["metadata"]["file_type"] == "png"
        assert data["metadata"]["width"] == 80
        assert data["metadata"]["height"] == 60
        assert data["metadata"]["band_count"] == 3
        assert data["metadata"]["is_geospatial"] is False
        assert data["qgis_manifest_url"].startswith("/api/files/")

        for key in [
            "original_image_url",
            "cloud_mask_url",
            "shadow_mask_url",
            "reconstructed_image_url",
            "difference_map_url",
            "attention_map_url",
            "confidence_map_url",
            "qgis_manifest_url",
        ]:
            download = client.get(data[key])
            assert download.status_code == 200
            if key == "qgis_manifest_url":
                assert download.headers["content-type"].startswith("application/json")
            else:
                assert download.headers["content-type"].startswith("image/png")
