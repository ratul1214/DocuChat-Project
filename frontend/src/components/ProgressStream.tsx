import { useEffect, useRef, useState } from 'react';

export default function ProgressStream() {
  const [lines, setLines] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const sub = localStorage.getItem('sub') || 'mock-user';
    const tenant = localStorage.getItem('tenant') || 'default';
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${proto}://${window.location.host}/ws/progress?tenant=${tenant}&sub=${sub}`);
    wsRef.current = ws;

    ws.onopen = () => setLines(ls => [...ls, 'WS connected']);
    ws.onmessage = (evt) => {
      console.log("📩 WS message:", evt.data);
      try {
        const data = JSON.parse(evt.data);
        const msg = data.stage ? `${data.stage}: ${data.message}` : data.message || JSON.stringify(data);
        setLines(ls => [...ls, msg]);
      } catch {
        setLines(ls => [...ls, String(evt.data)]);
      }
    };
    ws.onclose = () => setLines(ls => [...ls, 'WS closed']);
    ws.onerror = () => setLines(ls => [...ls, 'WS error']);

    return () => { ws.close(); };
  }, []);

  return (
    <div className="text-xs h-32 overflow-auto border rounded p-2 bg-white">
      {lines.map((l, i) => <div key={i}>{l}</div>)}
    </div>
  );
}
