"""Testes de regressão da Sprint 4: administração e isolamento de acesso."""
from fastapi.testclient import TestClient
from services.auth.main import app


def _login(client, email, password):
    res = client.post('/auth/login', json={'email': email, 'password': password})
    assert res.status_code == 200, res.text
    return {'Authorization': f"Bearer {res.json()['access_token']}"}


def test_admin_can_manage_roles_and_reactivate(tmp_path, monkeypatch):
    monkeypatch.setenv('AUTH_DB_PATH', str(tmp_path / 'auth-s4.sqlite3'))
    monkeypatch.setenv('ADMIN_EMAIL', 'admin@microlearn.local')
    monkeypatch.setenv('ADMIN_PASSWORD', 'senha-super-forte-admin-2026')
    with TestClient(app) as client:
        admin = _login(client, 'admin@microlearn.local', 'senha-super-forte-admin-2026')
        new = client.post('/auth/register', json={'name':'Aluna Exemplo','email':'aluna@example.com','password':'uma-senha-forte-123'})
        assert new.status_code == 201
        uid = new.json()['id']
        assert client.patch(f'/auth/users/{uid}', headers=admin, json={'role':'teacher'}).json()['role'] == 'teacher'
        assert client.patch(f'/auth/users/{uid}', headers=admin, json={'active':False}).json()['active'] is False
        assert client.post('/auth/login', json={'email':'aluna@example.com','password':'uma-senha-forte-123'}).status_code == 401
        assert client.patch(f'/auth/users/{uid}', headers=admin, json={'active':True}).json()['active'] is True
        assert _login(client, 'aluna@example.com', 'uma-senha-forte-123')
        assert any(u['id'] == uid and u['role'] == 'teacher' for u in client.get('/auth/users', headers=admin).json())


def test_admin_validation_and_self_protection(tmp_path, monkeypatch):
    monkeypatch.setenv('AUTH_DB_PATH', str(tmp_path / 'auth-s4-validation.sqlite3'))
    monkeypatch.setenv('ADMIN_EMAIL', 'admin@microlearn.local')
    monkeypatch.setenv('ADMIN_PASSWORD', 'senha-super-forte-admin-2026')
    with TestClient(app) as client:
        admin = _login(client, 'admin@microlearn.local', 'senha-super-forte-admin-2026')
        admin_id = client.get('/auth/me', headers=admin).json()['id']
        assert client.patch(f'/auth/users/{admin_id}', headers=admin, json={'active': False}).status_code == 409
        assert client.patch(f'/auth/users/{admin_id}', headers=admin, json={'role': 'student'}).status_code == 409
        assert client.patch(f'/auth/users/{admin_id}', headers=admin, json={'role': None}).status_code == 422
        assert client.patch(f'/auth/users/{admin_id}', headers=admin, json={}).status_code == 422
        assert client.patch('/auth/users/00000000-0000-4000-8000-000000000001', headers=admin, json={'active':False}).status_code == 404


def test_student_cannot_promote_self(tmp_path, monkeypatch):
    monkeypatch.setenv('AUTH_DB_PATH', str(tmp_path / 'auth-s4-student.sqlite3'))
    monkeypatch.delenv('ADMIN_EMAIL', raising=False)
    monkeypatch.delenv('ADMIN_PASSWORD', raising=False)
    with TestClient(app) as client:
        student = client.post('/auth/register', json={'name':'Aluna','email':'aluna@example.com','password':'uma-senha-forte-123'})
        assert student.status_code == 201
        uid = student.json()['id']
        token = _login(client, 'aluna@example.com', 'uma-senha-forte-123')
        assert client.get('/auth/users', headers=token).status_code == 403
        assert client.patch(f'/auth/users/{uid}', headers=token, json={'role': 'manager'}).status_code == 403
