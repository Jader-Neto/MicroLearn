# Registro de validação - MicroLearn - Sprint 4

**Escopo:** autenticação, administração de usuários, cursos, matrículas, avaliações, recomendações e monitoramento dos microsserviços.

## Verificações executadas no ambiente de geração

- `python -m pytest -q`: **24 testes aprovados novamente em 09/11/2026** pela `.venv`, incluindo três testes adicionais de gestão administrativa, reativação, permissões e validação de atualização.
- `PYTHONPATH=backend python tests/smoke_processes.py`: cinco processos Uvicorn independentes iniciados em portas de teste; Gateway e quatro microsserviços saudáveis; fluxo do professor/aluno/nota e recomendação aprovado.
- `npm ci` e `npm run build`: **build de produção aprovado** com Vite 6 e React 19 em 08/11/2026.
- Chrome headless em `http://127.0.0.1:5173`: **Home servida pelo Docker renderizada em 09/11/2026**, com resposta HTTP 200, estilos e navegação visíveis.
- `docker compose up --build -d` e `docker compose ps`: **execução aprovada em 09/11/2026**. Os seis contêineres ficaram ativos sem reinícios; Gateway, Auth, Courses, Assessments e Recommendations ficaram `healthy`, e o frontend permaneceu em execução.
- `GET /health` na Gateway respondeu HTTP 200; `GET /api/v1/status` informou os quatro microsserviços saudáveis. Os logs recentes dos seis contêineres não apresentaram erros, exceções, respostas HTTP 5xx ou falhas fatais.
- E2E pela API do ambiente Docker: **aprovado**. Foram validados cadastro de aluno e professor, promoção do professor pelo administrador, criação de curso e aula, publicação, matrícula, criação de questionário com duas questões, consulta sem exposição de `correct_index`, resposta com uma questão correta, nota 5,0, consulta do resultado e geração da recomendação. Ao final, `/api/v1/status` retornou `all_healthy=true`.
- A primeira execução no navegador revelou `ReferenceError: React is not defined` e tela em branco. A causa era o JSX clássico sem importação de `React`; `frontend/vite.config.js` passou a usar o runtime JSX automático. Build e navegador foram validados novamente após a correção.

## Evidência dos processos

O arquivo `smoke_test_results_sprint4.txt` contém o log do teste HTTP sem Docker. O script usa portas temporárias 18100-18104 e bancos temporários; nunca emprega dados pessoais reais. Na execução Compose, a seção `/api/v1/status` confirmou os quatro serviços pela Gateway e `docker compose ps` confirmou o estado dos seis contêineres.

O build padrão mantém a validação TLS. Quando um antivírus ou proxy inspeciona HTTPS, o arquivo opcional `docker-compose.ca.yml` permite fornecer uma CA pública local por `DOCKER_HOST_CA_FILE` apenas durante a instalação das dependências, sem desabilitar a verificação de certificados. O arquivo da CA deve permanecer fora do versionamento.

## Evidências visuais e próximos passos

1. Registrar capturas de cadastro/login e dos três painéis; a Home já foi visualmente validada.
2. Exercitar e capturar no navegador o fluxo de promoção do professor, CRUD de cursos e aulas, matrícula, avaliação e recomendação; esse mesmo fluxo já foi aprovado pela API Docker.
3. Verificar a apresentação em diferentes tamanhos de tela.
4. Inserir a URL do repositório já publicado na capa do relatório acadêmico final.

**Não afirmar que as verificações pendentes foram concluídas até possuírem evidências da execução local.**
