# Validação da Sprint 2 — 30/10/2026

## O que foi executado no ambiente de geração

- `python -m pytest -q`: **16 passed** (testes de Auth, Gateway, serviços e domínio Cursos).
- `python tests/smoke_processes.py`: **concluído com sucesso** com Gateway e quatro microsserviços FastAPI em cinco processos locais. Testou promoção de professor, curso, publicação, aula, matrícula, duplicidade, autorização e revogação de perfil.
- `python -m compileall -q backend`: **sem erros de compilação Python**.
- Parser TypeScript sobre 19 arquivos JS/JSX: **sem erros de sintaxe** (não equivale a build ou teste de navegador).
- YAML Compose parseado: **6 serviços** configurados (5 serviços FastAPI, incluindo Gateway, e 1 frontend React).

## Verificações ainda necessárias no Windows

- `docker compose up --build -d` e `docker compose ps`.
- `npm install` e `npm run build`: o acesso a registry.npmjs.org falhou neste ambiente (`EAI_AGAIN`).
- Visualização de telas no navegador e teste manual do formulário de curso e de aulas.
- Captura de `docker compose ps`, Swagger e telas para o relatório final da disciplina.

## Limites de segurança e implantação

- Validação de usuário e papel feita via HTTP ao Auth Service; sem compartilhamento de banco.
- Ainda não há revogação de JWT, rate limiting, HTTPS no ambiente local, proteção adicional contra XSS e testes de carga.
- O serviço Avaliações e Recomendações continua sinalizando `501 Not Implemented` até a Sprint 3.
