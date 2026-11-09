# MicroLearn - Evidências de validação da Sprint 3

**Escopo:** autenticação, cursos, questionários, correção, notas, recomendações e integração pela Gateway.

## Verificações executadas

- `PYTHONPATH=backend python -m pytest -q`: **21 testes aprovados** (inclui os testes das Sprints 1 e 2).
- `PYTHONPATH=backend python tests/smoke_processes.py`: cinco processos reais de API subiram com bancos temporários independentes; todos saudáveis; fluxo de professor, aluno, avaliação, nota 5/10 e recomendação da aula realizado de ponta a ponta.
- Regras verificadas: gabarito omitido na API de consulta, uma tentativa por quiz e aluno (409), matrícula obrigatória (403), resultados individuais protegidos, professor vê resultados do próprio curso, revogação de permissões em Auth.
- `typescript.transpileModule` analisou **23 arquivos JS/JSX sem diagnóstico de erro de sintaxe** (não corresponde a um build completo).

## Limites da validação

- A execução Docker Compose e a instalação/build npm não foram realizados neste ambiente.
- Não houve testes automatizados de navegação em navegador, acessibilidade ou apresentação responsiva.
- O sistema é um protótipo acadêmico e ainda requer política de limpeza distribuída ao excluir cursos e aulas; documentos e notas históricos não são apagados automaticamente entre serviços.

## Comandos de conferência no Windows

```powershell
Copy-Item .env.example .env
# Configure JWT_SECRET, ADMIN_EMAIL e ADMIN_PASSWORD no .env
docker compose up --build -d
docker compose ps
# no backend
python -m pytest -q
python tests/smoke_processes.py
# em frontend/
npm install
npm run build
```

Para evidências finais da disciplina, capture `docker compose ps`, Swagger Gateway, criação de questionário, resposta de aluno, notas e recomendações no navegador.
