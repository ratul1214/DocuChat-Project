// src/services/api.ts
const API_URL = import.meta.env.VITE_API_URL || `${window.location.origin}/api`;

// ---- helpers ----
export function authHeader() {
  const t = localStorage.getItem('token');
  return t ? { Authorization: `Bearer ${t}` } : {};
}
export function tenantHeader() {
  const k = localStorage.getItem('tenant') || 'default';
  return { 'X-Tenant': k };
}
function getTenant() {
  return localStorage.getItem('tenant') || 'default';
}
function getSub() {
  // prefer server-provided sub; fall back to a mock/dev value
  return localStorage.getItem('sub') || 'mock-user';
}

// ---- auth ----
export async function loginPassword(username: string, password: string, tenant = 'default') {
  const r = await fetch(`${API_URL}/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Tenant': tenant },
    body: JSON.stringify({ username, password, tenant }),
  });
  if (!r.ok) throw new Error((await r.text()) || 'Login failed');
  const j = await r.json(); // expect { token, tenant, sub }
  if (j.token) localStorage.setItem('token', j.token);
  localStorage.setItem('tenant', j.tenant || tenant);
  if (j.sub || username) localStorage.setItem('sub', j.sub || username);
  return j;
}
export function logout() {
  localStorage.removeItem('token');
  // Keep tenant so the user stays in same org; clear sub if you want:
  // localStorage.removeItem('tenant');
  // localStorage.removeItem('sub');
}

// ---- REST calls ----
export async function getMe() {
  const r = await fetch(`${API_URL}/me`, { headers: { ...authHeader(), ...tenantHeader() } });
  if (!r.ok) throw new Error('Failed /me');
  return r.json();
}
export async function listDocuments() {
  const r = await fetch(`${API_URL}/documents`, { headers: { ...authHeader(), ...tenantHeader() } });
  if (!r.ok) throw new Error('Failed /documents');
  return r.json();
}
export async function uploadFiles(files: File[]) {
  const form = new FormData();
  files.forEach(f => form.append('files', f));
  const r = await fetch(`${API_URL}/upload`, {
    method: 'POST',
    headers: { ...authHeader(), ...tenantHeader() }, // do NOT set Content-Type manually
    body: form,
  });
  if (!r.ok) throw new Error((await r.text()) || `Failed upload (${r.status})`);
  return r.json();
}
export async function ask(question: string, top_k = 5) {
  const r = await fetch(`${API_URL}/chat/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeader(), ...tenantHeader() },
    body: JSON.stringify({ query: question, top_k }),
  });
  if (!r.ok) {
    let msg = 'Failed ask';
    try { const j = await r.json(); if (j?.detail) msg = j.detail; } catch {}
    throw new Error(msg);
  }
  return r.json();
}

// ---- Agent workflow ----
export async function startAgentReport(topic: string, top_k = 6) {
  const r = await fetch(`${API_URL}/agent/report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeader(), ...tenantHeader() },
    body: JSON.stringify({ topic, top_k }),
  });
  if (!r.ok) throw new Error(`Failed to start agent (${r.status})`);
  return r.json() as Promise<{ report_id: number }>;
}
export async function listReports() {
  const r = await fetch(`${API_URL}/reports`, { headers: { ...authHeader(), ...tenantHeader() } });
  if (!r.ok) throw new Error(`Failed to list reports (${r.status})`);
  return r.json() as Promise<Array<{ id: number; title: string; created_at: string }>>;
}
export async function getReport(id: number) {
  const r = await fetch(`${API_URL}/reports/${id}`, { headers: { ...authHeader(), ...tenantHeader() } });
  if (!r.ok) throw new Error(`Failed to get report (${r.status})`);
  return r.json() as Promise<{ id: number; title: string; content: string; created_at: string }>;
}

// ---- WebSockets ----
// progress.{tenant}.{sub}
export function connectProgressWS(onMessage: (msg: any) => void) {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const tenant = getTenant();
  const sub = getSub();
  const url = `${proto}://${location.host}/ws/progress?tenant=${encodeURIComponent(tenant)}&sub=${encodeURIComponent(sub)}`;
  const ws = new WebSocket(url);
  ws.onmessage = (e) => { try { onMessage(JSON.parse(e.data)); } catch {} };
  return ws;
}
// agent.{tenant}.{report_id}
export function connectAgentWS(reportId: number, onMessage: (msg: any) => void) {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const tenant = getTenant();
  const url = `${proto}://${location.host}/ws/agent?tenant=${encodeURIComponent(tenant)}&report_id=${encodeURIComponent(String(reportId))}`;
  const ws = new WebSocket(url);
  ws.onmessage = (e) => { try { onMessage(JSON.parse(e.data)); } catch {} };
  return ws;
}
