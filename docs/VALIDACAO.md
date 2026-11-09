# Sprint 1 — Registro de validação

**Ambiente de execução do assistente:** Python com FastAPI, httpx, uvicorn, pytest e PyJWT. Não possui Docker instalado; o npm não conseguiu instalar dependências no momento da geração.

## Evidências confirmadas

- `pytest -q`: **10 passed**.
- `python tests/smoke_processes.py`: backend realmente executado em cinco processos Python independentes (quatro serviços de negócio e a Gateway).
- O smoke test confirmou `GET /api/v1/status` com `all_healthy=true`.
- Registro pela Gateway HTTP `201`, login HTTP `200` com JWT, `/auth/me` autenticado HTTP `200` e sem token HTTP `401`.
- O domínio Cursos retornou intencionalmente HTTP `501`, indicando a futura implementação.
- YAML do `docker-compose.yml` analisado com PyYAML sem erro.
- 12 arquivos JavaScript/JSX passaram na verificação sintática pelo parser TypeScript.

## Pendente de validação no PC do aluno

- `docker compose up --build -d` e `docker compose ps`.
- `npm install` / `npm run build` do frontend React.
- Fluxo cadastro → login → painel no navegador.
- Capturas para relatório final do professor.

**Apenas verificações realmente executadas foram consideradas aprovadas.**
