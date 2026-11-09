import { Link } from 'react-router-dom';
export default function CourseCard({ course, label }) {
  return <article className="course-card">
    <span className="category-tag">{course.category}</span>
    <h3>{course.title}</h3>
    <p>{course.description}</p>
    <div className="course-bottom">
      <span className="muted-text">{course.lesson_count !== undefined ? `${course.lesson_count} aula(s)` : course.status === 'draft' ? 'Rascunho' : 'Publicado'}</span>
      <Link className="small-link" to={`/cursos/${course.id}`}>{label || 'Ver detalhes'} →</Link>
    </div>
  </article>;
}
