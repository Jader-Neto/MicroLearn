"""Domínio Cursos (Sprint 2): catálogo, autoria, aulas e matrículas.

Todas as operações protegidas validam o JWT e consultam a identidade ativa
no Auth pela API HTTP; o serviço nunca abre o banco do Auth.
"""
import os
import sqlite3
import uuid
from contextlib import asynccontextmanager
from typing import Literal

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, field_validator

from common.security import bearer_token, decode_token
from .db import as_dict, connect, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title='MicroLearn - Cursos', version='0.2.0', lifespan=lifespan)


def get_actor(authorization: str | None = Header(default=None)) -> dict:
    token = bearer_token(authorization)
    claims = decode_token(token)
    try:
        response = httpx.get(
            os.getenv('AUTH_URL', 'http://localhost:8001').rstrip('/') + '/auth/me',
            headers={'Authorization': f'Bearer {token}'}, timeout=3.0,
        )
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail='Autenticação temporariamente indisponível') from exc
    if response.status_code == 401:
        raise HTTPException(status_code=401, detail='Conta não autorizada ou desativada')
    if response.status_code != 200:
        raise HTTPException(status_code=503, detail='Falha ao validar identidade')
    actor = response.json()
    if actor.get('id') != claims['sub'] or actor.get('role') not in {'student', 'teacher', 'manager'}:
        raise HTTPException(status_code=401, detail='Identidade inconsistente')
    return actor


def require_role(actor: dict, role: str):
    if actor['role'] != role:
        raise HTTPException(status_code=403, detail=f'Operação restrita ao perfil {role}')


def get_course(db, course_id: uuid.UUID):
    row = db.execute('SELECT * FROM courses WHERE id=?', (str(course_id),)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='Curso não encontrado')
    return as_dict(row)


def require_owner(course: dict, actor: dict):
    require_role(actor, 'teacher')
    if course['teacher_id'] != actor['id']:
        raise HTTPException(status_code=403, detail='Curso pertence a outro professor')


def is_enrolled(db, course_id: str, student_id: str):
    return db.execute('SELECT 1 FROM enrollments WHERE course_id=? AND student_id=?',
                      (course_id, student_id)).fetchone() is not None


class CourseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=5, max_length=3000)
    category: str = Field(min_length=2, max_length=80)


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, min_length=5, max_length=3000)
    category: str | None = Field(default=None, min_length=2, max_length=80)
    status: Literal['draft', 'published'] | None = None


class LessonCreate(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    body: str = Field(min_length=1, max_length=12000)
    material_url: str | None = Field(default=None, max_length=500)
    position: int = Field(default=1, ge=1, le=10000)

    @field_validator('material_url')
    @classmethod
    def valid_url(cls, value):
        if value and not (value.startswith('https://') or value.startswith('http://')):
            raise ValueError('O endereço deve começar com http:// ou https://')
        return value or None


class LessonUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=150)
    body: str | None = Field(default=None, min_length=1, max_length=12000)
    material_url: str | None = Field(default=None, max_length=500)
    position: int | None = Field(default=None, ge=1, le=10000)

    @field_validator('material_url')
    @classmethod
    def valid_url(cls, value):
        if value and not (value.startswith('https://') or value.startswith('http://')):
            raise ValueError('O endereço deve começar com http:// ou https://')
        return value or None


@app.get('/health')
def health():
    with connect() as db:
        db.execute('SELECT 1').fetchone()
    return {'service': 'courses', 'status': 'ok', 'implementation': 'sprint_2'}


@app.get('/courses')
def catalog():
    """Consulta pública de cursos publicados; não retorna rascunhos."""
    with connect() as db:
        rows = db.execute('''SELECT c.*,
            (SELECT COUNT(*) FROM lessons l WHERE l.course_id=c.id) AS lesson_count
            FROM courses c WHERE status='published' ORDER BY created_at DESC,title''').fetchall()
    return [as_dict(r) for r in rows]


@app.get('/courses/owned')
def owned(actor: dict = Depends(get_actor)):
    require_role(actor, 'teacher')
    with connect() as db:
        rows = db.execute('SELECT * FROM courses WHERE teacher_id=? ORDER BY created_at DESC', (actor['id'],)).fetchall()
    return [as_dict(r) for r in rows]


@app.get('/courses/enrollments/mine')
def my_enrollments(actor: dict = Depends(get_actor)):
    require_role(actor, 'student')
    with connect() as db:
        rows = db.execute('''SELECT c.*,e.created_at AS enrolled_at
            FROM enrollments e JOIN courses c ON c.id=e.course_id
            WHERE e.student_id=? ORDER BY e.created_at DESC''',(actor['id'],)).fetchall()
    return [as_dict(r) for r in rows]


@app.post('/courses', status_code=201)
def create_course(body: CourseCreate, actor: dict = Depends(get_actor)):
    require_role(actor, 'teacher')
    course_id = str(uuid.uuid4())
    with connect() as db:
        db.execute('INSERT INTO courses (id,title,description,category,teacher_id) VALUES (?,?,?,?,?)',
                   (course_id, body.title.strip(), body.description.strip(), body.category.strip(), actor['id']))
        row = db.execute('SELECT * FROM courses WHERE id=?', (course_id,)).fetchone()
    return as_dict(row)


@app.get('/courses/{course_id}')
def detail(course_id: uuid.UUID, actor: dict = Depends(get_actor)):
    with connect() as db:
        course = get_course(db, course_id)
    if course['status'] == 'draft' and (actor['role'] != 'teacher' or actor['id'] != course['teacher_id']):
        raise HTTPException(status_code=404, detail='Curso não encontrado')
    return course


@app.patch('/courses/{course_id}')
def update_course(course_id: uuid.UUID, body: CourseUpdate, actor: dict = Depends(get_actor)):
    values = body.model_dump(exclude_unset=True)
    if not values or any(v is None for v in values.values()):
        raise HTTPException(status_code=422, detail='Informe campos válidos para alterar')
    with connect() as db:
        course = get_course(db, course_id)
        require_owner(course, actor)
        cols = ', '.join(f'{key}=?' for key in values)
        db.execute(f'UPDATE courses SET {cols}, updated_at=CURRENT_TIMESTAMP WHERE id=?',
                   [*([v.strip() if isinstance(v,str) else v for v in values.values()]),str(course_id)])
        return as_dict(db.execute('SELECT * FROM courses WHERE id=?',(str(course_id),)).fetchone())


@app.delete('/courses/{course_id}', status_code=204)
def delete_course(course_id: uuid.UUID, actor: dict = Depends(get_actor)):
    with connect() as db:
        course = get_course(db, course_id)
        require_owner(course, actor)
        db.execute('DELETE FROM courses WHERE id=?',(str(course_id),))


@app.post('/courses/{course_id}/enrollments', status_code=201)
def enroll(course_id: uuid.UUID, actor: dict = Depends(get_actor)):
    require_role(actor, 'student')
    with connect() as db:
        course = get_course(db, course_id)
        if course['status'] != 'published':
            raise HTTPException(status_code=409, detail='Curso ainda não está publicado')
        try:
            enrollment_id = str(uuid.uuid4())
            db.execute('INSERT INTO enrollments (id,course_id,student_id) VALUES (?,?,?)',
                       (enrollment_id,str(course_id),actor['id']))
        except sqlite3.IntegrityError as exc:
            raise HTTPException(status_code=409, detail='Aluno já matriculado neste curso') from exc
    return {'id': enrollment_id, 'course_id': str(course_id), 'student_id': actor['id']}


@app.get('/courses/{course_id}/lessons')
def lessons(course_id: uuid.UUID, actor: dict = Depends(get_actor)):
    with connect() as db:
        course = get_course(db, course_id)
        own_course = actor['role']=='teacher' and actor['id']==course['teacher_id']
        student_access = actor['role']=='student' and course['status']=='published' and is_enrolled(db,str(course_id),actor['id'])
        if not (own_course or student_access):
            raise HTTPException(status_code=403, detail='Matrícula ou autoria necessária para acessar aulas')
        rows = db.execute('SELECT * FROM lessons WHERE course_id=? ORDER BY position,created_at,id',
                          (str(course_id),)).fetchall()
    return [as_dict(row) for row in rows]


@app.post('/courses/{course_id}/lessons', status_code=201)
def create_lesson(course_id: uuid.UUID, body: LessonCreate, actor: dict = Depends(get_actor)):
    lesson_id = str(uuid.uuid4())
    with connect() as db:
        course = get_course(db, course_id)
        require_owner(course, actor)
        db.execute('''INSERT INTO lessons(id,course_id,title,body,material_url,position) VALUES (?,?,?,?,?,?)''',
                   (lesson_id,str(course_id),body.title.strip(),body.body.strip(),body.material_url,body.position))
        return as_dict(db.execute('SELECT * FROM lessons WHERE id=?',(lesson_id,)).fetchone())


def get_lesson(db, course_id: uuid.UUID, lesson_id: uuid.UUID):
    row = db.execute('SELECT * FROM lessons WHERE id=? AND course_id=?',(str(lesson_id),str(course_id))).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='Aula não encontrada neste curso')
    return as_dict(row)


@app.patch('/courses/{course_id}/lessons/{lesson_id}')
def edit_lesson(course_id: uuid.UUID, lesson_id: uuid.UUID, body: LessonUpdate, actor: dict = Depends(get_actor)):
    values=body.model_dump(exclude_unset=True)
    if not values or any(v is None for k,v in values.items() if k!='material_url'):
        raise HTTPException(status_code=422, detail='Informe campos válidos')
    with connect() as db:
        course=get_course(db,course_id)
        require_owner(course,actor)
        get_lesson(db,course_id,lesson_id)
        cols=', '.join(f'{key}=?' for key in values)
        db.execute(f'UPDATE lessons SET {cols} WHERE id=?', [*values.values(),str(lesson_id)])
        return get_lesson(db,course_id,lesson_id)


@app.delete('/courses/{course_id}/lessons/{lesson_id}',status_code=204)
def delete_lesson(course_id: uuid.UUID, lesson_id: uuid.UUID, actor: dict = Depends(get_actor)):
    with connect() as db:
        course=get_course(db,course_id)
        require_owner(course,actor)
        get_lesson(db,course_id,lesson_id)
        db.execute('DELETE FROM lessons WHERE id=?',(str(lesson_id),))
