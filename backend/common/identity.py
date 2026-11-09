"""Validação compartilhada da identidade ativa via API do Auth Service.

Não lê o banco de outro serviço. A assinatura do JWT e a conta atual são
verificadas em cada operação protegida (incluindo revogação de papéis).
"""
import os
import httpx
from fastapi import Header, HTTPException
from common.security import bearer_token, decode_token


def current_actor(authorization: str | None = Header(default=None)) -> dict:
    token = bearer_token(authorization)
    claims = decode_token(token)
    try:
        response = httpx.get(
            os.getenv('AUTH_URL', 'http://localhost:8001').rstrip('/') + '/auth/me',
            headers={'Authorization': f'Bearer {token}'}, timeout=3,
        )
    except httpx.RequestError as exc:
        raise HTTPException(503, detail='Autenticação temporariamente indisponível') from exc
    if response.status_code == 401:
        raise HTTPException(401, detail='Conta não autorizada ou desativada')
    if response.status_code != 200:
        raise HTTPException(503, detail='Falha ao verificar conta')
    actor = response.json()
    if actor.get('id') != claims['sub'] or actor.get('role') not in ('student', 'teacher', 'manager'):
        raise HTTPException(401, detail='Identidade inconsistente')
    return actor


def service_json(base_url: str, path: str, authorization: str, *, timeout: float = 4.0):
    """Consulta HTTP autenticada; preserva 401/403/404, falhas viram 503."""
    try:
        r = httpx.get(base_url.rstrip('/') + path, headers={'Authorization': authorization}, timeout=timeout)
    except httpx.RequestError as exc:
        raise HTTPException(503, detail='Serviço dependente indisponível') from exc
    if r.status_code in (401, 403, 404):
        raise HTTPException(r.status_code, detail=r.json().get('detail', 'Acesso negado ou recurso inexistente'))
    if r.status_code != 200:
        raise HTTPException(503, detail='Falha no serviço dependente')
    return r.json()
