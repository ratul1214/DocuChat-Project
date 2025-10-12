import { BrowserRouter, Routes, Route, Navigate, Link } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import UploadPage from "./pages/UploadPage";
import ChatPage from "./pages/ChatPage";
import AgentPage from "./pages/AgentPage";
// in a header component or App shell
import { Button, Select } from 'antd';
import { logout } from './services/api';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';

function HeaderBar() {
  const nav = useNavigate();
  const [tenant, setTenant] = useState(localStorage.getItem('tenant') || 'default');

  function doLogout() {
    logout();
    nav('/login');
  }

  function changeTenant(v: string) {
    localStorage.setItem('tenant', v);
    setTenant(v);
    window.location.reload(); // simplest to refresh data per-tenant
  }

  return (
    <div className="flex gap-2 items-center">
      <Select
        value={tenant}
        style={{ width: 160 }}
        onChange={changeTenant}
        options={[
          { value: 'default', label: 'default' },
          // add more tenant keys here while testing
          { value: 'acme', label: 'acme' },
        ]}
      />
      <Button onClick={doLogout}>Logout</Button>
    </div>
  );
}



function Protected({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem("token");
  return token ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function AppRouter() {
  return (
    <BrowserRouter>
        <HeaderBar></HeaderBar>
      <header style={{ padding: 12, borderBottom: "1px solid #eee" }}>
        <nav style={{ display: "flex", gap: 12 }}>
          <Link to="/upload">Upload</Link>
          <Link to="/chat">Chat</Link>
          <span style={{ marginLeft: "auto", opacity: 0.6 }}>DocuChat</span>
        </nav>
      </header>

      <Routes>
          <Route path="/agent" element={<AgentPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/upload" element={<Protected><UploadPage /></Protected>} />
        <Route path="/chat" element={<Protected><ChatPage /></Protected>} />
        <Route path="*" element={<Navigate to="/upload" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
