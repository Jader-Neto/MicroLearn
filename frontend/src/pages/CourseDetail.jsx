import { useEffect, useState } from 'react';
import { Link, useParams, Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { coursesApi } from '../services/apiClient';
import CourseForm from '../components/CourseForm';
import LessonEditor from '../components/LessonEditor';
import Alert from '../components/Alert';

export default function CourseDetail() {
  const {id}=useParams();const navigate=useNavigate();const {token,user}=useAuth();
  const [course,setCourse]=useState(null);const [lessons,setLessons]=useState([]);const [mine,setMine]=useState(false);
  const [error,setError]=useState('');const [info,setInfo]=useState('');const [loading,setLoading]=useState(true);
  const [showEdit,setShowEdit]=useState(false);const [editingLesson,setEditingLesson]=useState(null);const [showLessonForm,setShowLessonForm]=useState(false);
  const isOwner=user?.role==='teacher'&&course?.teacher_id===user.id;
  const isStudent=user?.role==='student';
  useEffect(()=>{
    let active=true;
    Promise.all([coursesApi.detail(id,token),user?.role==='student'?coursesApi.enrolled(token):Promise.resolve([])])
      .then(([c,enrolled])=>{if(active){setCourse(c);setMine(enrolled.some(item=>item.id===id));}})
      .catch(e=>{if(active)setError(e.message);}).finally(()=>{if(active)setLoading(false);});
    return()=>{active=false;};
  },[id,token,user?.role]);
  useEffect(()=>{if((isOwner||mine)&&id&&token){coursesApi.lessons(id,token).then(setLessons).catch(e=>setError(e.message));}},[id,token,isOwner,mine]);
  async function doEnroll(){setError('');try{await coursesApi.enroll(id,token);setMine(true);setInfo('Matrícula realizada com sucesso.');}catch(e){setError(e.message);}}
  async function updateCourse(values){const updated=await coursesApi.update(id,values,token);setCourse(updated);setShowEdit(false);setInfo('Curso atualizado.');}
  async function deleteCourse(){
    if(!window.confirm('Excluir definitivamente o curso e suas matrículas e aulas?'))return;
    try { await coursesApi.remove(id,token);navigate('/professor/cursos',{replace:true}); }
    catch(e){setError(e.message);}
  }
  async function togglePublished(){try{const updated=await coursesApi.update(id,{status:course.status==='draft'?'published':'draft'},token);setCourse(updated);setInfo(updated.status==='published'?'Curso publicado.':'Curso voltou a ser rascunho.');}catch(e){setError(e.message);}}
  async function saveLesson(values){
    const l=editingLesson?await coursesApi.updateLesson(id,editingLesson.id,values,token):await coursesApi.createLesson(id,values,token);
    setLessons(all=>editingLesson?all.map(v=>v.id===l.id?l:v):[...all,l]);setEditingLesson(null);setShowLessonForm(false);setInfo('Aula salva.');
  }
  async function deleteLesson(lessonId){if(!window.confirm('Excluir esta aula?'))return;try{await coursesApi.removeLesson(id,lessonId,token);setLessons(all=>all.filter(l=>l.id!==lessonId));}catch(e){setError(e.message);}}
  if(!user)return <Navigate to="/entrar" replace/>;
  if(loading)return <p className="loading">Carregando curso...</p>;
  if(!course)return <section className="study-page"><Alert>{error||'Curso não encontrado'}</Alert><Link to="/cursos">Voltar ao catálogo</Link></section>;
  return <section className="study-page"><Link className="small-link" to={isOwner?'/professor/cursos':'/cursos'}>← Voltar aos cursos</Link>
    <div className="course-heading"><div><span className="category-tag">{course.category}</span><h1>{course.title}</h1><p>{course.description}</p><span className="muted-text">{course.status==='published'?'Publicado':'Rascunho'}</span></div>
      {isOwner&&<div className="inline-actions"><button className="secondary-button" onClick={()=>setShowEdit(v=>!v)}>Editar curso</button><button className="primary-button" onClick={togglePublished}>{course.status==='published'?'Retirar publicação':'Publicar curso'}</button><button className="text-action danger" onClick={deleteCourse}>Excluir curso</button></div>}
      {isStudent&&!mine&&<button className="primary-button" onClick={doEnroll}>Matricular-me</button>}
    </div><Alert>{error}</Alert><Alert variant="success">{info}</Alert>
    {isOwner&&showEdit&&<section className="white-panel"><h2>Editar curso</h2><CourseForm key={course.id+course.updated_at} initial={course} onSubmit={updateCourse} submitLabel="Atualizar dados"/></section>}
    <section className="white-panel lessons-panel"><div className="heading-inline"><h2>Aulas do curso</h2>{isOwner&&<button className="primary-button" onClick={()=>{setEditingLesson(null);setShowLessonForm(v=>!v);}}>Adicionar aula</button>}</div>
      {(isOwner||mine)?<>
        {isOwner&&(showLessonForm||editingLesson)&&<LessonEditor key={editingLesson?.id||'new'} initial={editingLesson} onSubmit={saveLesson} cancel={()=>{setEditingLesson(null);setShowLessonForm(false);}}/>}
        {lessons.length?<div className="lessons-list">{[...lessons].sort((a,b)=>a.position-b.position).map(lesson=><article key={lesson.id} className="lesson-item">
          <div className="lesson-head"><div><span className="muted-text">Aula {lesson.position}</span><h3>{lesson.title}</h3></div>{isOwner&&<div className="inline-actions"><button className="text-action" onClick={()=>{setEditingLesson(lesson);setShowLessonForm(false);}}>Editar</button><button className="text-action danger" onClick={()=>deleteLesson(lesson.id)}>Excluir</button></div>}</div>
          <p className="lesson-body">{lesson.body}</p>{lesson.material_url&&<a className="small-link" href={lesson.material_url} target="_blank" rel="noopener noreferrer">Material complementar ↗</a>}
        </article>)}</div>:<div className="empty-state">Este curso ainda não possui aulas.</div>}
      </>:<div className="empty-state">{isStudent?'Matricule-se para acessar as aulas e os materiais do curso.':'Somente o professor responsável ou estudantes matriculados podem acessar as aulas.'}</div>}
    </section>
    {(isOwner||mine)&&<section className="white-panel"><h2>Avaliações deste curso</h2><p>Questionários de múltipla escolha e correção automática.</p><Link className="primary-button" to={`/cursos/${id}/avaliacoes`}>{isOwner?'Gerenciar avaliações':'Ver questionários'}</Link></section>}
  </section>;
}
