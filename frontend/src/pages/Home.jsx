import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getSystemStatus } from '../services/apiClient';
import { useAuth } from '../context/AuthContext';

export default function Home() {
  const [status, setStatus] = useState(null);
  const [checking, setChecking] = useState(true);
  const { user } = useAuth();
  async function refreshStatus() {
    setChecking(true);
    try { setStatus(await getSystemStatus()); }
    finally { setChecking(false); }
  }
  useEffect(() => { refreshStatus(); }, []);
  const services = status?.services || [];
  return <div className="home">
    <section className="hero">
      <div><span className="eyebrow">EDUCAÇÃO DIGITAL • PROJETO ACADÊMICO</span>
      <h1>Aprender, ensinar e evoluir em um só lugar.</h1>
      <p>Um Ambiente Virtual de Aprendizagem desenvolvido com microsserviços independentes e componentes de software reutilizáveis.</p>
      <div className="hero-actions">{user ? <Link className="primary-button" to="/painel">Acessar meu painel</Link> : <><Link className="primary-button" to="/cadastro">Começar agora</Link><Link className="secondary-button" to="/entrar">Já tenho conta</Link></>}</div>
      </div>
      <div className="illustration" aria-hidden="true"><span className="glow-one"></span><div className="illustration-card"><span className="illustration-icon">ML</span><span className="illustration-title">Seu espaço de aprendizado</span><div className="fake-progress"><span></span></div><div className="fake-lines"><i></i><i></i><i></i></div></div></div>
    </section>
    <section className="features"><h2>Módulos da plataforma</h2><div className="feature-grid">
      <article className="feature"><span className="feature-symbol">01</span><h3>Cursos e aulas</h3><p>Catálogo, matrículas e materiais em um espaço organizado.</p><Link className="small-link" to="/cursos">Explorar cursos →</Link></article>
      <article className="feature"><span className="feature-symbol">02</span><h3>Avaliações</h3><p>Questionários objetivos, correção automática e notas.</p><span className="coming-soon">Disponível</span></article>
      <article className="feature"><span className="feature-symbol">03</span><h3>Recomendações</h3><p>Sugestões de revisão de acordo com o desempenho.</p><span className="coming-soon">Disponível</span></article>
    </div></section>
    <section className="status-section"><div><h2>Estado dos microsserviços</h2><p>Consulta real à API Gateway. Cada indicador representa um serviço independente.</p><button type="button" className="secondary-button" disabled={checking} onClick={refreshStatus}>{checking ? "Verificando..." : "Atualizar estado"}</button></div><div className="status-grid">{services.length ? services.map(item => <div className="status-card" key={item.service}><span className={item.ok ? 'status-dot online' : 'status-dot'}></span><span>{item.service}</span><strong>{item.ok ? 'Online' : 'Indisponível'}</strong></div>) : <p>{checking ? "Consultando serviços..." : "Não foi possível consultar o estado dos serviços."}</p>}</div></section>
  </div>;
}
