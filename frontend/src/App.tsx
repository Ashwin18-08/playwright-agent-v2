import { PlannerCard } from "./components/PlannerCard";
import { GeneratorCard } from "./components/GeneratorCard";
import { HealerCard } from "./components/HealerCard";
import { PipelineCard } from "./components/PipelineCard";

export default function App() {
  return (
    <div style={{
      minHeight: "100vh", backgroundColor: "#08090c",
      fontFamily: "'Inter', system-ui, -apple-system, sans-serif",
      color: "#e5e7eb",
    }}>
      {/* Header */}
      <div style={{
        padding: "20px 32px", borderBottom: "1px solid #1e2130",
        display: "flex", alignItems: "center", justifyContent: "space-between",
        background: "linear-gradient(135deg, #0f1117 0%, #111318 100%)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 28 }}>{"\u{1F3AD}"}</span>
          <div>
            <h1 style={{ margin: 0, fontSize: 20, fontWeight: 800, color: "#fff", letterSpacing: "-0.5px" }}>
              Playwright Test Agents
            </h1>
            <p style={{ margin: 0, fontSize: 12, color: "#6b7280" }}>
              Powered by official Playwright MCP + Azure OpenAI + LangGraph ReAct
            </p>
          </div>
        </div>
        <div style={{
          display: "flex", gap: 16, fontSize: 11, color: "#4b5563",
        }}>
          <span>Planner: explore + spec</span>
          <span style={{ color: "#2d3148" }}>|</span>
          <span>Generator: spec → tests</span>
          <span style={{ color: "#2d3148" }}>|</span>
          <span>Healer: run + fix</span>
        </div>
      </div>

      {/* Cards grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))",
        gap: 16,
        padding: "20px 24px",
        maxWidth: 1800,
        margin: "0 auto",
      }}>
        <PlannerCard />
        <GeneratorCard />
        <HealerCard />
        <PipelineCard />
      </div>
    </div>
  );
}