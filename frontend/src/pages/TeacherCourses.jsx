import { useEffect, useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { coursesApi } from '../services/apiClient';
import CourseCard from '../components/CourseCard';
import CourseForm from '../components/CourseForm';
import Alert from '../components/Alert';

export default function TeacherCourses() {
  const {token,user}=useAuth();
  const [items,setItems]=useState([]);const [error,setError]=useState('');const [success,setSuccess]=useState('');const [loading,setLoading]=useState(true);
  useEffect(()=>{if(user?.role==='teacher') coursesApi.owned(token).then(setItems).catch(e=>setError(e.message)).finally(()=>setLoading(false));},[token,user?.role]);
  if(user?.role!=='teacher') return <Navigate to="/painel" replace/>;
  async function create(values){const course=await coursesApi.create(values,token);setItems(v=>[course,...v]);setSuccess('Curso criado como rascunho. Adicione aulas e publique quando estiver pronto.');}
  return <section className="study-page"><span className="eyebrow">PAINEL DO PROFESSOR</span><h1>Meus cursos</h1><p>Crie novos cursos, organize aulas e publique o conteúdo.</p><Alert>{error}</Alert><Alert variant="success">{success}</Alert>
    <div className="study-two-col"><section className="white-panel"><h2>Criar novo curso</h2><CourseForm onSubmit={create}/></section><section className="white-panel"><h2>Cursos sob sua responsabilidade</h2>{loading?<p>Carregando...</p>:items.length?<div className="vertical-list">{items.map(c=><CourseCard key={c.id} course={c} label="Gerenciar"/>)}</div>:<div className="empty-state">Nenhum curso criado até o momento.</div>}</section></div>
    <p className="hint-text"><Link to="/cursos">Ver catálogo público</Link></p>
  </section>;
}
