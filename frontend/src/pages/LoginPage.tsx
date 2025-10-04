import { useState } from "react";
import { Button, Card, Input, Typography, message } from "antd";
import { getMe } from "../services/api";

const { Title, Paragraph } = Typography;

export default function LoginPage() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [loading, setLoading] = useState(false);

  async function useToken() {
    try {
      setLoading(true);
      localStorage.setItem("token", token);
      // sanity check
      await getMe();
      message.success("Logged in");
      window.location.assign("/upload");
    } catch {
      message.error("Invalid token or server unreachable");
      localStorage.removeItem("token");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 520, margin: "48px auto", padding: 16 }}>
      <Card>
        <Title level={3}>Login</Title>
        <Paragraph style={{ marginBottom: 8 }}>
          Step&nbsp;1 allows <strong>mock OIDC</strong>: paste any token (e.g. <code>testtoken</code>).
        </Paragraph>
        <Input.Password
          placeholder="Paste Bearer token (mock allowed)"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          style={{ marginBottom: 12 }}
        />
        <Button type="primary" block onClick={useToken} loading={loading}>
          Use Token
        </Button>
        <Paragraph type="secondary" style={{ marginTop: 12 }}>
          In Step 2, replace this with real Keycloak login.
        </Paragraph>
      </Card>
    </div>
  );
}
