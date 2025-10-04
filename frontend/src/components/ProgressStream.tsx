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
