import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <p className="loading" role="status">Verificando sessão...</p>;
  if (!user) return <Navigate to="/entrar" replace />;
  return children;
}
