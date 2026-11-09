import { createContext, useContext, useEffect, useState } from 'react';
import { authApi } from '../services/apiClient';

const AuthContext = createContext(null);
export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => sessionStorage.getItem('microlearn_token'));
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(token));

  useEffect(() => {
    let active = true;
    if (!token) { setUser(null); setLoading(false); return; }
    setLoading(true);
    authApi.me(token)
      .then((profile) => { if (active) setUser(profile); })
      .catch(() => { if (active) { sessionStorage.removeItem('microlearn_token'); setToken(null); setUser(null); } })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [token]);

  async function login(email, password) {
    const result = await authApi.login({ email, password });
    const profile = await authApi.me(result.access_token);
    sessionStorage.setItem('microlearn_token', result.access_token);
    setToken(result.access_token);
    setUser(profile);
  }
  function logout() {
    sessionStorage.removeItem('microlearn_token');
    setToken(null);
    setUser(null);
  }
  return <AuthContext.Provider value={{ token, user, loading, login, logout }}>{children}</AuthContext.Provider>;
}
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth precisa estar dentro de AuthProvider');
  return context;
}
