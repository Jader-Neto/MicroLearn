"""Sprint 3: recomendações explicáveis para notas abaixo de 7,0.

Lê notas pela API Avaliações e aulas pela API Cursos. A persistência local é
um cache recomputado por acesso e não uma cópia das tabelas de outros serviços.
"""
import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Header, HTTPException
from common.identity import current_actor, service_json
from common.security import bearer_token
from .db import connect, init_db


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app=FastAPI(title='MicroLearn - Recomendações',version='0.3.0',lifespan=lifespan)


@app.get('/health')
def health():
    with connect() as db:
        db.execute('SELECT 1')
    return {'service':'recommendations','status':'ok','implementation':'sprint_3'}


@app.get('/recommendations/mine')
def my_recommendations(authorization: str | None = Header(default=None), actor: dict = Depends(current_actor)):
    if actor['role'] != 'student':
        raise HTTPException(403,detail='Recomendações disponíveis apenas para alunos')
    auth='Bearer '+bearer_token(authorization)
    assessment_base=os.getenv('ASSESSMENTS_URL','http://localhost:8003')
    course_base=os.getenv('COURSES_URL','http://localhost:8002')
    results=service_json(assessment_base,'/assessments/results/mine',auth)
    course_lessons={}
    recommendations=[]
    for result in results:
        if result['score'] >= 7.0:
            continue
        course_id=result['course_id']
        if course_id not in course_lessons:
            try:
                course_lessons[course_id]=service_json(course_base,f'/courses/{course_id}/lessons',auth)
            except HTTPException as exc:
                if exc.status_code in (403,404):
                    # Não recomendar material de curso excluído ou sem matrícula.
                    course_lessons[course_id]=[]
                else:
                    raise
        lesson=next((lesson for lesson in course_lessons[course_id] if lesson['id']==result['lesson_id']),None)
        if not lesson:
            continue
        recommendations.append({
            'id':str(uuid.uuid5(uuid.NAMESPACE_URL,actor['id']+':'+result['attempt_id'])),
            'student_id':actor['id'], 'attempt_id':result['attempt_id'],
            'course_id':course_id,'lesson_id':lesson['id'],
            'lesson_title':lesson['title'], 'quiz_title':result['quiz_title'],
            'score':result['score'], 'reason':'Nota inferior a 7,0. Revise a aula relacionada à avaliação.',
        })
    with connect() as db:
        db.execute('DELETE FROM recommendations WHERE student_id=?',(actor['id'],))
        for rec in recommendations:
            db.execute('''INSERT INTO recommendations
                          (id,student_id,attempt_id,course_id,lesson_id,lesson_title,quiz_title,score)
                          VALUES(?,?,?,?,?,?,?,?)''',tuple(rec[k] for k in ('id','student_id','attempt_id',
                          'course_id','lesson_id','lesson_title','quiz_title','score')))
    return recommendations
