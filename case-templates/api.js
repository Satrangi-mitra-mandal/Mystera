/* ═══════════════════════════════════════════
   DetectiveOS — API Client
   Handles all fetch calls to the FastAPI backend
═══════════════════════════════════════════ */

// ── API Base URL ─────────────────────────────────────────────────────────────
// Automatically picks localhost in development, your live backend in production.
// IMPORTANT: Replace the production URL below with your actual Render/Railway URL.
const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ? 'http://localhost:8000'
  : 'https://YOUR-BACKEND-URL.onrender.com'; // ← REPLACE THIS with your backend URL

let _token = localStorage.getItem('dos_token');
let _user  = JSON.parse(localStorage.getItem('dos_user') || 'null');

/* ── Auth state ─────────────────────────── */
export const auth = {
  get token() { return _token; },
  get user()  { return _user; },
  get loggedIn() { return !!_token; },

  setSession(token, user) {
    _token = token;
    _user  = user;
    localStorage.setItem('dos_token', token);
    localStorage.setItem('dos_user', JSON.stringify(user));
    document.dispatchEvent(new CustomEvent('auth:change', { detail: { user } }));
  },

  clearSession() {
    _token = null;
    _user  = null;
    localStorage.removeItem('dos_token');
    localStorage.removeItem('dos_user');
    document.dispatchEvent(new CustomEvent('auth:change', { detail: null }));
  }
};

/* ── Core fetch wrapper ─────────────────── */
async function request(method, path, body = null, opts = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (_token) headers['Authorization'] = `Bearer ${_token}`;

  const config = { method, headers };
  if (body) config.body = JSON.stringify(body);

  const res = await fetch(`${API_BASE}${path}`, config);

  if (res.status === 401) {
    auth.clearSession();
    window.location.href = '/login.html';
    return;
  }

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.detail || `HTTP ${res.status}`);
  }

  return data;
}

/* ── API methods ────────────────────────── */
export const api = {
  // Auth
  async register(email, username, password, avatar) {
    const d = await request('POST', '/api/auth/register', { email, username, password, avatar });
    auth.setSession(d.access_token, d.user);
    return d;
  },

  async login(email, password) {
    const d = await request('POST', '/api/auth/login', { email, password });
    auth.setSession(d.access_token, d.user);
    return d;
  },

  async me() {
    return request('GET', '/api/auth/me');
  },

  logout() {
    auth.clearSession();
    window.location.href = '/index.html';
  },

  // Cases
  async getCases(filters = {}) {
    const params = new URLSearchParams(filters).toString();
    return request('GET', `/api/cases${params ? '?' + params : ''}`);
  },

  async getCase(slug) {
    return request('GET', `/api/cases/${slug}`);
  },

  async startCase(slug) {
    return request('POST', `/api/cases/${slug}/start`);
  },

  async getProgress(slug) {
    return request('GET', `/api/cases/${slug}/progress`);
  },

  async saveBoard(slug, boardState) {
    return request('PUT', `/api/cases/${slug}/board`, boardState);
  },

  // Interrogation
  async interrogate(suspectId, message, history = []) {
    return request('POST', `/api/interrogate/${suspectId}`, { message, history });
  },

  // Solutions
  async submitSolution(slug, solution) {
    return request('POST', `/api/cases/${slug}/solve`, solution);
  },

  async getSolution(slug) {
    return request('GET', `/api/cases/${slug}/solution`);
  },

  // Leaderboard
  async getGlobalLeaderboard() {
    return request('GET', '/api/leaderboard/global');
  },

  async getWeeklyLeaderboard() {
    return request('GET', '/api/leaderboard/weekly');
  },

  async getCaseLeaderboard(slug) {
    return request('GET', `/api/leaderboard/case/${slug}`);
  },
};

/* ── Toast notifications ────────────────── */
export function toast(message, type = 'info', duration = 3000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => el.remove(), duration);
}

/* ── Router (simple hash router) ───────── */
export function navigateTo(page, params = {}) {
  const query = new URLSearchParams(params).toString();
  window.location.href = `${page}${query ? '?' + query : ''}`;
}

export function getParam(key) {
  return new URLSearchParams(window.location.search).get(key);
}

/* ── Time formatter ─────────────────────── */
export function formatTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

export function timeSince(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}
