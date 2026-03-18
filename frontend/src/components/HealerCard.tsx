import { useState } from "react";
import { useAgent } from "../hooks/useAgent";
import { AgentCard } from "./AgentCard";
import { EventStream } from "./EventStream";
import { FileViewer } from "./FileViewer";
import { ToolBadges } from "./ToolBadges";

const TOOLS = [
  "browser_console_messages", "browser_evaluate", "browser_generate_locator",
  "browser_network_requests", "browser_snapshot", "browser_screenshot",
  "test_debug", "test_list", "test_run",
];

export function HealerCard() {
  const [url, setUrl] = useState("");
  const [testFile, setTestFile] = useState("");
  const [showTools, setShowTools] = useState(false);
  const { events, status, output, iteration, run, stop } = useAgent("healer");

  const submit = () => {
    if (status === "running") return;
    run({ url: url.trim(), test_file: testFile.trim() });
  };

  return (
    <AgentCard
      title="Healer"
      icon={"\u{1FA79}"}
      accent="#f97316"
      description="Run tests + fix failures"
      status={status}
      iteration={iteration}
    >
      <div style={{ padding: "12px 16px", borderBottom: "1px solid #1e2130" }}>
        <input type="text" placeholder="Target URL (optional)" value={url}
          onChange={(e) => setUrl(e.target.value)} style={inputStyle} />
        <input type="text" placeholder="Focus on file (optional, e.g. tests/login.spec.ts)"
          value={testFile} onChange={(e) => setTestFile(e.target.value)}
          style={{ ...inputStyle, marginTop: 6 }} />
        <div style={{ display: "flex", gap: 6, marginTop: 8, alignItems: "center" }}>
          {status === "running" ? (
            <button onClick={stop} style={{ ...btnStyle, backgroundColor: "#ef4444" }}>Stop</button>
          ) : (
            <button onClick={submit} style={{ ...btnStyle, backgroundColor: "#f97316", color: "#000" }}>
              Run & heal
            </button>
          )}
          <button onClick={() => setShowTools(!showTools)} style={{
            ...btnStyle, backgroundColor: "transparent", border: "1px solid #2d3148",
            color: "#6b7280", fontSize: 10,
          }}>
            {showTools ? "Hide" : "Show"} {TOOLS.length} tools
          </button>
        </div>
        {showTools && <ToolBadges tools={TOOLS} accent="#f97316" />}
      </div>

      <EventStream events={events} />

      {output && <FileViewer content={output} title="Healer report" />}
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