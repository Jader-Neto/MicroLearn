"""Persistência exclusiva do serviço Cursos; nenhuma tabela de outro domínio é acessada."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


def db_path():
    return Path(os.getenv('DB_PATH', '/data/courses.sqlite3'))


@contextmanager
def connect():
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys = ON')
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    with connect() as db:
        db.executescript('''
          CREATE TABLE IF NOT EXISTS courses (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL,
            category TEXT NOT NULL, teacher_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','published')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
          );
          CREATE TABLE IF NOT EXISTS lessons (
            id TEXT PRIMARY KEY, course_id TEXT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
            title TEXT NOT NULL, body TEXT NOT NULL, material_url TEXT,
            position INTEGER NOT NULL CHECK(position > 0),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
          );
          CREATE INDEX IF NOT EXISTS lessons_course ON lessons(course_id,position);
          CREATE TABLE IF NOT EXISTS enrollments (
            id TEXT PRIMARY KEY, course_id TEXT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
            student_id TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(course_id, student_id)
          );
          CREATE INDEX IF NOT EXISTS enrollment_student ON enrollments(student_id);
        ''')


def as_dict(row):
    return dict(row) if row is not None else None
