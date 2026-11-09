"""Cache de recomendações do próprio domínio, sem acesso a bancos externos."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


def db_path():
    return Path(os.getenv('DB_PATH', '/data/recommendations.sqlite3'))


@contextmanager
def connect():
    path = db_path()
    path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path,timeout=10)
    db.row_factory=sqlite3.Row
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
        db.execute('''CREATE TABLE IF NOT EXISTS recommendations(
          id TEXT PRIMARY KEY, student_id TEXT NOT NULL, attempt_id TEXT NOT NULL,
          course_id TEXT NOT NULL, lesson_id TEXT NOT NULL,
          lesson_title TEXT NOT NULL, quiz_title TEXT NOT NULL, score REAL NOT NULL,
          generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(student_id,attempt_id))''')
