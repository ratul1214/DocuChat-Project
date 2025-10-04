const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export function authHeader() {
  const t = localStorage.getItem('token');
  return t ? { Authorization: `Bearer ${t}` } : {};
}

export async function getMe() {
  const r = await fetch(`${API_URL}/me`, { headers: { ...authHeader() } });
  if (!r.ok) throw new Error('Failed /me');
  return r.json();
}

export async function listDocuments() {
  const r = await fetch(`${API_URL}/documents`, { headers: { ...authHeader() } });
  if (!r.ok) throw new Error('Failed /documents');
  return r.json();
}

export async function uploadFiles(files: File[]) {
  const form = new FormData();
  files.forEach(f => form.append("files", f));

  const r = await fetch(`${API_URL}/upload`, {
    method: "POST",
    headers: {
      ...authHeader(), // only Authorization
      // ❌ do NOT add Content-Type manually
    },
    body: form,
  });

  if (!r.ok) {
    const text = await r.text();
    throw new Error(text || `Failed upload (${r.status})`);
  }
  return r.json();
}

export async function ask(question: string, top_k = 5) {
  const r = await fetch(`${API_URL}/chat/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify({ question, top_k })
  });
  if (!r.ok) throw new Error('Failed ask');
  return r.json();
}
