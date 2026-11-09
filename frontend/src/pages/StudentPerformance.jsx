import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { assessmentsApi, recommendationsApi } from '../services/apiClient';
import Alert from '../components/Alert';
export default function StudentPerformance() {
  const {token,user}=useAuth();const [results,setResults]=useState([]);const [recommendations,setRecommendations]=useState([]);
  const [error,setError]=useState('');const [loading,setLoading]=useState(true);
  useEffect(()=>{let live=true;Promise.all([assessmentsApi.mine(token),recommendationsApi.mine(token)])
    .then(([notes,recs])=>{if(live){setResults(notes);setRecommendations(recs);}})
    .catch(e=>{if(live)setError(e.message);}).finally(()=>{if(live)setLoading(false);});return()=>{live=false;};},[token]);
  if(user?.role!=='student')return <section className="study-page"><Alert>Esta página é destinada aos alunos.</Alert></section>;
  return <section className="study-page"><h1>Notas e recomendações</h1><p>Veja as avaliações respondidas e as aulas de revisão sugeridas.</p><Alert>{error}</Alert>
    {loading?<p className="loading">Carregando seu desempenho...</p>:<>
      <section className="white-panel"><h2>Minhas notas</h2>{results.length?<div className="vertical-list">{results.map(r=><article className="quiz-list-item" key={r.attempt_id}><div><h3>{r.quiz_title}</h3><span className="muted-text">{r.correct_count}/{r.total} acertos</span></div><span className={r.score<7?'grade-pill grade-low':'grade-pill'}>{r.score.toFixed(2)}</span></article>)}</div>:<div className="empty-state">Você ainda não respondeu avaliações.</div>}</section>
      <section className="white-panel"><h2>Aulas recomendadas</h2>{recommendations.length?<div className="vertical-list">{recommendations.map(r=><article className="recommendation-item" key={r.id}><h3>{r.lesson_title}</h3><p>Na avaliação <strong>{r.quiz_title}</strong>, sua nota foi {r.score.toFixed(2)}. {r.reason}</p><Link className="small-link" to={`/cursos/${r.course_id}`}>Revisar aula no curso →</Link></article>)}</div>:<div className="empty-state">Nenhuma recomendação de revisão no momento. As sugestões aparecem quando uma nota é inferior a 7,0.</div>}</section>
    </>}
  </section>;
}
