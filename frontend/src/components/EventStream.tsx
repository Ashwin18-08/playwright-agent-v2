import { useEffect, useRef } from "react";
import type { AgentEvent } from "../types";

const ICONS: Record<string, string> = {
  started: "\u{1F680}", thinking: "\u{1F9E0}", tool_call: "\u{1F527}",
  tool_result: "\u{2705}", output: "\u{1F4DD}", error: "\u{274C}",
  done: "\u{1F389}", max_iterations: "\u{26A0}", pipeline_phase: "\u{1F3AD}",
  pipeline_artifact: "\u{1F4E6}", pipeline_done: "\u{1F389}", pipeline_error: "\u{274C}",
};

const COLORS: Record<string, string> = {
  started: "#818cf8", thinking: "#6b7280", tool_call: "#22d3ee",
  tool_result: "#34d399", output: "#a78bfa", error: "#ef4444",
  done: "#34d399", max_iterations: "#f59e0b", pipeline_phase: "#818cf8",
  pipeline_artifact: "#c084fc", pipeline_done: "#34d399", pipeline_error: "#ef4444",
};

export function EventStream({ events }: { events: AgentEvent[] }) {
  const bottom = useRef<HTMLDivElement>(null);
  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [events.length]);

  if (events.length === 0) {
    return (
      <div style={{
        padding: 24, textAlign: "center", color: "#4b5563", fontSize: 13,
      }}>
        No events yet — start the agent to see live activity
      </div>
    );
  }

  return (
    <div style={{ maxHeight: 360, overflowY: "auto", padding: "8px 0" }}>
      {events.map((evt, i) => {
        const icon = ICONS[evt.kind] || "\u{2022}";
        const accent = COLORS[evt.kind] || "#6b7280";
        return (
          <div key={i} style={{
            display: "flex", gap: 8, padding: "5px 12px",
            borderLeft: `2px solid ${accent}`, marginBottom: 3,
            borderRadius: "0 4px 4px 0", fontSize: 12,
            backgroundColor: `${accent}08`,
          }}>
            <span style={{ fontSize: 14, flexShrink: 0 }}>{icon}</span>
            <div style={{ minWidth: 0 }}>
              <span style={{
                fontWeight: 600, color: accent, fontSize: 10,
                textTransform: "uppercase", letterSpacing: "0.5px",
              }}>
                {evt.kind.replace(/_/g, " ")}
              </span>
              <div style={{
                color: "#d1d5db", marginTop: 1,
                whiteSpace: "pre-wrap", wordBreak: "break-word",
                maxHeight: 100, overflow: "auto", fontSize: 11,
                fontFamily: "monospace", lineHeight: 1.4,
              }}>
                {formatEvent(evt)}
              </div>
            </div>
          </div>
        );
      })}
      <div ref={bottom} />
    </div>
  );
}

function formatEvent(e: AgentEvent): string {
  const { kind, ...r } = e;
  switch (kind) {
    case "started":
      return `Agent: ${r.agent} | Tools: ${r.tools_count}`;
    case "thinking":
      return `Iteration ${r.iteration}`;
    case "tool_call":
      return `${r.tool}(${JSON.stringify(r.args || {}).slice(0, 120)})`;
    case "tool_result":
      return `${r.tool} — ${r.success ? "OK" : "FAIL"}\n${(r.result_preview as string || "").slice(0, 200)}`;
    case "output":
      return (r.text as string || "").slice(0, 300) + ((r.text as string || "").length > 300 ? "..." : "");
    case "pipeline_phase":
      return r.message as string || "";
    case "pipeline_artifact":
      return `[${r.artifact_type}] ${r.filename || ""}`;
    case "error":
    case "pipeline_error":
      return r.message as string || JSON.stringify(r);
    default:
      return JSON.stringify(r, null, 2).slice(0, 200);
  }
}