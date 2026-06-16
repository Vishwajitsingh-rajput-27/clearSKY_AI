from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_signup_login_projects_history_and_storage() -> None:
    email = f"user-{uuid4().hex}@example.com"
    password = "StrongPass123"

    with TestClient(app) as client:
        unauthorized = client.get("/api/auth/me")
        assert unauthorized.status_code == 401

        signup = client.post(
            "/api/auth/signup",
            json={"email": email, "password": password, "full_name": "Research User"},
        )
        assert signup.status_code == 201
        signup_data = signup.json()["data"]
        token = signup_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        me = client.get("/api/auth/me", headers=headers)
        assert me.status_code == 200
        assert me.json()["data"]["email"] == email

        duplicate = client.post(
            "/api/auth/signup",
            json={"email": email, "password": password},
        )
        assert duplicate.status_code == 409

        login = client.post("/api/auth/login", json={"email": email, "password": password})
        assert login.status_code == 200
        assert login.json()["data"]["user"]["email"] == email

        project = client.post(
            "/api/projects",
            json={"name": "LISS-IV public test", "description": "Auth integration project"},
            headers=headers,
        )
        assert project.status_code == 201
        project_id = project.json()["data"]["id"]

        upload = client.post(
            "/api/scenes/upload",
            data={"project_id": project_id},
            files={"file": ("auth-scene.tif", b"fake-tiff-content", "image/tiff")},
            headers=headers,
        )
        assert upload.status_code == 201
        assert upload.json()["data"]["project_id"] == project_id

        history = client.get("/api/users/me/history", headers=headers)
        assert history.status_code == 200
        history_data = history.json()["data"]
        assert history_data["items"]
        assert history_data["storage"]["used_storage_bytes"] > 0

        storage = client.get("/api/users/me/storage", headers=headers)
        assert storage.status_code == 200
        assert storage.json()["data"]["remaining_storage_bytes"] > 0


def test_login_rejects_invalid_credentials() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/login",
            json={"email": "missing@example.com", "password": "bad-password"},
        )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"
