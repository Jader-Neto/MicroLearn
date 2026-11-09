import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import AppShell from './components/AppShell';
import ProtectedRoute from './components/ProtectedRoute';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import CoursesCatalog from './pages/CoursesCatalog';
import TeacherCourses from './pages/TeacherCourses';
import MyEnrollments from './pages/MyEnrollments';
import CourseDetail from './pages/CourseDetail';
import CourseAssessments from './pages/CourseAssessments';
import QuizDetail from './pages/QuizDetail';
import StudentPerformance from './pages/StudentPerformance';
import UserManagement from './pages/UserManagement';

export default function App() {
  return <BrowserRouter><AuthProvider><AppShell><Routes>
    <Route path="/" element={<Home/>}/>
    <Route path="/entrar" element={<Login/>}/>
    <Route path="/cadastro" element={<Register/>}/>
    <Route path="/painel" element={<ProtectedRoute><Dashboard/></ProtectedRoute>}/>
    <Route path="/cursos" element={<CoursesCatalog/>}/>
    <Route path="/cursos/:id" element={<ProtectedRoute><CourseDetail/></ProtectedRoute>}/>
    <Route path="/professor/cursos" element={<ProtectedRoute><TeacherCourses/></ProtectedRoute>}/>
    <Route path="/cursos/:id/avaliacoes" element={<ProtectedRoute><CourseAssessments/></ProtectedRoute>}/>
    <Route path="/avaliacoes/:quizId" element={<ProtectedRoute><QuizDetail/></ProtectedRoute>}/>
    <Route path="/desempenho" element={<ProtectedRoute><StudentPerformance/></ProtectedRoute>}/>
    <Route path="/admin/usuarios" element={<ProtectedRoute><UserManagement/></ProtectedRoute>}/>
    <Route path="/meus-cursos" element={<ProtectedRoute><MyEnrollments/></ProtectedRoute>}/>
    <Route path="*" element={<Navigate to="/" replace/>}/>
  </Routes></AppShell></AuthProvider></BrowserRouter>;
}
