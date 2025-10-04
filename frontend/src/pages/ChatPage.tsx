import { useEffect, useState } from "react";
import { Button, Card, Input, List, Typography, message } from "antd";
import { ask, getMe } from "../services/api";

const { Title } = Typography;

type Citation = { index: number; filename: string; score?: number };

export default function ChatPage() {
  const [me, setMe] = useState<any>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [citations, setCitations] = useState<Citation[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        setMe(await getMe());
      } catch {
        message.error("Auth required");
        window.location.assign("/login");
      }
    })();
  }, []);

  async function onAsk() {
    setAnswer("");
    setCitations([]);
    setLoading(true);
    try {
      const r = await ask(question, 5);
      setAnswer(r.answer || "");
      setCitations(r.citations || []);
    } catch (e: any) {
      message.error(e.message || "Ask failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-12">
      <header className="flex items-center justify-between">
        <Title level={3} className="!mb-0">Chat</Title>
        <div className="text-sm opacity-70">Signed in as: {me?.sub ?? "unknown"}</div>
      </header>

      <Card title="Ask a question about your docs">
        <div className="space-y-3">
          <Input.TextArea
            rows={3}
            placeholder="e.g., What is my name in my CV?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <Button type="primary" onClick={onAsk} loading={loading} disabled={!question.trim()}>
            Ask
          </Button>

          {answer && (
            <div className="p-3 rounded bg-white border mt-2">
              <div className="whitespace-pre-wrap">{answer}</div>
              {citations?.length > 0 && (
                <>
                  <div className="font-medium mt-3 mb-1">Citations</div>
                  <List
                    size="small"
                    dataSource={citations}
                    renderItem={(c) => (
                      <List.Item>
                        [Doc {c.index}] {c.filename}
                        {typeof c.score === "number" ? ` (score ${c.score.toFixed?.(3) ?? c.score})` : ""}
                      </List.Item>
                    )}
                  />
                </>
              )}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
