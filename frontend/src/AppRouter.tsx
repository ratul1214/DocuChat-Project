import { BrowserRouter, Routes, Route, Navigate, Link } from "react-router-dom";
import LoginPage from "./pages/LoginPage";
import UploadPage from "./pages/UploadPage";
import ChatPage from "./pages/ChatPage";

function Protected({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem("token");
  return token ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function AppRouter() {
  return (
    <BrowserRouter>
      <header style={{ padding: 12, borderBottom: "1px solid #eee" }}>
        <nav style={{ display: "flex", gap: 12 }}>
          <Link to="/upload">Upload</Link>
          <Link to="/chat">Chat</Link>
          <span style={{ marginLeft: "auto", opacity: 0.6 }}>DocuChat</span>
        </nav>
      </header>

      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/upload" element={<Protected><UploadPage /></Protected>} />
        <Route path="/chat" element={<Protected><ChatPage /></Protected>} />
        <Route path="*" element={<Navigate to="/upload" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
