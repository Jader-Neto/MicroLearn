"""Autenticação: registro público de alunos, login, perfis e administração."""
import sqlite3
import uuid
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from common.security import bearer_token, decode_token, issue_token
from .db import bootstrap_manager, connect, hash_password, init_db, safe_user, verify_password

# EmailStr requer email-validator; validamos e-mail sem dependência adicional.
import re

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    bootstrap_manager()
    yield


app = FastAPI(title="MicroLearn - Autenticação", version="0.1.0", lifespan=lifespan)


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


class UserUpdate(BaseModel):
    role: Literal["student", "teacher", "manager"] | None = None
    active: bool | None = None


def normalize_email(value: str) -> str:
    email = value.strip().lower()
    if not EMAIL_RE.fullmatch(email):
        raise HTTPException(status_code=422, detail="E-mail inválido")
    return email


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    claims = decode_token(bearer_token(authorization))
    with connect() as db:
        row = db.execute("SELECT * FROM users WHERE id = ?", (claims["sub"],)).fetchone()
    if not row or not row["active"]:
        raise HTTPException(status_code=401, detail="Usuário desativado ou inexistente")
    # Não permitir que o JWT antigo continue carregando permissões revogadas.
    user = safe_user(row)
    return user


def manager(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "manager":
        raise HTTPException(status_code=403, detail="Operação restrita ao administrador")
    return user


@app.get("/health")
def health():
    with connect() as db:
        db.execute("SELECT 1").fetchone()
    return {"service": "auth", "status": "ok"}


@app.post("/auth/register", status_code=201)
def register(body: RegisterRequest):
    email = normalize_email(body.email)
    user_id = str(uuid.uuid4())
    try:
        with connect() as db:
            db.execute("INSERT INTO users (id,name,email,password_hash,role) VALUES (?,?,?,?,?)", (
                user_id, body.name.strip(), email, hash_password(body.password), "student"
            ))
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="E-mail já cadastrado") from exc
    return {"id": user_id, "name": body.name.strip(), "email": email, "role": "student", "active": True}


@app.post("/auth/login")
def login(body: LoginRequest):
    email = normalize_email(body.email)
    with connect() as db:
        row = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not row or not verify_password(body.password, row["password_hash"]) or not row["active"]:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    return {"access_token": issue_token(row["id"], row["role"]), "token_type": "bearer", "role": row["role"]}


@app.get("/auth/me")
def me(user: dict = Depends(get_current_user)):
    return user


@app.get("/auth/users")
def list_users(_=Depends(manager)):
    with connect() as db:
        rows = db.execute("SELECT * FROM users ORDER BY created_at, email").fetchall()
    return [safe_user(row) for row in rows]


@app.patch("/auth/users/{user_id}")
def update_user(user_id: uuid.UUID, body: UserUpdate, actor: dict = Depends(manager)):
    updates = body.model_dump(exclude_unset=True)
    if not updates or any(value is None for value in updates.values()):
        raise HTTPException(status_code=422, detail="Informe role e/ou active com valores válidos")
    if actor["id"] == str(user_id) and (updates.get("active") is False or ("role" in updates and updates["role"] != "manager")):
        raise HTTPException(status_code=409, detail="Administrador não pode remover o próprio acesso")
    columns = ", ".join(f"{name} = ?" for name in updates)
    values = [int(value) if name == "active" else value for name, value in updates.items()]
    with connect() as db:
        updated = db.execute(f"UPDATE users SET {columns} WHERE id = ?", (*values, str(user_id)))
        if not updated.rowcount:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        row = db.execute("SELECT * FROM users WHERE id = ?", (str(user_id),)).fetchone()
    return safe_user(row)
