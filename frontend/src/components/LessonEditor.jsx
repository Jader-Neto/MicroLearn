import { useState } from 'react';
import Alert from './Alert';

export default function LessonEditor({ onSubmit, initial=null, cancel }) {
  const [values,setValues]=useState({title:initial?.title||'',body:initial?.body||'',material_url:initial?.material_url||'',position:initial?.position||1});
  const [pending,setPending]=useState(false);const [error,setError]=useState('');
  async function save(event){
    event.preventDefault();setPending(true);setError('');
    try{await onSubmit({...values,position:Number(values.position),material_url:values.material_url||null});
      if(!initial)setValues({title:'',body:'',material_url:'',position:1});
    }catch(e){setError(e.message);}finally{setPending(false);}
  }
  return <form className="study-form" onSubmit={save}>
    <label htmlFor="lesson-title">Título da aula</label><input id="lesson-title" value={values.title} minLength={3} maxLength={150} required onChange={e=>setValues(v=>({...v,title:e.target.value}))}/>
    <label htmlFor="lesson-body">Conteúdo da aula</label><textarea id="lesson-body" rows={6} value={values.body} required maxLength={12000} onChange={e=>setValues(v=>({...v,body:e.target.value}))}/>
    <label htmlFor="lesson-url">Link complementar (opcional)</label><input id="lesson-url" type="url" value={values.material_url} onChange={e=>setValues(v=>({...v,material_url:e.target.value}))} placeholder="https://..."/>
    <label htmlFor="lesson-position">Ordem da aula</label><input id="lesson-position" type="number" min={1} max={10000} value={values.position} onChange={e=>setValues(v=>({...v,position:e.target.value}))}/>
    <Alert>{error}</Alert><div className="inline-actions"><button className="primary-button" disabled={pending} type="submit">{pending?'Salvando...':initial?'Atualizar aula':'Adicionar aula'}</button>{cancel&&<button type="button" className="secondary-button" onClick={cancel}>Cancelar</button>}</div>
  </form>;
}
