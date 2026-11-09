"""Primitivas JWT compartilhadas entre gateway e serviços (sem acesso a bancos)."""
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import HTTPException, status

ALGORITHM = "HS256"
ISSUER = "microlearn-auth"
AUDIENCE = "microlearn-api"


def _secret() -> str:
    secret = os.getenv("JWT_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET precisa ter pelo menos 32 caracteres")
    return secret


def issue_token(user_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + timedelta(minutes=60),
    }
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        data = jwt.decode(
            token,
            _secret(),
            algorithms=[ALGORITHM],
            issuer=ISSUER,
            audience=AUDIENCE,
            options={"require": ["sub", "exp", "iat", "role", "iss", "aud"]},
        )
        if data.get("role") not in {"student", "teacher", "manager"}:
            raise jwt.InvalidTokenError("papel inválido")
        return data
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ausente, inválido ou expirado", headers={"WWW-Authenticate": "Bearer"}) from exc


def bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Autenticação necessária", headers={"WWW-Authenticate": "Bearer"})
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Autenticação necessária")
    return token
