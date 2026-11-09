"""Escopo Sprint 1: serviço pronto para implantação; CRUD chegará nas Sprints 2/3."""
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException


def create_stub_app(name: str, sprint: int) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        path = Path(os.environ.get("DB_PATH", f"/data/{name}.sqlite3"))
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS service_metadata (key TEXT PRIMARY KEY, value TEXT)")
            db.execute("INSERT OR REPLACE INTO service_metadata VALUES ('name', ?)", (name,))
        yield

    app = FastAPI(title=f"MicroLearn - {name.title()}", version="0.1.0", lifespan=lifespan)

    @app.get("/health")
    def health():
        path = os.environ.get("DB_PATH", f"/data/{name}.sqlite3")
        with sqlite3.connect(path) as db:
            db.execute("SELECT 1").fetchone()
        return {"service": name, "status": "ok", "implementation": f"planned_for_sprint_{sprint}"}

    @app.api_route("/{path:path}", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
    def pending(path: str):
        raise HTTPException(status_code=501, detail=f"Funcionalidade de {name} prevista para Sprint {sprint}")

    return app
