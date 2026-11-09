import { useEffect,useState } from 'react';
import { Link,Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { coursesApi } from '../services/apiClient';
import CourseCard from '../components/CourseCard';
import Alert from '../components/Alert';
export default function MyEnrollments(){
  const {user,token}=useAuth();const [courses,setCourses]=useState([]);const [loading,setLoading]=useState(true);const [error,setError]=useState('');
  useEffect(()=>{if(user?.role==='student') coursesApi.enrolled(token).then(setCourses).catch(e=>setError(e.message)).finally(()=>setLoading(false));},[token,user?.role]);
  if(user?.role!=='student')return <Navigate to="/painel" replace/>;
  return <section className="study-page"><span className="eyebrow">MINHA JORNADA</span><h1>Meus cursos</h1><p>Seu conteúdo de aprendizagem fica disponível aqui.</p><Alert>{error}</Alert>{loading?<p>Carregando matrículas...</p>:courses.length?<div className="courses-grid">{courses.map(c=><CourseCard key={c.id} course={c} label="Abrir aulas"/>)}</div>:<div className="empty-state">Você ainda não se matriculou em nenhum curso. <Link to="/cursos">Explorar catálogo</Link></div>}</section>
}
