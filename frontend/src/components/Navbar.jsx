import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
export default function Navbar() {
  const { user, logout } = useAuth();
  return <header className="topbar">
    <Link className="brand" to="/"><span className="brand-mark">M</span> MicroLearn</Link>
    <nav className="nav-links" aria-label="Navegação principal">
      <Link to="/">Início</Link><Link to="/cursos">Cursos</Link>
      {user ? <><Link to="/painel">Meu painel</Link>{user.role === 'manager' && <Link to="/admin/usuarios">Gerenciar usuários</Link>}{user.role === 'teacher' && <Link to="/professor/cursos">Gerenciar cursos</Link>}{user.role === 'student' && <><Link to="/meus-cursos">Meus cursos</Link><Link to="/desempenho">Desempenho</Link></>}<button className="text-button" onClick={logout}>Sair</button></> : <><Link to="/entrar">Entrar</Link><Link className="nav-primary" to="/cadastro">Criar conta</Link></>}
    </nav>
  </header>;
}
