import { useState } from "react";
import { useAgent } from "../hooks/useAgent";
import { AgentCard } from "./AgentCard";
import { EventStream } from "./EventStream";
import { FileViewer } from "./FileViewer";
import { ToolBadges } from "./ToolBadges";

const TOOLS = [
  "browser_navigate", "browser_click", "browser_type", "browser_snapshot",
  "browser_screenshot", "browser_hover", "browser_press_key", "browser_wait",
  "browser_scroll_down", "browser_scroll_up", "browser_go_back", "browser_go_forward",
  "browser_select_option", "browser_tab_new", "browser_tab_select", "browser_tab_close",
  "browser_drag", "browser_file_upload", "test_run", "planner_setup_page",
];

export function PlannerCard() {
  const [url, setUrl] = useState("");
  const [goal, setGoal] = useState("");
  const [showTools, setShowTools] = useState(false);
  const { events, status, output, iteration, run, stop } = useAgent("planner");

  const submit = () => {
    if (!goal.trim() || status === "running") return;
    run({ url: url.trim(), goal: goal.trim() });
  };

  return (
    <AgentCard
      title="Planner"
      icon={"\u{1F4CB}"}
      accent="#818cf8"
      description="Explore app + write test plan"
      status={status}
      iteration={iteration}
    >
      <div style={{ padding: "12px 16px", borderBottom: "1px solid #1e2130" }}>
        <input type="text" placeholder="Target URL" value={url}
          onChange={(e) => setUrl(e.target.value)} style={inputStyle} />
        <input type="text" placeholder="Test goal (e.g. 'Create login tests')"
          value={goal} onChange={(e) => setGoal(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()} style={{ ...inputStyle, marginTop: 6 }} />
        <div style={{ display: "flex", gap: 6, marginTop: 8, alignItems: "center" }}>
          {status === "running" ? (
            <button onClick={stop} style={{ ...btnStyle, backgroundColor: "#ef4444" }}>Stop</button>
          ) : (
            <button onClick={submit} disabled={!goal.trim()} style={{
              ...btnStyle, backgroundColor: goal.trim() ? "#818cf8" : "#2d3148",
              cursor: goal.trim() ? "pointer" : "not-allowed",
            }}>Explore & Plan</button>
          )}
          <button onClick={() => setShowTools(!showTools)} style={{
            ...btnStyle, backgroundColor: "transparent", border: "1px solid #2d3148",
            color: "#6b7280", fontSize: 10,
          }}>
            {showTools ? "Hide" : "Show"} {TOOLS.length} tools
          </button>
        </div>
        {showTools && <ToolBadges tools={TOOLS} accent="#818cf8" />}
      </div>

      <EventStream events={events} />

      {output && <FileViewer content={output} title="specs/test-plan.md" />}
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