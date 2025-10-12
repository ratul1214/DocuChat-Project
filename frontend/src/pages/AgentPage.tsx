import { useEffect, useRef, useState } from "react";
import {
  startAgentReport,
  connectProgressWS,
  getReport,
  listReports,
} from "../services/api";
import { marked } from "marked";

export default function AgentPage() {
  const [topic, setTopic] = useState("Summarize my uploaded documents");
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [report, setReport] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  const pushLog = (line: string) =>
    setLogs((prev) => [...prev, `${new Date().toLocaleTimeString()} → ${line}`]);

  useEffect(() => {
    listReports().then(setHistory).catch(console.error);
    return () => wsRef.current?.close();
  }, []);

  async function runAgent() {
    setIsRunning(true);
    setLogs([]);
    setReport(null);

    try {
      const { report_id } = await startAgentReport(topic, 6);
      pushLog(`Started agent report #${report_id}`);

      wsRef.current?.close();
      wsRef.current = connectProgressWS(async (msg) => {
        const kind = msg.kind;
        const data = msg.data;

        if (kind === "error") {
          pushLog(`❌ Error: ${data.error}`);
          setIsRunning(false);
          return;
        }

        pushLog(`${kind}: ${JSON.stringify(data)}`);

        if (kind === "done" && data.report_id) {
          const r = await getReport(data.report_id);
          setReport(r);
          setIsRunning(false);
          listReports().then(setHistory);
        }
      });
    } catch (err: any) {
      pushLog(`❌ ${err.message}`);
      setIsRunning(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold">🧠 AI Agent Reports</h1>

      <div className="bg-white p-4 rounded-lg shadow space-y-4">
        <input
          className="w-full border p-2 rounded"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Enter your question or topic..."
        />
        <button
          onClick={runAgent}
          disabled={isRunning}
          className={`px-4 py-2 rounded text-white ${
            isRunning ? "bg-gray-400" : "bg-blue-600 hover:bg-blue-700"
          }`}
        >
          {isRunning ? "Running..." : "Run Agent"}
        </button>
      </div>

      {/* Progress log */}
      <div className="bg-gray-50 border rounded-lg p-3 h-64 overflow-auto font-mono text-sm">
        {logs.length === 0 ? (
          <div className="text-gray-400">No progress yet...</div>
        ) : (
          logs.map((l, i) => <div key={i}>{l}</div>)
        )}
      </div>

      {/* Final Report */}
      {report && (
        <div className="bg-white p-4 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-2">{report.title}</h2>
          <div
            className="prose max-w-none"
            dangerouslySetInnerHTML={{ __html: marked(report.content || "") }}
          />
        </div>
      )}

      {/* Report History */}
      {history.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-2">📜 Past Reports</h2>
          <ul className="list-disc pl-6">
            {history.map((r) => (
              <li key={r.id}>
                <button
                  onClick={() => getReport(r.id).then(setReport)}
                  className="text-blue-600 hover:underline"
                >
                  {r.title} —{" "}
                  <span className="text-gray-500 text-sm">
                    {new Date(r.created_at).toLocaleString()}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
