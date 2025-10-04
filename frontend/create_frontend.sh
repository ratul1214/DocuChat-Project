set -euo pipefail


# Basic Vite structure (manual)
mkdir -p public src/pages src/components src/services src/styles

# package.json
cat > package.json <<'EOF'
{
  "name": "docuchat-frontend",
  "private": true,
  "version": "0.0.1",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview --port 5173 --strictPort"
  },
  "dependencies": {
    "antd": "^5.19.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.10",
    "typescript": "^5.5.4",
    "vite": "^5.4.2"
  }
}
EOF

# index.html
cat > index.html <<'EOF'
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>DocuChat</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
EOF

# tsconfig.json
cat > tsconfig.json <<'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "jsx": "react-jsx",
    "moduleResolution": "Bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "strict": true
  },
  "include": ["src"]
}
EOF

# vite.config.ts
cat > vite.config.ts <<'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true
  }
})
EOF

# Tailwind setup
cat > postcss.config.js <<'EOF'
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
EOF

cat > tailwind.config.js <<'EOF'
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {},
  },
  plugins: [],
}
EOF

# styles
cat > src/styles/index.css <<'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

html, body, #root { height: 100%; }
body { @apply bg-gray-50; }
EOF

# env samples
cat > .env.sample <<'EOF'
VITE_API_URL=http://localhost/api
VITE_WS_URL=ws://localhost/ws/progress
VITE_OIDC_MOCK_SUB=mock-user
EOF

# main.tsx
cat > src/main.tsx <<'EOF'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './pages/App'
import './styles/index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
EOF

# services/api.ts
cat > src/services/api.ts <<'EOF'
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost/api';

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
  files.forEach(f => form.append('files', f));
  const r = await fetch(`${API_URL}/upload`, {
    method: 'POST',
    headers: { ...authHeader() },
    body: form
  });
  if (!r.ok) throw new Error('Failed upload');
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
EOF

# components/ProgressStream.tsx
cat > src/components/ProgressStream.tsx <<'EOF'
import { useEffect, useState } from 'react';

export default function ProgressStream() {
  const [events, setEvents] = useState<any[]>([]);

  useEffect(() => {
    const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost/ws/progress';
    const sub = import.meta.env.VITE_OIDC_MOCK_SUB || 'mock-user';
    const ws = new WebSocket(`${WS_URL}?sub=${encodeURIComponent(sub)}`);
    ws.onmessage = (ev) => {
      const data = JSON.parse(ev.data);
      setEvents(prev => [data, ...prev].slice(0, 50));
    };
    return () => ws.close();
  }, []);

  return (
    <div className="space-y-2">
      {events.map((e, i) => (
        <div key={i} className="text-sm p-2 rounded border bg-white">
          <div className="font-medium">{e.stage}</div>
          <div className="text-gray-600">{e.filename} {e.chunks ? `(chunks: ${e.chunks})` : ''}</div>
        </div>
      ))}
      {events.length === 0 && <div className="text-gray-500">No progress yet. Upload something!</div>}
    </div>
  );
}
EOF

# pages/App.tsx (router-less minimal UI)
cat > src/pages/App.tsx <<'EOF'
import { useEffect, useState } from 'react'
import { Button, Input, Upload, Typography, message, Divider, List, Card } from 'antd'
import { UploadOutlined } from '@ant-design/icons'
import { getMe, listDocuments, uploadFiles, ask } from '../services/api'
import ProgressStream from '../components/ProgressStream'

const { Title } = Typography

export default function App() {
  const [token, setToken] = useState<string>(() => localStorage.getItem('token') || '')
  const [me, setMe] = useState<any>(null)
  const [docs, setDocs] = useState<any[]>([])
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<string>('')
  const [citations, setCitations] = useState<any[]>([])

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token)
      refresh()
    }
  }, [token])

  async function refresh() {
    try {
      const m = await getMe();
      setMe(m)
      const d = await listDocuments();
      setDocs(d)
    } catch (e:any) {
      message.error(e.message)
    }
  }

  async function handleUpload(fileList: File[]) {
    try {
      await uploadFiles(fileList)
      message.success('Files queued for indexing')
      setTimeout(refresh, 800)
    } catch (e:any) {
      message.error(e.message)
    }
  }

  async function handleAsk() {
    setAnswer('')
    setCitations([])
    try {
      const r = await ask(question)
      setAnswer(r.answer)
      setCitations(r.citations || [])
    } catch (e:any) {
      message.error(e.message)
    }
  }

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8">
      <header className="flex items-center justify-between">
        <Title level={3} className="!mb-0">DocuChat</Title>
        <div className="flex items-center gap-2">
          <Input.Password
            placeholder="Paste Bearer token (or type anything in mock mode)"
            value={token}
            onChange={e => setToken(e.target.value)}
            className="w-80"
          />
          <Button onClick={refresh}>Use Token</Button>
        </div>
      </header>

      <section className="grid md:grid-cols-2 gap-6">
        <Card title="Uploads & Progress" className="shadow">
          <Upload.Dragger
            multiple
            beforeUpload={() => false}
            customRequest={({ file, onSuccess, onError }) => {
              const f = file as File
              handleUpload([f]).then(() => onSuccess && onSuccess({}, f)).catch(onError as any)
            }}
          >
            <p className="ant-upload-drag-icon"><UploadOutlined /></p>
            <p className="ant-upload-text">Click or drag files to upload</p>
            <p className="ant-upload-hint">PDF, Markdown, Text</p>
          </Upload.Dragger>
          <Divider />
          <ProgressStream />
          <Divider />
          <List
            header={<div className="font-medium">Your Documents</div>}
            dataSource={docs}
            renderItem={(d:any) => (
              <List.Item>
                <div className="flex justify-between w-full">
                  <span>{d.filename}</span>
                  <span className="text-gray-500 text-sm">{new Date(d.created_at).toLocaleString()}</span>
                </div>
              </List.Item>
            )}
          />
        </Card>

        <Card title="Chat" className="shadow">
          <div className="space-y-3">
            <Input.TextArea rows={3} value={question} onChange={e=>setQuestion(e.target.value)} placeholder="Ask a question about your docs" />
            <Button type="primary" onClick={handleAsk}>Ask</Button>
            {answer && (
              <div className="p-3 rounded bg-white border">
                <div className="whitespace-pre-wrap">{answer}</div>
                {citations.length>0 && (
                  <div className="text-sm text-gray-600 mt-2">
                    <div className="font-medium mb-1">Citations</div>
                    <ul className="list-disc ml-5">
                      {citations.map((c:any) => (
                        <li key={c.index}>[Doc {c.index}] {c.filename} (score {c.score})</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </Card>
      </section>

      <footer className="text-xs text-gray-500">MVP — login uses bearer token. In Step 2, wire real Keycloak OIDC.</footer>
    </div>
  )
}
EOF

# Done
