import sqlite3


def test_health(auth_client):
    r = auth_client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_register_login_me_and_duplicate(auth_client):
    data = {"name": "Aluno Teste", "email": " ALUNO@EXEMPLO.COM ", "password": "senha-super-segura-123"}
    created = auth_client.post("/auth/register", json=data)
    assert created.status_code == 201, created.text
    assert created.json()["role"] == "student"
    assert "password" not in created.text
    assert created.json()["email"] == "aluno@exemplo.com"
    assert auth_client.post("/auth/register", json=data).status_code == 409
    wrong = auth_client.post("/auth/login", json={"email":data["email"],"password":"errada"})
    assert wrong.status_code == 401
    login = auth_client.post("/auth/login", json={"email":"aluno@exemplo.com", "password":data["password"]})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    profile = auth_client.get("/auth/me", headers={"Authorization":f"Bearer {token}"})
    assert profile.status_code == 200
    assert profile.json()["id"] == created.json()["id"]
    assert auth_client.get("/auth/me").status_code == 401
    assert auth_client.get("/auth/me", headers={"Authorization":"Bearer invalido"}).status_code == 401


def test_public_register_cannot_choose_admin_role(auth_client):
    body = {"name":"Falsa Admin", "email":"adminfake@example.com", "password":"12345678", "role":"manager"}
    user = auth_client.post("/auth/register", json=body)
    assert user.status_code == 201
    assert user.json()["role"] == "student"


def test_password_is_hashed(auth_client, tmp_path):
    auth_client.post("/auth/register", json={"name":"Clara Lima", "email":"clara@example.com", "password":"senha-987654321"})
    with sqlite3.connect(tmp_path / "auth.sqlite3") as db:
        result = db.execute("SELECT password_hash FROM users WHERE email = ?", ("clara@example.com",)).fetchone()[0]
    assert result.startswith("pbkdf2_sha256$")
    assert "senha-987654321" not in result


def test_non_admin_cannot_list_or_change_role(auth_client):
    created = auth_client.post("/auth/register", json={"name":"Lucas", "email":"lucas@example.com", "password":"senhamuito8"}).json()
    token = auth_client.post("/auth/login", json={"email":"lucas@example.com", "password":"senhamuito8"}).json()["access_token"]
    headers = {"Authorization":f"Bearer {token}"}
    assert auth_client.get("/auth/users", headers=headers).status_code == 403
    assert auth_client.patch(f"/auth/users/{created['id']}", json={"role":"manager"}, headers=headers).status_code == 403


def test_bootstrap_admin_permission_and_deactivate(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "with-admin.sqlite3"))
    monkeypatch.setenv("ADMIN_EMAIL", "admin@microlearn.local")
    monkeypatch.setenv("ADMIN_PASSWORD", "senha-de-admin-forte-321")
    from fastapi.testclient import TestClient
    from services.auth.main import app
    with TestClient(app) as client:
        login = client.post("/auth/login", json={"email":"admin@microlearn.local", "password":"senha-de-admin-forte-321"})
        assert login.status_code == 200
        headers = {"Authorization":f"Bearer {login.json()['access_token']}"}
        student = client.post("/auth/register", json={"name":"Maria", "email":"maria@example.com", "password":"123456789"}).json()
        assert client.get("/auth/users", headers=headers).status_code == 200
        result = client.patch(f"/auth/users/{student['id']}", json={"role":"teacher"}, headers=headers)
        assert result.status_code == 200 and result.json()["role"] == "teacher"
        changed = client.patch(f"/auth/users/{student['id']}", json={"active":False}, headers=headers)
        assert changed.status_code == 200 and changed.json()["active"] is False
        assert client.post("/auth/login", json={"email":"maria@example.com", "password":"123456789"}).status_code == 401
        # Um admin não pode remover a própria permissão.
        assert client.patch(f"/auth/users/{client.get('/auth/me',headers=headers).json()['id']}",json={"role":"student"},headers=headers).status_code == 409
