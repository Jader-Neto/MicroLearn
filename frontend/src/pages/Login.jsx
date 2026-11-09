import { useState } from 'react';
import { Link, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Alert from '../components/Alert';
export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  if (user) return <Navigate to="/painel" replace />;
  async function submit(event) {
    event.preventDefault(); setError(''); setSubmitting(true);
    try { await login(email, password); navigate('/painel', { replace: true }); }
    catch (err) { setError(err.message); }
    finally { setSubmitting(false); }
  }
  return <div className="auth-layout"><section className="auth-card"><span className="eyebrow">ÁREA DE ACESSO</span><h1>Boas-vindas de volta.</h1><p>Entre com sua conta MicroLearn.</p>
    <Alert variant="success">{location.state?.created ? "Conta criada. Entre com suas credenciais." : ""}</Alert>
    <form onSubmit={submit}><label htmlFor="email">E-mail</label><input id="email" required type="email" autoComplete="email" placeholder="seu@email.com" value={email} onChange={e=>setEmail(e.target.value)}/>
    <label htmlFor="password">Senha</label><input id="password" required type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)}/><Alert>{error}</Alert>
    <button className="primary-button stretch" disabled={submitting} type="submit">{submitting ? 'Entrando...' : 'Entrar'}</button></form><p className="auth-footer">Não tem conta? <Link to="/cadastro">Cadastre-se</Link></p></section></div>;
}
