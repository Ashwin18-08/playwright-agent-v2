interface Props {
  tools: string[];
  accent: string;
}

export function ToolBadges({ tools, accent }: Props) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 8 }}>
      {tools.map((t) => (
        <span key={t} style={{
          fontSize: 10, fontFamily: "monospace", padding: "2px 6px",
          borderRadius: 4, backgroundColor: `${accent}15`, color: accent,
          border: `1px solid ${accent}30`,
        }}>
          {t}
        </span>
      ))}
    </div>
  );
}