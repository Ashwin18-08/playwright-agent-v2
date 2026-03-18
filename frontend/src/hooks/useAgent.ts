import { useCallback, useRef, useState } from "react";
import { connectAgent } from "../api/agent";
import type { AgentEvent, AgentName, AgentStatus } from "../types";

export function useAgent(agentName: AgentName) {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [status, setStatus] = useState<AgentStatus>("idle");
  const [output, setOutput] = useState("");
  const [iteration, setIteration] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);

  const run = useCallback((params: Record<string, unknown>) => {
    setEvents([]);
    setStatus("running");
    setOutput("");
    setIteration(0);

    const ws = connectAgent(
      agentName,
      params,
      (data) => {
        const evt = data as AgentEvent;
        setEvents((p) => [...p, evt]);

        switch (evt.kind) {
          case "thinking":
            setIteration((evt.iteration as number) || 0);
            break;
          case "output":
          case "pipeline_artifact":
            setOutput((p) => p + ((evt.text || evt.content || "") as string) + "\n");
            break;
          case "done":
          case "pipeline_done":
            setStatus("done");
            break;
          case "error":
          case "pipeline_error":
            setStatus("error");
            break;
          case "max_iterations":
            setStatus("done");
            break;
        }
      },
      () => setStatus((p) => (p === "running" ? "done" : p)),
    );
    wsRef.current = ws;
  }, [agentName]);

  const stop = useCallback(() => {
    wsRef.current?.close();
    wsRef.current = null;
    setStatus("idle");
  }, []);

  return { events, status, output, iteration, run, stop };
}