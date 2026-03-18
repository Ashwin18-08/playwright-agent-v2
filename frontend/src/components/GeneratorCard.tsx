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
  "browser_select_option", "browser_generate_locator", "test_run", "test_list",
  "generator_setup_page",
];

export function GeneratorCard() {
  const [url, setUrl] = useState("");
  const [spec, setSpec] = useState("");
  const [showTools, setShowTools] = useState(false);
  const { events, status, output, iteration, run, stop } = useAgent("generator");

  const submit = () => {
    if (!spec.trim() || status === "running") return;
    run({ url: url.trim(), spec: spec.trim() });
  };

  return (
    <AgentCard
      title="Generator"
      icon={"\u{1F9EA}"}
      accent="#34d399"
      description="Spec → .spec.ts test files"
      status={status}
      iteration={iteration}
    >
      <div style={{ padding: "12px 16px", borderBottom: "1px solid #1e2130" }}>
        <input type="text" placeholder="Target URL" value={url}
          onChange={(e) => setUrl(e.target.value)} style={inputStyle} />
        <textarea placeholder="Paste markdown test plan here..."
          value={spec} onChange={(e) => setSpec(e.target.value)}
          rows={4} style={{ ...inputStyle, marginTop: 6, resize: "vertical", minHeight: 80 }} />
        <div style={{ display: "flex", gap: 6, marginTop: 8, alignItems: "center" }}>
          {status === "running" ? (
            <button onClick={stop} style={{ ...btnStyle, backgroundColor: "#ef4444" }}>Stop</button>
          ) : (
            <button onClick={submit} disabled={!spec.trim()} style={{
              ...btnStyle, backgroundColor: spec.trim() ? "#34d399" : "#2d3148",
              color: spec.trim() ? "#000" : "#fff",
              cursor: spec.trim() ? "pointer" : "not-allowed",
            }}>Generate tests</button>
          )}
          <button onClick={() => setShowTools(!showTools)} style={{
            ...btnStyle, backgroundColor: "transparent", border: "1px solid #2d3148",
            color: "#6b7280", fontSize: 10,
          }}>
            {showTools ? "Hide" : "Show"} {TOOLS.length} tools
          </button>
        </div>
        {showTools && <ToolBadges tools={TOOLS} accent="#34d399" />}
      </div>

      <EventStream events={events} />

      {output && <FileViewer content={output} title="Generated test files" />}
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