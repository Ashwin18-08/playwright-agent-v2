import { useState } from "react";
import { useAgent } from "../hooks/useAgent";
import { AgentCard } from "./AgentCard";
import { EventStream } from "./EventStream";
import { FileViewer } from "./FileViewer";

export function PipelineCard() {
  const [url, setUrl] = useState("");
  const [goal, setGoal] = useState("");
  const { events, status, output, iteration, run, stop } = useAgent("pipeline");

  const submit = () => {
    if (!goal.trim() || status === "running") return;
    run({ url: url.trim(), goal: goal.trim() });
  };

  // Extract current phase from events
  const phases = events.filter((e) => e.kind === "pipeline_phase");
  const currentPhase = phases.length > 0 ? (phases[phases.length - 1].phase as string) : "";

  // Extract artifacts
  const artifacts = events.filter((e) => e.kind === "pipeline_artifact");

  return (
    <AgentCard
      title="Full pipeline"
      icon={"\u{1F3AD}"}
      accent="#c084fc"
      description="Planner → Generator → Healer"
      status={status}
      iteration={iteration}
    >
      <div style={{ padding: "12px 16px", borderBottom: "1px solid #1e2130" }}>
        <input type="text" placeholder="Target URL" value={url}
          onChange={(e) => setUrl(e.target.value)} style={inputStyle} />
        <input type="text" placeholder="Test goal"
          value={goal} onChange={(e) => setGoal(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          style={{ ...inputStyle, marginTop: 6 }} />
        <div style={{ display: "flex", gap: 6, marginTop: 8, alignItems: "center" }}>
          {status === "running" ? (
            <button onClick={stop} style={{ ...btnStyle, backgroundColor: "#ef4444" }}>Stop</button>
          ) : (
            <button onClick={submit} disabled={!goal.trim()} style={{
              ...btnStyle, backgroundColor: goal.trim() ? "#c084fc" : "#2d3148",
              color: goal.trim() ? "#000" : "#fff",
              cursor: goal.trim() ? "pointer" : "not-allowed",
            }}>Run full pipeline</button>
          )}
        </div>

        {/* Phase indicators */}
        {status !== "idle" && (
          <div style={{ display: "flex", gap: 4, marginTop: 10 }}>
            {["planner", "generator", "healer"].map((p) => {
              const done = phases.findIndex((e) => e.phase === p) >= 0 && currentPhase !== p;
              const active = currentPhase === p;
              return (
                <div key={p} style={{
                  flex: 1, padding: "6px 0", borderRadius: 6, textAlign: "center",
                  fontSize: 11, fontWeight: 600, transition: "all 0.3s",
                  backgroundColor: active ? "#c084fc20" : done ? "#34d39920" : "#1e2130",
                  color: active ? "#c084fc" : done ? "#34d399" : "#4b5563",
                  border: active ? "1px solid #c084fc40" : "1px solid transparent",
                }}>
                  {done ? "\u2713 " : active ? "\u25B6 " : ""}{p}
                </div>
              );
            })}
          </div>
        )}
      </div>

      <EventStream events={events} />

      {artifacts.map((a, i) => (
        <FileViewer
          key={i}
          content={(a.content as string) || ""}
          title={`${a.artifact_type}: ${(a.filename as string) || a.phase}`}
        />
      ))}
    </AgentCard>
  );
}

const inputStyle: React.CSSProperties = {
  width: "100%", padding: "8px 12px", borderRadius: 8, fontSize: 12,
  border: "1px solid #2d3148", backgroundColor: "#0c0d14",
  color: "#e5e7eb", outline: "none", boxSizing: "border-box",
};

const btnStyle: React.CSSProperties = {
  padding: "6px 14px", borderRadius: 8, border: "none",
  color: "#fff", fontWeight: 600, fontSize: 12, cursor: "pointer",
};