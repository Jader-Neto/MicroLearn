"""Cobertura de regras de negócio da Sprint 2 com DB real e identidades simuladas.

Também existe smoke HTTP real em tests/smoke_processes.py, incluindo Auth e Gateway.
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from services.courses.main import app, get_actor


@pytest.fixture
def course_context(tmp_path, monkeypatch):
    monkeypatch.setenv('DB_PATH',str(tmp_path/'courses.sqlite3'))
    actor={'id':str(uuid.uuid4()),'role':'teacher','name':'Professor A'}
    app.dependency_overrides[get_actor]=lambda:actor.copy()
    try:
        with TestClient(app) as client:
            yield client, actor
    finally:
        app.dependency_overrides.clear()


def make_course(client):
    resp=client.post('/courses',json={'title':'Introdução a Python','description':'Curso inicial de Python','category':'Programação'})
    assert resp.status_code==201,resp.text
    return resp.json()


def test_catalog_only_published_and_owner_crud(course_context):
    client, actor=course_context
    course=make_course(client)
    assert course['status']=='draft' and course['teacher_id']==actor['id']
    assert client.get('/courses').json()==[]
    assert client.get('/courses/owned').json()[0]['id']==course['id']
    changed=client.patch(f"/courses/{course['id']}",json={'title':'Python Aplicado','status':'published'})
    assert changed.status_code==200 and changed.json()['title']=='Python Aplicado'
    assert len(client.get('/courses').json())==1
    assert client.patch(f"/courses/{course['id']}",json={'status':'invalid'}).status_code==422
    assert client.patch(f"/courses/{course['id']}",json={}).status_code==422
    assert client.delete(f"/courses/{course['id']}").status_code==204
    assert client.get('/courses').json()==[]


def test_permissions_student_teacher_and_admin(course_context):
    client, actor=course_context
    course=make_course(client)
    other={'id':str(uuid.uuid4()),'role':'teacher'}
    actor.update(other)
    assert client.patch(f"/courses/{course['id']}",json={'title':'Invasão'}).status_code==403
    assert client.delete(f"/courses/{course['id']}").status_code==403
    assert client.post(f"/courses/{course['id']}/lessons",json={'title':'Nova Aula','body':'Dados'}).status_code==403
    actor.update({'id':str(uuid.uuid4()),'role':'manager'})
    assert client.post('/courses',json={'title':'Outro Curso','description':'Descrição longa','category':'Dev'}).status_code==403
    actor.update({'id':str(uuid.uuid4()),'role':'student'})
    assert client.post('/courses',json={'title':'Curso X','description':'Descrição longa','category':'Dev'}).status_code==403
    assert client.post(f"/courses/{course['id']}/enrollments").status_code==409 # rascunho
    assert client.get(f"/courses/{course['id']}").status_code==404 # oculta rascunho


def test_enrollment_lessons_edit_and_cascade(course_context):
    client, actor=course_context
    owner_id=actor['id']
    c=make_course(client)
    lesson=client.post(f"/courses/{c['id']}/lessons",json={'title':'Primeira aula','body':'Conteúdo de Python','position':2}).json()
    assert lesson['title']=='Primeira aula'
    assert client.patch(f"/courses/{c['id']}/lessons/{lesson['id']}",json={'position':1}).json()['position']==1
    assert client.patch(f"/courses/{c['id']}",json={'status':'published'}).status_code==200
    student_id=str(uuid.uuid4())
    actor.update({'id':student_id,'role':'student'})
    assert client.get(f"/courses/{c['id']}/lessons").status_code==403
    r=client.post(f"/courses/{c['id']}/enrollments")
    assert r.status_code==201 and r.json()['student_id']==student_id
    assert client.post(f"/courses/{c['id']}/enrollments").status_code==409
    assert len(client.get('/courses/enrollments/mine').json())==1
    assert client.get(f"/courses/{c['id']}/lessons").json()[0]['body']=='Conteúdo de Python'
    assert client.post(f"/courses/{c['id']}/lessons",json={'title':'Aula ilegal','body':'X'}).status_code==403
    actor.update({'id':owner_id,'role':'teacher'})
    assert client.delete(f"/courses/{c['id']}/lessons/{lesson['id']}").status_code==204
    assert client.get(f"/courses/{c['id']}/lessons").json()==[]
    assert client.delete(f"/courses/{c['id']}").status_code==204
    actor.update({'id':student_id,'role':'student'})
    assert client.get('/courses/enrollments/mine').json()==[]


def test_validation_and_absent_resource(course_context):
    client,_=course_context
    assert client.post('/courses',json={'title':'x','description':'x','category':'a'}).status_code==422
    c=make_course(client)
    assert client.post(f"/courses/{c['id']}/lessons",json={'title':'Nova aula','body':'texto','material_url':'javascript:alert(1)'}).status_code==422
    assert client.get(f"/courses/{uuid.uuid4()}").status_code==404
    assert client.get('/courses/not-a-uuid').status_code==422
    assert client.delete(f"/courses/{c['id']}/lessons/{uuid.uuid4()}").status_code==404


def test_courses_requires_real_auth_header_when_not_overridden(tmp_path,monkeypatch):
    import httpx
    from common.security import issue_token
    monkeypatch.setenv('DB_PATH',str(tmp_path/'test-auth.sqlite3'))
    app.dependency_overrides.clear()
    with TestClient(app) as client:
        assert client.post('/courses',json={'title':'Python','description':'Descrição','category':'Dev'}).status_code==401
        assert client.get('/courses/owned',headers={'Authorization':'Bearer bogus'}).status_code==401
        def fake_get(url, **kwargs):
            return httpx.Response(401,json={'detail':'disabled'})
        monkeypatch.setattr('services.courses.main.httpx.get',fake_get)
        token=issue_token(str(uuid.uuid4()),'teacher')
        assert client.get('/courses/owned',headers={'Authorization':f'Bearer {token}'}).status_code==401
