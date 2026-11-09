import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import CourseCard from '../components/CourseCard';
import Alert from '../components/Alert';
import { coursesApi } from '../services/apiClient';
import { useAuth } from '../context/AuthContext';

export default function CoursesCatalog() {
  const [courses,setCourses]=useState([]);const [error,setError]=useState('');const [loading,setLoading]=useState(true);
  const {user}=useAuth();
  useEffect(()=>{coursesApi.catalog().then(setCourses).catch(e=>setError(e.message)).finally(()=>setLoading(false));},[]);
  return <section className="study-page"><span className="eyebrow">EXPLORE O CATÁLOGO</span><h1>Cursos disponíveis</h1><p>Explore cursos publicados e entre para realizar sua matrícula.</p>
    <Alert>{error}</Alert>{loading?<p>Carregando catálogo...</p>:courses.length?<div className="courses-grid">{courses.map(c=><CourseCard key={c.id} course={c} label={user?'Acessar curso':'Conhecer curso'}/>)}</div>:<div className="empty-state"><h3>Não há cursos publicados.</h3><p>Novos cursos aparecerão aqui após a publicação por um professor.</p></div>}
    {!user&&<p className="hint-text">Para acessar aulas e se matricular, <Link to="/entrar">entre na sua conta</Link>.</p>}
  </section>;
}
