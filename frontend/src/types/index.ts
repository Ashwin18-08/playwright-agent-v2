export interface AgentEvent {
  kind: string;
  [key: string]: unknown;
}

export type AgentName = "planner" | "generator" | "healer" | "pipeline";

export type AgentStatus = "idle" | "running" | "done" | "error";

export interface ToolInfo {
  name: string;
  description: string;
  agents: AgentName[];
}