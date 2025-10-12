// src/pages/LoginPage.tsx (simplified)
import { useState } from 'react';
import { Input, Button, message, Select } from 'antd';
import { loginPassword } from '../services/api';
import { useNavigate } from 'react-router-dom';

export default function LoginPage() {
  const [username, setU] = useState('');
  const [password, setP] = useState('');
  const [tenant, setT] = useState(localStorage.getItem('tenant') || 'default');
  const nav = useNavigate();

  async function submit() {
    try {
      await loginPassword(username, password, tenant);
      message.success('Logged in');
      nav('/upload');
    } catch (e:any) {
      message.error(e.message);
    }
  }

  return (
    <div className="max-w-md mx-auto p-6 space-y-4">
      <Select value={tenant} onChange={v=>{setT(v); localStorage.setItem('tenant', v)}} options={[{value:'default',label:'default'},{value:'acme',label:'acme'}]} />
      <Input placeholder="Username" value={username} onChange={e=>setU(e.target.value)} />
      <Input.Password placeholder="Password" value={password} onChange={e=>setP(e.target.value)} />
      <Button type="primary" onClick={submit}>Login</Button>
    </div>
  );
}
