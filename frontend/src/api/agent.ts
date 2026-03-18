import type { AgentName, ToolInfo } from "../types";

const API = "http://localhost:8000";
const WS_BASE = API.replace(/^http/, "ws");

export function connectAgent(
  agent: AgentName,
  params: Record<string, unknown>,
  onEvent: (evt: Record<string, unknown>) => void,
  onClose?: () => void,
): WebSocket {
  const ws = new WebSocket(`${WS_BASE}/ws/${agent}`);
  ws.onopen = () => ws.send(JSON.stringify(params));
  ws.onmessage = (m) => {
    try { onEvent(JSON.parse(m.data)); } catch {}
  };
  ws.onclose = () => onClose?.();
  ws.onerror = () => onClose?.();
  return ws;
}

export async function getTools(): Promise<{ total: number; tools: ToolInfo[] }> {
  const r = await fetch(`${API}/api/tools`);
  return r.json();
}

export async function getHealth(): Promise<boolean> {
  try { return (await fetch(`${API}/api/health`)).ok; } catch { return false; }
}