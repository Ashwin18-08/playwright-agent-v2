import type { ReactNode } from "react";
import type { AgentStatus } from "../types";
import { StatusIndicator } from "./StatusIndicator";

interface Props {
  title: string;
  icon: string;
  accent: string;
  description: string;
  status: AgentStatus;
  iteration: number;
  children: ReactNode;
}

export function AgentCard({ title, icon, accent, description, status, iteration, children }: Props) {
  return (
    <div style={{
      backgroundColor: "#111318",
      borderRadius: 16,
      border: `1px solid ${status === "running" ? accent + "40" : "#1e2130"}`,
      overflow: "hidden",
      transition: "border-color 0.3s",
      display: "flex",
      flexDirection: "column",
    }}>
      {/* Header */}
      <div style={{
        padding: "16px 20px",
        borderBottom: "1px solid #1e2130",
        background: `linear-gradient(135deg, ${accent}08 0%, transparent 60%)`,
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{
              fontSize: 20, width: 36, height: 36, borderRadius: 10,
              backgroundColor: `${accent}15`, display: "flex",
              alignItems: "center", justifyContent: "center",
            }}>{icon}</span>
            <div>
              <div style={{ fontSize: 15, fontWeight: 700, color: "#fff" }}>{title}</div>
              <div style={{ fontSize: 11, color: "#6b7280", marginTop: 1 }}>{description}</div>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            {status === "running" && iteration > 0 && (
              <span style={{
                fontSize: 10, fontFamily: "monospace", color: "#6b7280",
                backgroundColor: "#1e2130", padding: "2px 6px", borderRadius: 4,
              }}>
                iter {iteration}
              </span>
            )}
            <StatusIndicator status={status} />
          </div>
        </div>
      </div>

      {/* Content */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        {children}
      </div>
    </div>
  );
}