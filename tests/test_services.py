from fastapi.testclient import TestClient
from services.courses.main import app as courses_app
from services.assessments.main import app as assessments_app
from services.recommendations.main import app as recommendations_app


def test_courses_service_initialized(tmp_path, monkeypatch):
    monkeypatch.setenv('DB_PATH', str(tmp_path / 'courses.sqlite3'))
    with TestClient(courses_app) as client:
        assert client.get('/health').json()['implementation'] == 'sprint_2'
        assert client.get('/courses').json() == []
    assert (tmp_path / 'courses.sqlite3').exists()


def test_sprint3_services_initialized(tmp_path, monkeypatch):
    for name, app in [('assessments', assessments_app), ('recommendations', recommendations_app)]:
        monkeypatch.setenv('DB_PATH', str(tmp_path / (name + '.sqlite3')))
        with TestClient(app) as client:
            assert client.get('/health').json()['implementation'] == 'sprint_3'
        assert (tmp_path / (name + '.sqlite3')).exists()
