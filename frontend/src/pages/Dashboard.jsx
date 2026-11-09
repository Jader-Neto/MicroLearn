import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
const labels = {student:'Aluno',teacher:'Professor',manager:'Administrador'};
export default function Dashboard() {
  const { user } = useAuth();
  return <div className="dashboard"><span className="eyebrow">PAINEL DO USUÁRIO</span><h1>Olá, {user.name.split(' ')[0]}.</h1><p>Acesse os módulos de aprendizagem disponíveis.</p>
    <div className="profile-card"><div className="avatar">{user.name[0].toUpperCase()}</div><div><h2>{user.name}</h2><p>{user.email}</p><span className="role-pill">{labels[user.role] || user.role}</span></div></div>
    {user.role==='manager'&&<section className="white-panel"><h2>Administração</h2><p>Gerencie contas, autorize novos professores e controle o acesso à plataforma.</p><Link className="small-link" to="/admin/usuarios">Abrir gerenciamento de usuários →</Link></section>}
    <h2 className="section-title">Módulos do AVA</h2><div className="feature-grid"><div className="feature"><h3>Cursos e aulas</h3><p>{user.role==='teacher'?'Crie cursos, gerencie aulas e publique materiais.':user.role==='student'?'Explore cursos, matricule-se e acompanhe suas aulas.':'Consulte os cursos publicados na plataforma.'}</p><Link className="small-link" to={user.role==='teacher'?'/professor/cursos':user.role==='student'?'/meus-cursos':'/cursos'}>{user.role==='teacher'?'Gerenciar cursos':user.role==='student'?'Minhas matrículas':'Ver catálogo'} →</Link></div><div className="feature"><h3>Minhas avaliações</h3><p>Realize questionários e consulte os resultados das suas atividades.</p><Link className="small-link" to={user.role==='teacher'?'/professor/cursos':user.role==='student'?'/desempenho':'/cursos'}>Acessar avaliações →</Link></div><div className="feature"><h3>Para você</h3><p>Recomendações de aulas para estudar quando a nota for inferior a 7,0.</p>{user.role==='student'&&<Link className="small-link" to="/desempenho">Consultar recomendações →</Link>}</div></div>
  </div>;
}
