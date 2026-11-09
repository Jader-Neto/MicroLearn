# Checklist da entrega acadêmica - Engenharia de Software 2026.2

## Implementado/documentado no código

- [x] Sistema AVA com quatro microsserviços de negócio e API Gateway
- [x] Frontend React baseado em componentes reutilizáveis
- [x] Cadastro, login, perfis, administração de usuários
- [x] Cursos, aulas, publicação e matrícula
- [x] Questionários, notas, gabarito protegido, tentativa única
- [x] Recomendações explicáveis por nota inferior a 7,0
- [x] Bancos privados por microsserviço
- [x] Endpoints REST documentados em `API_ENDPOINTS.md`
- [x] Testes automatizados e teste de integração HTTP real
- [x] Product Backlog e sprints preparados nos PDFs das etapas anteriores

## Evidências verificadas no computador do grupo

- [x] `docker compose up --build -d` e `docker compose ps` funcionando
- [x] `npm ci && npm run build` concluído
- [x] Listagem real: seis contêineres ativos, cinco backends saudáveis e sem reinícios
- [x] Home servida pelo Docker respondendo HTTP 200 e renderizada no Chrome
- [x] E2E pela API Docker: usuários, promoção, curso/aula, matrícula, avaliação, nota e recomendação

## Pendente de evidência para a entrega

- [ ] Capturas reais de interface: Home, Login, Cursos, Matrícula, Aulas, Questionário, Notas, Recomendações e Administração
- [ ] Identificar equipe, orientador e período no relatório acadêmico definitivo
- [ ] Repositório GitHub publicado e URL real na capa do relatório
- [ ] Ensaio visual da demonstração funcional ponta a ponta (o E2E pela API já foi aprovado)

## Observações de projeto

Não há agentes de IA na versão desenvolvida; o recomendador implementado usa regras determinísticas. A exclusão de um curso não executa transação distribuída para remoção de notas em outro microsserviço; há registro deste limite em README e no relatório.
