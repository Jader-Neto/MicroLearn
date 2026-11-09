import { useState } from 'react';
import Alert from './Alert';

const blank = () => ({ statement: '', options: ['', '', ''], correct_index: 0 });
export default function AssessmentEditor({ lessons, onSave, onCancel }) {
  const [title, setTitle] = useState('');
  const [lessonId, setLessonId] = useState(lessons[0]?.id || '');
  const [questions, setQuestions] = useState([blank()]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  function editQuestion(index, update) { setQuestions(all => all.map((q, i) => i === index ? { ...q, ...update } : q)); }
  function editOption(index, optionIndex, value) {
    setQuestions(all => all.map((q, i) => i === index ? { ...q, options: q.options.map((v, j) => j === optionIndex ? value : v) } : q));
  }
  async function handleSubmit(event) {
    event.preventDefault(); setError(''); setBusy(true);
    try {
      await onSave({ title, lesson_id: lessonId, questions });
      setTitle(''); setQuestions([blank()]);
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }
  return <form className="study-form assessment-form" onSubmit={handleSubmit}>
    <h3>Novo questionário</h3><Alert>{error}</Alert>
    <label htmlFor="quiz-title">Título</label><input id="quiz-title" required minLength="3" maxLength="150" value={title} onChange={e=>setTitle(e.target.value)}/>
    <label htmlFor="quiz-lesson">Aula recomendada para revisão</label>
    <select id="quiz-lesson" required value={lessonId} onChange={e=>setLessonId(e.target.value)}>
      {lessons.map(l=><option key={l.id} value={l.id}>{l.position}. {l.title}</option>)}
    </select>
    {questions.map((q,i)=><section className="question-editor" key={i}>
      <div className="heading-inline"><h4>Questão {i+1}</h4>{questions.length>1&&<button type="button" className="text-action danger" onClick={()=>setQuestions(all=>all.filter((_,j)=>i!==j))}>Remover</button>}</div>
      <label htmlFor={`question-${i}`}>Enunciado</label><textarea id={`question-${i}`} required minLength="5" maxLength="1000" value={q.statement} onChange={e=>editQuestion(i,{statement:e.target.value})}/>
      {q.options.map((option,j)=><div className="option-editor" key={j}>
        <label htmlFor={`opt-${i}-${j}`}>Alternativa {j+1}</label>
        <input id={`opt-${i}-${j}`} required maxLength="300" value={option} onChange={e=>editOption(i,j,e.target.value)}/>
      </div>)}
      <label htmlFor={`correct-${i}`}>Alternativa correta (visível somente na edição)</label>
      <select id={`correct-${i}`} value={q.correct_index} onChange={e=>editQuestion(i,{correct_index:Number(e.target.value)})}>
        {q.options.map((_,j)=><option value={j} key={j}>Alternativa {j+1}</option>)}
      </select>
    </section>)}
    <div className="inline-actions"><button type="button" className="secondary-button" onClick={()=>setQuestions(all=>[...all,blank()])} disabled={questions.length>=20}>Adicionar questão</button>
      <button type="submit" className="primary-button" disabled={busy||!lessonId}>{busy?'Salvando...':'Criar avaliação'}</button>
      <button type="button" className="text-action" onClick={onCancel}>Cancelar</button></div>
  </form>;
}
