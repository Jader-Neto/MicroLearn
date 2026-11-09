import os
import pytest

os.environ.setdefault("JWT_SECRET", "test-secret-only-not-for-production-012345678901234567890")


@pytest.fixture
def auth_client(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth.sqlite3"))
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    from fastapi.testclient import TestClient
    from services.auth.main import app
    with TestClient(app) as client:
        yield client
