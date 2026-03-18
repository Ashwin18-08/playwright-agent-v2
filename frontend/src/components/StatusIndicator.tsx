import type { AgentStatus } from "../types";

const cfg: Record<AgentStatus, { label: string; dot: string; bg: string; text: string }> = {
  idle:    { label: "Ready",    dot: "#4b5563", bg: "rgba(75,85,99,0.1)",   text: "#9ca3af" },
  running: { label: "Running",  dot: "#818cf8", bg: "rgba(129,140,248,0.1)", text: "#818cf8" },
  done:    { label: "Complete", dot: "#34d399", bg: "rgba(52,211,153,0.1)",  text: "#34d399" },
  error:   { label: "Error",    dot: "#ef4444", bg: "rgba(239,68,68,0.1)",   text: "#ef4444" },
};

export function StatusIndicator({ status }: { status: AgentStatus }) {
  const c = cfg[status];
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      padding: "3px 10px", borderRadius: 99, fontSize: 11, fontWeight: 600,
      color: c.text, backgroundColor: c.bg,
    }}>
      <span style={{
        width: 6, height: 6, borderRadius: "50%", backgroundColor: c.dot,
        animation: status === "running" ? "pulse 1.2s infinite" : "none",
      }} />
      {c.label}
    </span>
  );
}