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
  showUploadList={false}
  beforeUpload={(file) => {
    // call your uploader yourself
    handleUpload([file as File]);
    return false; // prevent AntD from trying to upload
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
