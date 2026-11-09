import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { assessmentsApi } from '../services/apiClient';
import Alert from '../components/Alert';
export default function QuizDetail() {
  const { quizId }=useParams(); const { user, token }=useAuth();
  const [quiz,setQuiz]=useState(null); const [answers,setAnswers]=useState({}); const [result,setResult]=useState(null);
  const [error,setError]=useState(''); const [busy,setBusy]=useState(false);
  useEffect(()=>{let live=true;assessmentsApi.detail(quizId,token).then(data=>{if(live)setQuiz(data);}).catch(e=>{if(live)setError(e.message);});return()=>{live=false;};},[quizId,token]);
  async function submit(event) { event.preventDefault(); setError(''); setBusy(true);
    try { const grades=await assessmentsApi.submit(quizId,quiz.questions.map((_,i)=>Number(answers[i])),token);setResult(grades);setQuiz(q=>({...q,already_submitted:true,my_score:grades.score})); }
    catch(e){setError(e.message);}finally{setBusy(false);}
  }
  const isStudent=user?.role==='student';
  return <section className="study-page"><Link className="small-link" to={quiz?`/cursos/${quiz.course_id}/avaliacoes`:'/meus-cursos'}>← Voltar às avaliações</Link>
    <h1>{quiz?.title||'Questionário'}</h1><Alert>{error}</Alert>
    {quiz && <section className="white-panel"><p className="muted-text">{quiz.questions.length} questão(ões) • Uma tentativa por aluno</p>
      {quiz.already_submitted ? <div className="grade-result"><h2>Avaliação finalizada</h2><p>Sua nota: <strong>{quiz.my_score?.toFixed(2)} / 10</strong></p><Link className="small-link" to="/desempenho">Consultar notas e recomendações</Link></div> : <>
        {!isStudent&&<p>Prévia das questões. O gabarito não é incluído neste retorno de API.</p>}
        <form onSubmit={submit}>{quiz.questions.map((q,i)=><fieldset key={q.id} className="question-display"><legend><strong>{i+1}. {q.statement}</strong></legend>{q.options.map((option,j)=><label className="answer-choice" key={j}><input type="radio" name={`q-${i}`} value={j} checked={answers[i]===j} onChange={()=>setAnswers(a=>({...a,[i]:j}))} disabled={!isStudent}/><span>{option}</span></label>)}</fieldset>)}
          {isStudent&&<button className="primary-button" type="submit" disabled={busy||Object.keys(answers).length!==quiz.questions.length}>{busy?'Enviando...':'Finalizar avaliação'}</button>}
        </form></>}
      {result&&<Alert variant="success">Nota {result.score.toFixed(2)}. {result.recommend_review?'Consulte as aulas recomendadas para revisão.':'Bom resultado!'}</Alert>}
    </section>}
  </section>;
}
