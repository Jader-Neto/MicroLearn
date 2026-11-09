# Contratos REST do MicroLearn - Sprint 4

**Base externa:** `http://localhost:8000/api/v1`. A Gateway encaminha requisições a cada microsserviço, mediante validação JWT para rotas protegidas.

As descrições abaixo refletem os métodos registrados no código FastAPI, não uma especificação hipotética. Autorização de recursos ocorre nos respectivos microsserviços.

## Autenticação

| Método | Caminho externo | Endpoint Python |
|---|---|---|
| POST | `/api/v1/auth/register` | `register` |
| POST | `/api/v1/auth/login` | `login` |
| GET | `/api/v1/auth/me` | `me` |
| GET | `/api/v1/auth/users` | `list_users` |
| PATCH | `/api/v1/auth/users/{user_id}` | `update_user` |

## Cursos

| Método | Caminho externo | Endpoint Python |
|---|---|---|
| GET | `/api/v1/courses` | `catalog` |
| GET | `/api/v1/courses/owned` | `owned` |
| GET | `/api/v1/courses/enrollments/mine` | `my_enrollments` |
| POST | `/api/v1/courses` | `create_course` |
| GET | `/api/v1/courses/{course_id}` | `detail` |
| PATCH | `/api/v1/courses/{course_id}` | `update_course` |
| DELETE | `/api/v1/courses/{course_id}` | `delete_course` |
| POST | `/api/v1/courses/{course_id}/enrollments` | `enroll` |
| GET | `/api/v1/courses/{course_id}/lessons` | `lessons` |
| POST | `/api/v1/courses/{course_id}/lessons` | `create_lesson` |
| PATCH | `/api/v1/courses/{course_id}/lessons/{lesson_id}` | `edit_lesson` |
| DELETE | `/api/v1/courses/{course_id}/lessons/{lesson_id}` | `delete_lesson` |

## Avaliações

| Método | Caminho externo | Endpoint Python |
|---|---|---|
| POST | `/api/v1/assessments/courses/{course_id}/quizzes` | `create_quiz` |
| GET | `/api/v1/assessments/courses/{course_id}/quizzes` | `list_quizzes` |
| GET | `/api/v1/assessments/results/mine` | `results_mine` |
| GET | `/api/v1/assessments/courses/{course_id}/results` | `results_for_teacher` |
| GET | `/api/v1/assessments/quizzes/{quiz_id}` | `quiz_detail` |
| POST | `/api/v1/assessments/quizzes/{quiz_id}/submit` | `submit` |
| DELETE | `/api/v1/assessments/quizzes/{quiz_id}` | `delete_quiz` |

## Recomendações

| Método | Caminho externo | Endpoint Python |
|---|---|---|
| GET | `/api/v1/recommendations/mine` | `my_recommendations` |

## Monitoramento

- `GET /health`: Gateway funcionando.
- `GET /api/v1/status`: verifica os quatro microsserviços e retorna `all_healthy` e `services`.
- Cada serviço interno também oferece `GET /health` na rede do Compose.

## Segurança e persistência

- JWT válido obrigatório para operações privadas.
- O serviço Auth valida perfil atualizado e estado da conta nas operações protegidas.
- Bancos SQLite próprios por domínio, em volumes separados do Compose.
- O cadastro público atribui somente o perfil `student`. O administrador autoriza professores pela rota `PATCH /auth/users/{user_id}`.
