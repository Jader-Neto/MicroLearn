import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import Alert from '../components/Alert';
import { authApi } from '../services/apiClient';
import { useAuth } from '../context/AuthContext';
export default function Register() {
  const [values, setValues] = useState({ name:'', email:'', password:'', confirm:'' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const { user } = useAuth(); const navigate = useNavigate();
  if (user) return <Navigate to="/painel" replace />;
  async function submit(e) {
    e.preventDefault(); setError('');
    if (values.password !== values.confirm) return setError('As senhas não conferem.');
    setBusy(true);
    try { await authApi.register({ name:values.name, email:values.email, password:values.password }); navigate('/entrar', { state: { created:true } }); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }
  return <div className="auth-layout"><section className="auth-card"><span className="eyebrow">COMECE A APRENDER</span><h1>Crie sua conta.</h1><p>O cadastro público cria um perfil de aluno. Perfis de professor são definidos por um administrador.</p>
    <form onSubmit={submit}><label htmlFor="name">Nome completo</label><input id="name" type="text" required minLength={2} maxLength={100} autoComplete="name" value={values.name} onChange={e=>setValues({...values,name:e.target.value})}/>
    <label htmlFor="email">E-mail</label><input id="email" type="email" required autoComplete="email" value={values.email} onChange={e=>setValues({...values,email:e.target.value})}/>
    <label htmlFor="pass">Senha (mínimo 8 caracteres)</label><input id="pass" type="password" required minLength={8} autoComplete="new-password" value={values.password} onChange={e=>setValues({...values,password:e.target.value})}/>
    <label htmlFor="confirm">Confirme a senha</label><input id="confirm" type="password" required minLength={8} autoComplete="new-password" value={values.confirm} onChange={e=>setValues({...values,confirm:e.target.value})}/><Alert>{error}</Alert>
    <button type="submit" disabled={busy} className="primary-button stretch">{busy?'Criando conta...':'Criar conta de aluno'}</button></form><p className="auth-footer">Já possui conta? <Link to="/entrar">Entrar</Link></p></section></div>;
}
