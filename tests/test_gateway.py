import httpx
import pytest
from fastapi.testclient import TestClient
from common.security import issue_token
from gateway.main import app


def test_gateway_health():
    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/api/v1/unknown/test").status_code == 404
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/courses/new").status_code == 401


def test_gateway_public_proxy_and_private_jwt(monkeypatch):
    seen = []
    def handler(request):
        seen.append((request.method, request.url.path, request.headers.get("authorization")))
        if request.url.path == "/auth/register":
            return httpx.Response(201, json={"role":"student", "id":"example"})
        return httpx.Response(200, json={"value":"forwarded"})
    transport = httpx.MockTransport(handler)
    original_async_client = httpx.AsyncClient
    monkeypatch.setattr('gateway.main.httpx.AsyncClient', lambda **kwargs: original_async_client(transport=transport))
    with TestClient(app) as client:
        public = client.post('/api/v1/auth/register', json={"name":"Alex"})
        assert public.status_code == 201 and public.json()['role'] == 'student'
        token = issue_token('00000000-0000-4000-8000-000000000000', 'student')
        private = client.get('/api/v1/auth/me', headers={"Authorization": f"Bearer {token}"})
        assert private.status_code == 200
    assert seen[0][1] == '/auth/register'
    assert seen[1][1] == '/auth/me'
    assert seen[1][2] == f'Bearer {token}'


def test_end_to_end_gateway_to_real_auth_service(tmp_path, monkeypatch):
    """Cadastro → login → /me passando pelo proxy real e pelo ASGI do Auth."""
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth-e2e.sqlite3"))
    monkeypatch.delenv("ADMIN_EMAIL", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    from services.auth.main import app as auth_app
    original_async_client = httpx.AsyncClient
    transport = httpx.ASGITransport(app=auth_app)
    monkeypatch.setattr('gateway.main.httpx.AsyncClient', lambda **kwargs: original_async_client(transport=transport, base_url='http://auth-service:8000'))
    with TestClient(auth_app), TestClient(app) as client:
        r = client.post('/api/v1/auth/register', json={"name":"João Silva","email":"joao@exemplo.com","password":"super-senha-12345"})
        assert r.status_code == 201, r.text
        r = client.post('/api/v1/auth/login', json={"email":"joao@exemplo.com","password":"super-senha-12345"})
        assert r.status_code == 200, r.text
        token = r.json()['access_token']
        r = client.get('/api/v1/auth/me', headers={"Authorization":f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()['name'] == 'João Silva'
        assert r.json()['role'] == 'student'
