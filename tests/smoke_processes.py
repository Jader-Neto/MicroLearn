"""Teste local de cinco processos reais. Não requer Docker nem frontend."""
import os
import json
import secrets
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
PORTS = {"auth":18101, "courses":18102, "assessments":18103, "recommendations":18104, "gateway":18100}
MODULES = {"auth":"services.auth.main:app", "courses":"services.courses.main:app", "assessments":"services.assessments.main:app", "recommendations":"services.recommendations.main:app", "gateway":"gateway.main:app"}


def wait_healthy(port, process, timeout=12):
    start = time.time()
    while time.time() - start < timeout:
        if process.poll() is not None:
            raise RuntimeError(f"Processo {port} terminou prematuramente")
        try:
            if httpx.get(f"http://127.0.0.1:{port}/health", timeout=0.8).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.2)
    raise TimeoutError(f"Não iniciou na porta {port}")


def main():
    processes = []
    with tempfile.TemporaryDirectory() as tmp:
        base_env = os.environ.copy()
        base_env["PYTHONPATH"] = str(ROOT / "backend")
        base_env["JWT_SECRET"] = secrets.token_urlsafe(48)
        base_env["ADMIN_EMAIL"] = "admin@microlearn.local"
        base_env["ADMIN_PASSWORD"] = "senha-de-admin-teste-123456"
        for name in PORTS:
            if name != "gateway":
                env = base_env.copy()
                if name == "auth":
                    env["AUTH_DB_PATH"] = str(Path(tmp) / 'auth.sqlite3')
                else:
                    env["DB_PATH"] = str(Path(tmp) / (name + '.sqlite3'))
                    if name in ('courses','assessments','recommendations'):
                        env['AUTH_URL'] = f"http://127.0.0.1:{PORTS['auth']}"
                    if name in ('assessments','recommendations'):
                        env['COURSES_URL'] = f"http://127.0.0.1:{PORTS['courses']}"
                    if name == 'recommendations':
                        env['ASSESSMENTS_URL'] = f"http://127.0.0.1:{PORTS['assessments']}"
                p = subprocess.Popen([sys.executable, "-m", "uvicorn", MODULES[name], "--host", "127.0.0.1", "--port", str(PORTS[name]), "--log-level", "error"], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                processes.append(p)
                wait_healthy(PORTS[name], p)
        env = base_env.copy()
        for name in ("auth", "courses", "assessments", "recommendations"):
            env[name.upper() + "_URL"] = f"http://127.0.0.1:{PORTS[name]}"
        p = subprocess.Popen([sys.executable, "-m", "uvicorn", MODULES["gateway"], "--host", "127.0.0.1", "--port", str(PORTS["gateway"]), "--log-level", "error"], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        processes.append(p)
        try:
            wait_healthy(PORTS["gateway"], p)
            base = f"http://127.0.0.1:{PORTS['gateway']}"
            status = httpx.get(base + '/api/v1/status', timeout=6).json()
            assert status['all_healthy'] is True, status
            print('STATUS REAL DA API GATEWAY: '+json.dumps(status, ensure_ascii=False, sort_keys=True))
            print('OK: gateway e 4 microsserviços operacionais em processos separados')
            r = httpx.post(base + '/api/v1/auth/register',json={"name":"Aluno Exemplo","email":"aluno@example.com","password":"UmaSenhaSegura123!"}, timeout=7)
            assert r.status_code == 201, r.text
            print('OK: cadastro via gateway HTTP 201')
            r = httpx.post(base + '/api/v1/auth/login',json={"email":"aluno@example.com","password":"UmaSenhaSegura123!"}, timeout=7)
            assert r.status_code == 200, r.text
            token = r.json()['access_token']
            print('OK: login via gateway HTTP 200 e JWT emitido')
            r = httpx.get(base + '/api/v1/auth/me',headers={"Authorization":f"Bearer {token}"}, timeout=7)
            assert r.status_code == 200 and r.json()['role'] == 'student', r.text
            print('OK: /auth/me com JWT HTTP 200')
            r = httpx.get(base + '/api/v1/auth/me', timeout=7)
            assert r.status_code == 401
            print('OK: /auth/me sem JWT bloqueado HTTP 401')
            r = httpx.get(base + '/api/v1/courses',timeout=7)
            assert r.status_code == 200 and r.json() == [], r.text
            print('OK: catálogo público vazio HTTP 200')
            # Um administrador promove um aluno a professor por sua API.
            admin_login = httpx.post(base+'/api/v1/auth/login',json={
                'email':'admin@microlearn.local','password':'senha-de-admin-teste-123456'},timeout=8)
            assert admin_login.status_code == 200, admin_login.text
            admin_auth={'Authorization':'Bearer '+admin_login.json()['access_token']}
            new_teacher=httpx.post(base+'/api/v1/auth/register',json={
                'name':'Docente Demo','email':'docente@example.com','password':'UmaSenhaSegura123!'},timeout=8)
            assert new_teacher.status_code == 201,new_teacher.text
            promoted=httpx.patch(base+'/api/v1/auth/users/'+new_teacher.json()['id'],
                json={'role':'teacher'},headers=admin_auth,timeout=8)
            assert promoted.status_code == 200,promoted.text
            teacher_login=httpx.post(base+'/api/v1/auth/login',json={
                'email':'docente@example.com','password':'UmaSenhaSegura123!'},timeout=8)
            teacher_auth={'Authorization':'Bearer '+teacher_login.json()['access_token']}
            course=httpx.post(base+'/api/v1/courses',json={
                'title':'Fundamentos de Python','description':'Primeiros passos com Python',
                'category':'Programação'},headers=teacher_auth,timeout=8)
            assert course.status_code == 201,course.text
            cid=course.json()['id']
            lesson=httpx.post(base+f'/api/v1/courses/{cid}/lessons',json={
                'title':'Variáveis em Python','body':'Tipos, atribuições e exemplos','position':1},
                headers=teacher_auth,timeout=8)
            assert lesson.status_code == 201,lesson.text
            published=httpx.patch(base+f'/api/v1/courses/{cid}',json={'status':'published'},
                                  headers=teacher_auth,timeout=8)
            assert published.status_code == 200,published.text
            assert len(httpx.get(base+'/api/v1/courses',timeout=8).json()) == 1
            print('OK: professor cria curso, adiciona aula e publica via Gateway')
            enrolled=httpx.post(base+f'/api/v1/courses/{cid}/enrollments',
                                headers={'Authorization':'Bearer '+token},timeout=8)
            assert enrolled.status_code == 201,enrolled.text
            enrolled_again=httpx.post(base+f'/api/v1/courses/{cid}/enrollments',
                                headers={'Authorization':'Bearer '+token},timeout=8)
            assert enrolled_again.status_code == 409,enrolled_again.text
            lessons=httpx.get(base+f'/api/v1/courses/{cid}/lessons',
                                headers={'Authorization':'Bearer '+token},timeout=8)
            assert lessons.status_code == 200 and len(lessons.json()) == 1,lessons.text
            print('OK: aluno matricula-se, duplicidade bloqueada e aulas disponíveis')
            student_create=httpx.post(base+'/api/v1/courses',json={
                'title':'Curso indevido','description':'Não autorizado','category':'Dev'},
                headers={'Authorization':'Bearer '+token},timeout=8)
            assert student_create.status_code == 403,student_create.text
            print('OK: aluno não pode criar curso HTTP 403')
            # Sprint 3: questionário de duas questões, nota baixa e recomendação.
            quiz=httpx.post(base+f'/api/v1/assessments/courses/{cid}/quizzes',
                headers=teacher_auth,json={'title':'Avaliação de Python', 'lesson_id':lesson.json()['id'],
                  'questions':[{'statement':'Qual é o resultado de 2+2?',
                     'options':['3','4','5'],'correct_index':1},
                    {'statement':'Qual é o resultado de 3+3?',
                     'options':['5','6','7'],'correct_index':1}]},timeout=8)
            assert quiz.status_code==201,quiz.text
            quiz_id=quiz.json()['id']
            student_auth={'Authorization':'Bearer '+token}
            detail=httpx.get(base+f'/api/v1/assessments/quizzes/{quiz_id}',headers=student_auth,timeout=8)
            assert detail.status_code==200 and 'correct_index' not in detail.text,detail.text
            print('OK: professor cria avaliação, aluno lê questões sem gabarito')
            sent=httpx.post(base+f'/api/v1/assessments/quizzes/{quiz_id}/submit',
                            headers=student_auth,json={'answers':[1,0]},timeout=8)
            assert sent.status_code==201 and sent.json()['score']==5.0,sent.text
            duplicate=httpx.post(base+f'/api/v1/assessments/quizzes/{quiz_id}/submit',
                            headers=student_auth,json={'answers':[1,1]},timeout=8)
            assert duplicate.status_code==409,duplicate.text
            grades=httpx.get(base+'/api/v1/assessments/results/mine',headers=student_auth,timeout=8)
            assert grades.status_code==200 and grades.json()[0]['score']==5.0,grades.text
            teacher_grades=httpx.get(base+f'/api/v1/assessments/courses/{cid}/results',headers=teacher_auth,timeout=8)
            assert teacher_grades.status_code==200 and teacher_grades.json()[0]['score']==5.0,teacher_grades.text
            print('OK: resposta é corrigida (5/10), segunda tentativa bloqueada e nota persistida')
            recs=httpx.get(base+'/api/v1/recommendations/mine',headers=student_auth,timeout=8)
            assert recs.status_code==200 and len(recs.json())==1,recs.text
            assert recs.json()[0]['lesson_id']==lesson.json()['id'],recs.text
            assert recs.json()[0]['score']==5.0
            print('OK: recomendação mostra aula correta para nota inferior a 7')
            # Aluno sem matrícula não pode consultar avaliação alheia.
            other=httpx.post(base+'/api/v1/auth/register',json={
               'name':'Aluno Sem Matrícula','email':'sem-matricula@example.com','password':'UmaSenhaSegura123!'},timeout=8)
            assert other.status_code==201,other.text
            other_login=httpx.post(base+'/api/v1/auth/login',json={
               'email':'sem-matricula@example.com','password':'UmaSenhaSegura123!'},timeout=8)
            other_auth={'Authorization':'Bearer '+other_login.json()['access_token']}
            no_access=httpx.get(base+f'/api/v1/assessments/quizzes/{quiz_id}',headers=other_auth,timeout=8)
            assert no_access.status_code==403,no_access.text
            assert httpx.get(base+'/api/v1/assessments/results/mine',headers=other_auth,timeout=8).json()==[]
            print('OK: aluno não matriculado não acessa questionário nem notas de outro aluno')
            # Mudança de perfil invalida privilégios antigos mesmo com JWT ainda válido.
            demoted=httpx.patch(base+'/api/v1/auth/users/'+new_teacher.json()['id'],
                json={'role':'student'},headers=admin_auth,timeout=8)
            assert demoted.status_code == 200,demoted.text
            attempt=httpx.post(base+'/api/v1/courses',json={
                'title':'Tentativa posterior','description':'Professor removido',
                'category':'Dev'},headers=teacher_auth,timeout=8)
            assert attempt.status_code == 403,attempt.text
            print('OK: permissão de professor revogada bloqueia token antigo HTTP 403')
            print('RESULTADO: TESTE DE PROCESSOS CONCLUÍDO COM SUCESSO')
        finally:
            for process in reversed(processes):
                process.terminate()
            for process in reversed(processes):
                try:process.communicate(timeout=3)
                except subprocess.TimeoutExpired:process.kill()


if __name__ == '__main__':
    main()
