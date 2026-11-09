"""Validação do domínio de avaliações: gabarito, nota, tentativas e acesso."""
import uuid
import pytest
from fastapi.testclient import TestClient
from common.identity import current_actor
from services.assessments.main import app


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    monkeypatch.setenv('DB_PATH',str(tmp_path/'assessments.sqlite3'))
    actor={'id':str(uuid.uuid4()),'role':'teacher'}
    course_id=str(uuid.uuid4()); lesson_id=str(uuid.uuid4())
    app.dependency_overrides[current_actor]=lambda:actor
    def fake_service(base, path, authorization, **kwargs):
        if path.endswith('/lessons'):
            return [{'id':lesson_id,'title':'Revisão Python'}]
        return {'id':course_id,'teacher_id':teacher_id}
    teacher_id=actor['id']
    monkeypatch.setattr('services.assessments.main.service_json',fake_service)
    with TestClient(app) as client:
        client.headers.update({"Authorization":"Bearer test-jwt-fixture"})
        yield client,actor,course_id,lesson_id
    app.dependency_overrides.clear()


def payload(lesson_id):
    return {'title':'Avaliação Python','lesson_id':lesson_id,
            'questions':[{'statement':'Quanto é 2+2?', 'options':['3','4','5'], 'correct_index':1},
                         {'statement':'Quanto é 3+3?', 'options':['5','6','7'], 'correct_index':1}]}


def test_teacher_can_create_and_student_cannot_see_answers(ctx):
    client, actor, cid, lid = ctx
    r=client.post(f'/assessments/courses/{cid}/quizzes',json=payload(lid))
    assert r.status_code==201,r.text
    quiz=r.json(); qid=quiz['id']
    assert len(client.get(f'/assessments/courses/{cid}/quizzes').json()) == 1
    actor.update({'id':str(uuid.uuid4()),'role':'student'})
    r=client.get(f'/assessments/quizzes/{qid}')
    assert r.status_code==200
    assert 'correct_index' not in r.text and 'answers_json' not in r.text
    assert r.json()['already_submitted'] is False
    assert client.post(f'/assessments/courses/{cid}/quizzes',json=payload(lid)).status_code==403


def test_grade_one_attempt_private_results(ctx):
    client,actor,cid,lid=ctx
    qid=client.post(f'/assessments/courses/{cid}/quizzes',json=payload(lid)).json()['id']
    actor.update({'id':str(uuid.uuid4()),'role':'student'})
    r=client.post(f'/assessments/quizzes/{qid}/submit',json={'answers':[1,0]})
    assert r.status_code==201,r.text
    assert r.json()['score']==5 and r.json()['recommend_review'] is True
    assert client.post(f'/assessments/quizzes/{qid}/submit',json={'answers':[1,1]}).status_code==409
    assert client.post(f'/assessments/quizzes/{qid}/submit',json={'answers':[1,9]}).status_code==422
    result=client.get('/assessments/results/mine').json()
    assert len(result)==1 and result[0]['score']==5 and result[0]['student_id']==actor['id']
    actor['id']=str(uuid.uuid4())
    assert client.get('/assessments/results/mine').json()==[]


def test_validation_authorization_and_delete(ctx):
    client,actor,cid,lid=ctx
    body=payload(lid)
    body['questions'][0]['correct_index']=3
    assert client.post(f'/assessments/courses/{cid}/quizzes',json=body).status_code==422
    body=payload(str(uuid.uuid4()))
    assert client.post(f'/assessments/courses/{cid}/quizzes',json=body).status_code==422
    qid=client.post(f'/assessments/courses/{cid}/quizzes',json=payload(lid)).json()['id']
    assert client.delete(f'/assessments/quizzes/{qid}').status_code==204
    assert client.get(f'/assessments/quizzes/{qid}').status_code==404


def test_teacher_results_and_cannot_delete_after_response(ctx):
    client,actor,cid,lid=ctx
    teacher_id=actor['id']
    qid=client.post(f'/assessments/courses/{cid}/quizzes',json=payload(lid)).json()['id']
    actor.update({'id':str(uuid.uuid4()),'role':'student'})
    assert client.get(f'/assessments/courses/{cid}/results').status_code==403
    r=client.post(f'/assessments/quizzes/{qid}/submit',json={'answers':[1,1]})
    assert r.json()['score']==10 and not r.json()['recommend_review']
    actor.update({'id':teacher_id,'role':'teacher'})
    grades=client.get(f'/assessments/courses/{cid}/results')
    assert grades.status_code==200 and grades.json()[0]['score']==10
    assert client.delete(f'/assessments/quizzes/{qid}').status_code==409
