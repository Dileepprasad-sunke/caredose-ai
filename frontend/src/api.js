/**
 * CareDose AI — Frontend API Service (frontend/src/api.js)
 * Connects the React UI to the FastAPI + SQLite backend.
 */

const API_BASE = 'https://caredose-ai-1.onrender.com/api';

export function getToken() {
  return localStorage.getItem('caredose_token') || '';
}

export function setToken(token) {
  if (token) {
    localStorage.setItem('caredose_token', token);
  } else {
    localStorage.removeItem('caredose_token');
  }
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || data.message || 'An unexpected error occurred.');
  }
  return data;
}

export const api = {
  // Authentication
  login: (email, password) =>
    request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  signup: (name, email, password) =>
    request('/auth/signup', { method: 'POST', body: JSON.stringify({ name, email, password }) }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  getMe: () => request('/auth/me'),
  resetDemo: () => request('/auth/demo-reset', { method: 'POST' }),

  // Dashboard
  getDashboard: () => request('/dashboard'),

  // Medications CRUD + Status
  getMedications: () => request('/medications'),
  getMedicationDetail: (id) => request(`/medications/${id}`),
  createMedication: (payload) =>
    request('/medications', { method: 'POST', body: JSON.stringify(payload) }),
  updateMedication: (id, payload) =>
    request(`/medications/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteMedication: (id) => request(`/medications/${id}`, { method: 'DELETE' }),
  markStatus: (id, status, scheduled_date = null) =>
    request(`/medications/${id}/status`, {
      method: 'POST',
      body: JSON.stringify({ status, scheduled_date }),
    }),

  // Analytics & Reminders
  getAnalytics: () => request('/analytics'),
  getDueReminders: () => request('/reminders/due'),

  // Agentic AI & AI Assistant
  getAIState: () => request('/ai/state'),
  submitFollowUpResponse: (medication_id, response_choice, scheduled_date = null) =>
    request('/ai/followup-response', {
      method: 'POST',
      body: JSON.stringify({ medication_id, response_choice, scheduled_date }),
    }),
  sendAssistantChat: (message) =>
    request('/ai/chat', { method: 'POST', body: JSON.stringify({ message }) }),
  simulateMissedDose: () => request('/ai/simulate-missed', { method: 'POST' }),

  // Trusted Caregiver
  getCaregiver: () => request('/caregiver'),
  saveCaregiver: (payload) =>
    request('/caregiver', { method: 'PUT', body: JSON.stringify(payload) }),
  deleteCaregiver: () => request('/caregiver', { method: 'DELETE' }),
  simulateCaregiverAlert: () => request('/caregiver/simulate-alert', { method: 'POST' }),

  // Settings
  getSettings: () => request('/settings'),
  updateSettings: (payload) =>
    request('/settings', { method: 'PUT', body: JSON.stringify(payload) }),
};
