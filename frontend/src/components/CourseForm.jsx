import { useState } from 'react';
import Alert from './Alert';

export default function CourseForm({ initial, onSubmit, submitLabel='Salvar curso' }) {
  const [values, setValues] = useState({title:initial?.title||'', description:initial?.description||'', category:initial?.category||''});
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  async function save(event) {
    event.preventDefault();setPending(true);setError('');
    try { await onSubmit(values); if (!initial) setValues({title:'',description:'',category:''}); }
    catch (err) {setError(err.message);}
    finally {setPending(false);}
  }
  return <form className="study-form" onSubmit={save}>
    <label htmlFor="course-title">Título do curso</label><input id="course-title" required minLength={3} maxLength={120} value={values.title} onChange={event=>setValues(v=>({...v,title:event.target.value}))}/>
    <label htmlFor="course-category">Categoria</label><input id="course-category" required minLength={2} maxLength={80} value={values.category} onChange={event=>setValues(v=>({...v,category:event.target.value}))} placeholder="Ex.: Programação"/>
    <label htmlFor="course-description">Descrição</label><textarea id="course-description" required minLength={5} maxLength={3000} rows={4} value={values.description} onChange={event=>setValues(v=>({...v,description:event.target.value}))}/>
    <Alert>{error}</Alert><button type="submit" disabled={pending} className="primary-button">{pending?'Salvando...':submitLabel}</button>
  </form>;
}
