"""Sprint 3: questionários objetivos, uma tentativa por aluno, notas de 0 a 10.

Dados de cursos e matrículas são consultados pela API HTTP do serviço Cursos;
usuários são consultados pela API do Auth. Gabarito nunca é devolvido ao aluno.
"""
import json
import os
import sqlite3
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Header, HTTPException
from pydantic import BaseModel, Field, model_validator
from common.identity import current_actor, service_json
from common.security import bearer_token
from .db import connect, init_db


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(title='MicroLearn - Avaliações', version='0.3.0', lifespan=lifespan)


def courses_url():
    return os.getenv('COURSES_URL', 'http://localhost:8002')


def get_course_and_lessons(course_id, authorization):
    """Valida matrícula ou autoria; Cursos é autoridade sobre vínculo e aulas."""
    base = courses_url()
    course = service_json(base, f'/courses/{course_id}', authorization)
    lessons = service_json(base, f'/courses/{course_id}/lessons', authorization)
    return course, lessons


def require_teacher(course, actor):
    if actor['role'] != 'teacher' or course['teacher_id'] != actor['id']:
        raise HTTPException(403, detail='Apenas o professor responsável pode modificar avaliações')


def quiz_row(db, quiz_id):
    row = db.execute('SELECT * FROM quizzes WHERE id=?', (str(quiz_id),)).fetchone()
    if not row:
        raise HTTPException(404, detail='Questionário não encontrado')
    return dict(row)


def questions_for(db, quiz_id, include_answer=False):
    rows = db.execute('SELECT * FROM questions WHERE quiz_id=? ORDER BY position', (str(quiz_id),)).fetchall()
    result = []
    for r in rows:
        q = {'id': r['id'], 'position': r['position'], 'statement': r['statement'], 'options': json.loads(r['options_json'])}
        if include_answer:
            q['correct_index'] = r['correct_index']
        result.append(q)
    return result


class QuestionIn(BaseModel):
    statement: str = Field(min_length=5, max_length=1000)
    options: list[str] = Field(min_length=2, max_length=5)
    correct_index: int = Field(ge=0, le=4)

    @model_validator(mode='after')
    def check_options(self):
        if any(not v.strip() or len(v) > 300 for v in self.options):
            raise ValueError('Alternativas devem conter de 1 a 300 caracteres')
        if self.correct_index >= len(self.options):
            raise ValueError('Índice da resposta correta fora do intervalo')
        return self


class QuizIn(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    lesson_id: uuid.UUID
    questions: list[QuestionIn] = Field(min_length=1, max_length=20)


class SubmitIn(BaseModel):
    answers: list[int] = Field(min_length=1, max_length=20)


@app.get('/health')
def health():
    with connect() as db:
        db.execute('SELECT 1')
    return {'service':'assessments', 'status':'ok', 'implementation':'sprint_3'}


@app.post('/assessments/courses/{course_id}/quizzes', status_code=201)
def create_quiz(course_id: uuid.UUID, body: QuizIn, authorization: str | None = Header(default=None), actor: dict = Depends(current_actor)):
    auth = 'Bearer ' + bearer_token(authorization)
    course, lessons = get_course_and_lessons(course_id, auth)
    require_teacher(course, actor)
    if str(body.lesson_id) not in {lesson['id'] for lesson in lessons}:
        raise HTTPException(422, detail='A aula de revisão deve pertencer a este curso')
    quiz_id = str(uuid.uuid4())
    with connect() as db:
        db.execute('INSERT INTO quizzes(id,course_id,teacher_id,lesson_id,title) VALUES(?,?,?,?,?)',
                   (quiz_id,str(course_id),actor['id'],str(body.lesson_id),body.title.strip()))
        for index, q in enumerate(body.questions, start=1):
            db.execute('''INSERT INTO questions(id,quiz_id,position,statement,options_json,correct_index)
                          VALUES(?,?,?,?,?,?)''', (str(uuid.uuid4()),quiz_id,index,q.statement.strip(),
                          json.dumps([o.strip() for o in q.options],ensure_ascii=False),q.correct_index))
    return {'id':quiz_id,'course_id':str(course_id),'lesson_id':str(body.lesson_id),
            'title':body.title.strip(),'question_count':len(body.questions)}


@app.get('/assessments/courses/{course_id}/quizzes')
def list_quizzes(course_id: uuid.UUID, authorization: str | None = Header(default=None), actor: dict = Depends(current_actor)):
    if actor['role'] not in ('student', 'teacher'):
        raise HTTPException(403, detail='Perfil sem acesso às avaliações')
    get_course_and_lessons(course_id, 'Bearer '+bearer_token(authorization))
    with connect() as db:
        rows = db.execute('''SELECT q.*, (SELECT COUNT(*) FROM questions WHERE quiz_id=q.id) AS question_count
                             FROM quizzes q WHERE course_id=? ORDER BY q.created_at,q.id''',(str(course_id),)).fetchall()
    return [dict(r) for r in rows]


@app.get('/assessments/results/mine')
def results_mine(actor: dict = Depends(current_actor)):
    if actor['role'] != 'student':
        raise HTTPException(403, detail='Recurso disponível apenas a alunos')
    with connect() as db:
        rows = db.execute('''SELECT a.id AS attempt_id,a.quiz_id,a.student_id,a.score,a.correct_count,a.total,
                                  a.created_at,q.course_id,q.lesson_id,q.title AS quiz_title
                             FROM attempts a JOIN quizzes q ON q.id=a.quiz_id
                             WHERE a.student_id=? ORDER BY a.created_at DESC, a.id DESC''',(actor['id'],)).fetchall()
    return [dict(r) for r in rows]


@app.get('/assessments/courses/{course_id}/results')
def results_for_teacher(course_id: uuid.UUID, authorization: str | None = Header(default=None), actor: dict = Depends(current_actor)):
    course, _ = get_course_and_lessons(course_id, 'Bearer '+bearer_token(authorization))
    require_teacher(course, actor)
    with connect() as db:
        rows=db.execute('''SELECT a.id AS attempt_id,a.student_id,a.score,a.correct_count,a.total,
                                 a.created_at,q.title AS quiz_title,q.id AS quiz_id
                           FROM attempts a JOIN quizzes q ON q.id=a.quiz_id
                           WHERE q.course_id=? ORDER BY a.created_at DESC''',(str(course_id),)).fetchall()
    return [dict(r) for r in rows]


@app.get('/assessments/quizzes/{quiz_id}')
def quiz_detail(quiz_id: uuid.UUID, authorization: str | None = Header(default=None), actor: dict = Depends(current_actor)):
    with connect() as db:
        quiz = quiz_row(db, quiz_id)
    course, _ = get_course_and_lessons(quiz['course_id'], 'Bearer '+bearer_token(authorization))
    if actor['role'] not in ('student', 'teacher'):
        raise HTTPException(403, detail='Perfil sem acesso')
    with connect() as db:
        data = {**quiz, 'questions':questions_for(db, quiz_id)}  # Sem gabarito, inclusive ao listar
        if actor['role']=='student':
            attempt = db.execute('SELECT score,created_at FROM attempts WHERE quiz_id=? AND student_id=?',
                                 (str(quiz_id),actor['id'])).fetchone()
            data['already_submitted'] = bool(attempt)
            data['my_score'] = attempt['score'] if attempt else None
    return data


@app.post('/assessments/quizzes/{quiz_id}/submit', status_code=201)
def submit(quiz_id: uuid.UUID, body: SubmitIn, authorization: str | None = Header(default=None), actor: dict = Depends(current_actor)):
    if actor['role'] != 'student':
        raise HTTPException(403, detail='Somente alunos podem responder avaliações')
    with connect() as db:
        quiz = quiz_row(db, quiz_id)
        rows = db.execute('SELECT * FROM questions WHERE quiz_id=? ORDER BY position',(str(quiz_id),)).fetchall()
    # Revalida matrícula e publicação a cada submissão.
    get_course_and_lessons(quiz['course_id'], 'Bearer '+bearer_token(authorization))
    if len(body.answers) != len(rows):
        raise HTTPException(422, detail='Responda a todas as questões exatamente uma vez')
    for index, (answer, question) in enumerate(zip(body.answers, rows), start=1):
        if answer < 0 or answer >= len(json.loads(question['options_json'])):
            raise HTTPException(422, detail=f'Alternativa inválida na questão {index}')
    correct = sum(int(ans == q['correct_index']) for ans,q in zip(body.answers,rows))
    score = round(10 * correct / len(rows), 2)
    attempt_id = str(uuid.uuid4())
    try:
        with connect() as db:
            db.execute('''INSERT INTO attempts(id,quiz_id,student_id,answers_json,correct_count,total,score)
                          VALUES(?,?,?,?,?,?,?)''', (attempt_id,str(quiz_id),actor['id'],
                          json.dumps(body.answers),correct,len(rows),score))
    except sqlite3.IntegrityError as exc:
        raise HTTPException(409, detail='Você já respondeu este questionário') from exc
    return {'attempt_id':attempt_id,'quiz_id':str(quiz_id),'score':score,'correct_count':correct,
            'total':len(rows),'recommend_review':score<7.0}


@app.delete('/assessments/quizzes/{quiz_id}',status_code=204)
def delete_quiz(quiz_id: uuid.UUID, authorization: str | None = Header(default=None), actor: dict = Depends(current_actor)):
    with connect() as db:
        quiz=quiz_row(db,quiz_id)
    course,_=get_course_and_lessons(quiz['course_id'],'Bearer '+bearer_token(authorization))
    require_teacher(course,actor)
    with connect() as db:
        if db.execute('SELECT 1 FROM attempts WHERE quiz_id=? LIMIT 1',(str(quiz_id),)).fetchone():
            raise HTTPException(409, detail='Questionário com respostas não pode ser excluído')
        db.execute('DELETE FROM quizzes WHERE id=?',(str(quiz_id),))
