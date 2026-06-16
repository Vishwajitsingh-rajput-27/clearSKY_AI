from fastapi.testclient import TestClient

from app.main import app


def test_research_summary_and_export_files_are_served() -> None:
    with TestClient(app) as client:
        summary = client.get("/api/research/summary")
        export = client.post(
            "/api/research/export",
            json={
                "report_type": "complete_research_report",
                "formats": ["pdf", "csv", "json", "markdown"],
            },
        )

        assert summary.status_code == 200
        summary_data = summary.json()["data"]
        assert summary_data["registered_models"] >= 5
        assert summary_data["model_comparison"]

        assert export.status_code == 201
        payload = export.json()
        assert payload["success"] is True
        files = payload["data"]["files"]
        assert {item["format"] for item in files} == {"pdf", "csv", "json", "markdown"}

        for item in files:
            download = client.get(item["storage_url"])
            assert download.status_code == 200
            assert download.content

        pdf_file = next(item for item in files if item["format"] == "pdf")
        pdf_download = client.get(pdf_file["storage_url"])
        assert pdf_download.content.startswith(b"%PDF-1.4")

        csv_file = next(item for item in files if item["format"] == "csv")
        csv_download = client.get(csv_file["storage_url"])
        assert b"model_name" in csv_download.content
