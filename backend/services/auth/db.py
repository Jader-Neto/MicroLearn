"""SQLite exclusivo do serviço de Autenticação. Nunca compartilhado entre serviços."""
import base64
import hashlib
import hmac
import os
import sqlite3
import uuid
from contextlib import contextmanager


def db_file() -> str:
    return os.getenv("AUTH_DB_PATH", "/data/auth.sqlite3")


@contextmanager
def connect():
    path = db_file()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    rounds = 600_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
    return "pbkdf2_sha256${}${}${}".format(rounds, base64.b64encode(salt).decode(), base64.b64encode(digest).decode())


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt, expected = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), base64.b64decode(salt), int(rounds))
        return hmac.compare_digest(derived, base64.b64decode(expected))
    except (ValueError, TypeError):
        return False


def init_db():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student','teacher','manager')),
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")


def bootstrap_manager():
    """Cria administrador apenas mediante credenciais fornecidas pelo operador."""
    email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    password = os.getenv("ADMIN_PASSWORD", "")
    if not email and not password:
        return
    if not email or len(password) < 12:
        raise RuntimeError("ADMIN_EMAIL e ADMIN_PASSWORD (mínimo 12 caracteres) são necessários juntos")
    with connect() as db:
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if not existing:
            db.execute("INSERT INTO users (id,name,email,password_hash,role) VALUES (?,?,?,?,?)", (
                str(uuid.uuid4()), "Administrador", email, hash_password(password), "manager"
            ))


def safe_user(row) -> dict:
    return {"id": row["id"], "name": row["name"], "email": row["email"], "role": row["role"], "active": bool(row["active"])}
