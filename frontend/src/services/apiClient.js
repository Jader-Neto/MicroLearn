// Toda a comunicação do navegador passa pela API Gateway.
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
export async function apiRequest(path, { token, ...options } = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    });
  } catch {
    throw new Error('Não foi possível conectar à API Gateway. Verifique os serviços.');
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data?.detail;
    const message = typeof detail === 'string' ? detail : 'Erro ao processar a solicitação';
    throw new Error(message);
  }
  return data;
}
export const authApi = {
  login: (credentials) => apiRequest('/auth/login', { method: 'POST', body: JSON.stringify(credentials) }),
  register: (values) => apiRequest('/auth/register', { method: 'POST', body: JSON.stringify(values) }),
  me: (token) => apiRequest('/auth/me', { token }),
  users: (token) => apiRequest('/auth/users', { token }),
  updateUser: (id, changes, token) => apiRequest(`/auth/users/${encodeURIComponent(id)}`, { method: 'PATCH', token, body: JSON.stringify(changes) }),
};
export async function getSystemStatus() {
  try { return await apiRequest('/status'); }
  catch { return null; }
}

// Contrato REST do microsserviço Cursos (Sprint 2).
export const coursesApi = {
  catalog: () => apiRequest('/courses'),
  owned: (token) => apiRequest('/courses/owned', { token }),
  enrolled: (token) => apiRequest('/courses/enrollments/mine', { token }),
  detail: (id, token) => apiRequest(`/courses/${encodeURIComponent(id)}`, { token }),
  create: (values, token) => apiRequest('/courses', { method:'POST', token, body:JSON.stringify(values) }),
  update: (id, values, token) => apiRequest(`/courses/${encodeURIComponent(id)}`, { method:'PATCH', token, body:JSON.stringify(values) }),
  remove: (id, token) => apiRequest(`/courses/${encodeURIComponent(id)}`, { method:'DELETE', token }),
  enroll: (id, token) => apiRequest(`/courses/${encodeURIComponent(id)}/enrollments`, { method:'POST', token }),
  lessons: (id, token) => apiRequest(`/courses/${encodeURIComponent(id)}/lessons`, { token }),
  createLesson: (id, values, token) => apiRequest(`/courses/${encodeURIComponent(id)}/lessons`, { method:'POST', token, body:JSON.stringify(values) }),
  updateLesson: (id, lessonId, values, token) => apiRequest(`/courses/${encodeURIComponent(id)}/lessons/${encodeURIComponent(lessonId)}`, { method:'PATCH', token, body:JSON.stringify(values) }),
  removeLesson: (id, lessonId, token) => apiRequest(`/courses/${encodeURIComponent(id)}/lessons/${encodeURIComponent(lessonId)}`, { method:'DELETE', token }),
};

// Sprint 3: questionários e recomendações por APIs independentes.
export const assessmentsApi = {
  byCourse: (courseId, token) => apiRequest(`/assessments/courses/${encodeURIComponent(courseId)}/quizzes`, { token }),
  create: (courseId, data, token) => apiRequest(`/assessments/courses/${encodeURIComponent(courseId)}/quizzes`, { method: 'POST', token, body: JSON.stringify(data) }),
  detail: (quizId, token) => apiRequest(`/assessments/quizzes/${encodeURIComponent(quizId)}`, { token }),
  submit: (quizId, answers, token) => apiRequest(`/assessments/quizzes/${encodeURIComponent(quizId)}/submit`, { method: 'POST', token, body: JSON.stringify({ answers }) }),
  remove: (quizId, token) => apiRequest(`/assessments/quizzes/${encodeURIComponent(quizId)}`, { method: 'DELETE', token }),
  mine: (token) => apiRequest('/assessments/results/mine', { token }),
  courseResults: (courseId, token) => apiRequest(`/assessments/courses/${encodeURIComponent(courseId)}/results`, { token }),
};
export const recommendationsApi = {
  mine: (token) => apiRequest('/recommendations/mine', { token }),
};
