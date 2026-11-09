import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../services/apiClient';
import Alert from '../components/Alert';

const roleNames = { student: 'Aluno', teacher: 'Professor', manager: 'Administrador' };

export default function UserManagement() {
  const { user, token } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (user?.role !== 'manager') { setLoading(false); return; }
    let alive = true;
    authApi.users(token)
      .then(data => { if (alive) setUsers(data); })
      .catch(err => { if (alive) setError(err.message); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [token, user?.role]);

  if (user?.role !== 'manager') return <Navigate to="/painel" replace />;

  async function updateAccount(account, changes) {
    if (account.id === user.id && (changes.active === false || (changes.role && changes.role !== 'manager'))) {
      setError('Você não pode desativar ou rebaixar seu próprio usuário administrador.');
      return;
    }
    if (!window.confirm(`Confirmar alteração na conta ${account.email}?`)) return;
    setError(''); setSuccess(''); setWorking(account.id);
    try {
      const updated = await authApi.updateUser(account.id, changes, token);
      setUsers(current => current.map(item => item.id === account.id ? updated : item));
      setSuccess(`Conta ${updated.email} atualizada.`);
    } catch (err) { setError(err.message); }
    finally { setWorking(null); }
  }

  return <section className="study-page">
    <span className="eyebrow">ADMINISTRAÇÃO DA PLATAFORMA</span>
    <h1>Gerenciamento de usuários</h1>
    <p>Autorize professores, altere perfis e ative ou desative contas. As modificações são aplicadas pelo microsserviço de Autenticação.</p>
    <Alert>{error}</Alert><Alert variant="success">{success}</Alert>
    <section className="white-panel">
      <h2>Contas cadastradas</h2>
      {loading ? <p role="status">Consultando contas...</p> : users.length ?
        <div className="results-table-wrapper"><table className="results-table">
          <thead><tr><th>Usuário</th><th>Perfil</th><th>Situação</th><th>Alteração de perfil</th><th>Conta</th></tr></thead>
          <tbody>{users.map(account => <tr key={account.id}>
            <td><strong>{account.name}</strong><div className="muted-text">{account.email}</div></td>
            <td>{roleNames[account.role] || account.role}</td>
            <td>{account.active ? 'Ativa' : 'Desativada'}</td>
            <td><label className="sr-only" htmlFor={`role-${account.id}`}>Perfil de {account.name}</label>
              <select id={`role-${account.id}`} className="admin-select"
                value={account.role} disabled={working === account.id || account.id === user.id}
                onChange={event => updateAccount(account, { role: event.target.value })}>
                <option value="student">Aluno</option><option value="teacher">Professor</option><option value="manager">Administrador</option>
              </select></td>
            <td><button type="button" className="secondary-button admin-action"
              disabled={working === account.id || account.id === user.id}
              onClick={() => updateAccount(account, { active: !account.active })}>
              {working === account.id ? 'Atualizando...' : account.active ? 'Desativar' : 'Reativar'}
            </button></td>
          </tr>)}</tbody>
        </table></div> : <p>Nenhum usuário encontrado.</p>}
      <p className="hint-text">A conta do administrador atual não pode ser desativada ou rebaixada nesta interface.</p>
    </section>
  </section>;
}
