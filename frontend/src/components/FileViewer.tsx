export function FileViewer({ content, title }: { content: string; title?: string }) {
  if (!content) return null;

  return (
    <div style={{
      borderRadius: 8, overflow: "hidden",
      border: "1px solid #1e2130", marginTop: 8,
    }}>
      {title && (
        <div style={{
          padding: "6px 12px", backgroundColor: "#161822",
          borderBottom: "1px solid #1e2130", display: "flex",
          justifyContent: "space-between", alignItems: "center",
        }}>
          <span style={{ fontSize: 11, fontFamily: "monospace", color: "#9ca3af" }}>
            {title}
          </span>
          <button onClick={() => navigator.clipboard.writeText(content)} style={{
            fontSize: 10, padding: "2px 8px", borderRadius: 4,
            border: "1px solid #2d3148", backgroundColor: "#1e2130",
            color: "#818cf8", cursor: "pointer", fontWeight: 600,
          }}>
            Copy
          </button>
        </div>
      )}
      <pre style={{
        margin: 0, padding: 12, fontSize: 11, lineHeight: 1.5,
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
        color: "#c4b5fd", whiteSpace: "pre-wrap", wordBreak: "break-word",
        maxHeight: 300, overflow: "auto", backgroundColor: "#0c0d14",
      }}>
        {content}
      </pre>
    </div>
  );
}