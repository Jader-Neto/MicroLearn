import uuid
from fastapi.testclient import TestClient
from common.identity import current_actor
from services.recommendations.main import app


def test_recommendation_below_seven_and_cache(tmp_path,monkeypatch):
    monkeypatch.setenv('DB_PATH',str(tmp_path/'recs.sqlite3'))
    student=str(uuid.uuid4()); cid=str(uuid.uuid4()); lesson=str(uuid.uuid4())
    actor={'id':student,'role':'student'}
    app.dependency_overrides[current_actor]=lambda:actor
    results=[{'attempt_id':str(uuid.uuid4()),'course_id':cid,'lesson_id':lesson,
              'quiz_title':'Revisão','score':5.0},
             {'attempt_id':str(uuid.uuid4()),'course_id':cid,'lesson_id':lesson,
              'quiz_title':'Avançada','score':10.0}]
    def fake(base,path,auth,**kw):
        if path.endswith('results/mine'):
            return results
        return [{'id':lesson,'title':'Aula 1'}]
    monkeypatch.setattr('services.recommendations.main.service_json',fake)
    try:
        with TestClient(app) as client:
            client.headers.update({"Authorization":"Bearer test-jwt-fixture"})
            response=client.get('/recommendations/mine')
            assert response.status_code==200,response.text
            assert len(response.json())==1
            assert response.json()[0]['score']==5.0
            assert response.json()[0]['lesson_title']=='Aula 1'
            from services.recommendations.db import connect
            with connect() as db:
                assert db.execute('SELECT COUNT(*) FROM recommendations').fetchone()[0]==1
            actor['role']='teacher'
            assert client.get('/recommendations/mine').status_code==403
            actor['role']='student'; results.clear()
            assert client.get('/recommendations/mine').json()==[]
            with connect() as db:
                assert db.execute('SELECT COUNT(*) FROM recommendations').fetchone()[0]==0
    finally: app.dependency_overrides.clear()
