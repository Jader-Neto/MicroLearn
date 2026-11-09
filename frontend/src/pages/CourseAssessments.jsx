import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { assessmentsApi, coursesApi } from '../services/apiClient';
import Alert from '../components/Alert';
import AssessmentEditor from '../components/AssessmentEditor';

export default function CourseAssessments() {
  const { id } = useParams(); const { user, token } = useAuth();
  const [course, setCourse] = useState(null); const [quizzes,setQuizzes] = useState([]);
  const [lessons, setLessons] = useState([]); const [results, setResults] = useState([]);
  const [showForm,setShowForm] = useState(false); const [error,setError] = useState(''); const [info,setInfo] = useState('');
  const [loading,setLoading] = useState(true);
  const owner = user?.role === 'teacher' && course?.teacher_id === user.id;
  useEffect(()=>{
    let live=true; setLoading(true); setError('');
    Promise.all([coursesApi.detail(id,token), coursesApi.lessons(id,token), assessmentsApi.byCourse(id,token)])
      .then(([c,l,q])=>{if(live){setCourse(c);setLessons(l);setQuizzes(q);}})
      .catch(e=>{if(live)setError(e.message);}).finally(()=>{if(live)setLoading(false);});
    return ()=>{live=false;};
  },[id,token]);
  useEffect(()=>{if(owner){assessmentsApi.courseResults(id,token).then(setResults).catch(e=>setError(e.message));}},[owner,id,token]);
  async function createQuiz(values){const quiz=await assessmentsApi.create(id,values,token);setQuizzes(v=>[...v,quiz]);setShowForm(false);setInfo('Avaliação cadastrada.');}
  async function removeQuiz(quizId){if(!window.confirm('Excluir avaliação ainda sem respostas?'))return;try{await assessmentsApi.remove(quizId,token);setQuizzes(v=>v.filter(q=>q.id!==quizId));}catch(e){setError(e.message);}}
  return <section className="study-page"><Link className="small-link" to={`/cursos/${id}`}>← Voltar ao curso</Link>
    <h1>Avaliações {course ? `— ${course.title}` : ''}</h1><p>Questionários objetivos e notas de 0 a 10. Cada aluno pode responder uma vez.</p>
    <Alert>{error}</Alert><Alert variant="success">{info}</Alert>
    {loading ? <p className="loading">Carregando avaliações...</p> : <>
      {owner && <div className="white-panel"><div className="heading-inline"><h2>Gerenciar avaliações</h2><button className="primary-button" onClick={()=>setShowForm(v=>!v)} disabled={!lessons.length}>{showForm?'Fechar':'Nova avaliação'}</button></div>
        {!lessons.length && <p>Cadastre uma aula antes de criar um questionário.</p>}
        {showForm && !!lessons.length && <AssessmentEditor lessons={lessons} onSave={createQuiz} onCancel={()=>setShowForm(false)}/>}</div>}
      <div className="white-panel"><h2>Questionários disponíveis</h2>{quizzes.length ? <div className="vertical-list">{quizzes.map(q=><article className="quiz-list-item" key={q.id}><div><h3>{q.title}</h3><span className="muted-text">{q.question_count} questão(ões)</span></div><div className="inline-actions"><Link className="secondary-button" to={`/avaliacoes/${q.id}`}>{owner?'Visualizar':'Responder'}</Link>{owner&&<button className="text-action danger" onClick={()=>removeQuiz(q.id)}>Excluir</button>}</div></article>)}</div> : <div className="empty-state">Nenhuma avaliação cadastrada neste curso.</div>}</div>
      {owner&&<section className="white-panel"><h2>Resultados dos alunos</h2>{results.length ? <div className="results-table-wrapper"><table className="results-table"><thead><tr><th>Questionário</th><th>ID do aluno</th><th>Acertos</th><th>Nota</th></tr></thead><tbody>{results.map(r=><tr key={r.attempt_id}><td>{r.quiz_title}</td><td><code>{r.student_id.slice(0,8)}...</code></td><td>{r.correct_count}/{r.total}</td><td>{r.score.toFixed(2)}</td></tr>)}</tbody></table></div>:<p className="muted-text">Ainda não há respostas registradas.</p>}</section>}
    </>}
  </section>;
}
