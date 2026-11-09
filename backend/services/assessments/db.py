"""Banco SQLite exclusivo do serviço Avaliações."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


def path():
    return Path(os.getenv('DB_PATH', '/data/assessments.sqlite3'))


@contextmanager
def connect():
    dest = path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(dest, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
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
            CREATE TABLE IF NOT EXISTS quizzes (
                id TEXT PRIMARY KEY, course_id TEXT NOT NULL,
                teacher_id TEXT NOT NULL, lesson_id TEXT NOT NULL,
                title TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS quiz_course ON quizzes(course_id);
            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY, quiz_id TEXT NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
                position INTEGER NOT NULL, statement TEXT NOT NULL,
                options_json TEXT NOT NULL, correct_index INTEGER NOT NULL,
                UNIQUE(quiz_id,position)
            );
            CREATE TABLE IF NOT EXISTS attempts (
                id TEXT PRIMARY KEY, quiz_id TEXT NOT NULL REFERENCES quizzes(id),
                student_id TEXT NOT NULL, answers_json TEXT NOT NULL,
                correct_count INTEGER NOT NULL, total INTEGER NOT NULL,
                score REAL NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(quiz_id,student_id)
            );
            CREATE INDEX IF NOT EXISTS attempt_student ON attempts(student_id);
        ''')
