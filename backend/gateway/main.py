"""Gateway HTTP: roteamento explícito, validação JWT e tratamento de falhas de rede."""
import asyncio
import os

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from common.security import bearer_token, decode_token

SERVICE_MAP = {
    "auth": os.getenv("AUTH_URL", "http://localhost:8001"),
    "courses": os.getenv("COURSES_URL", "http://localhost:8002"),
    "assessments": os.getenv("ASSESSMENTS_URL", "http://localhost:8003"),
    "recommendations": os.getenv("RECOMMENDATIONS_URL", "http://localhost:8004"),
}
TIMEOUT = httpx.Timeout(5.0)
app = FastAPI(title="MicroLearn - API Gateway", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[v.strip() for v in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if v.strip()],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/health")
def health():
    return {"service": "gateway", "status": "ok"}


@app.get("/api/v1/status")
async def service_status():
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        async def probe(name: str, base: str):
            try:
                response = await client.get(base + "/health")
                return {"service": name, "ok": response.status_code == 200}
            except httpx.HTTPError:
                return {"service": name, "ok": False}
        values = await asyncio.gather(*(probe(k, v) for k, v in SERVICE_MAP.items()))
    return {"gateway": "ok", "services": values, "all_healthy": all(x["ok"] for x in values)}


def is_public(service: str, path: str, method: str) -> bool:
    return (service == "auth" and method == "POST" and path in {"register", "login"}) or (service == "courses" and method == "GET" and path == "")


@app.api_route("/api/v1/{service}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@app.api_route("/api/v1/{service}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def forward(service: str, request: Request, path: str = ""):
    if service not in SERVICE_MAP:
        raise HTTPException(status_code=404, detail="Microsserviço desconhecido")
    path = path.strip("/")
    if not is_public(service, path, request.method):
        decode_token(bearer_token(request.headers.get("authorization")))
    url = f"{SERVICE_MAP[service].rstrip('/')}/{service}"
    if path:
        url += "/" + path
    if request.url.query:
        url += "?" + request.url.query
    headers = {"Accept": "application/json"}
    for key in ("authorization", "content-type"):
        if key in request.headers:
            headers[key] = request.headers[key]
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=False) as client:
            r = await client.request(request.method, url, content=await request.body(), headers=headers)
        return Response(content=r.content, status_code=r.status_code, media_type=r.headers.get("content-type", "application/json"))
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=503, detail="Tempo limite ao consultar o microsserviço") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=503, detail="Microsserviço indisponível") from exc
