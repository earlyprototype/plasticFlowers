import { ReferenceNode } from "../../lib/types";

type ResearchPanelProps = {
    references: ReferenceNode[];
};

export function ResearchPanel({ references }: ResearchPanelProps) {
    if (references.length === 0) {
        return null;
    }

    return (
        <div
            style={{
                display: "flex",
                flexDirection: "column",
                gap: "10px",
                padding: "12px",
                background: "#FFFFFF",
                borderRadius: "12px",
                boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
                maxHeight: "400px",
                overflowY: "auto",
            }}
        >
            <h3
                style={{
                    margin: 0,
                    fontSize: "15px",
                    fontWeight: 700,
                    color: "#111827",
                    borderBottom: "1px solid #E5E7EB",
                    paddingBottom: "8px",
                }}
            >
                Librarian ({references.length})
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {references.map((ref) => (
                    <div
                        key={ref.id}
                        style={{
                            padding: "8px",
                            background: "#F9FAFB",
                            borderRadius: "8px",
                            border: "1px solid #E5E7EB",
                            fontSize: "13px",
                        }}
                    >
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
                            <span style={{ fontWeight: 600, color: "#4B5563" }}>{ref.entity_type || "Entity"}</span>
                            <span
                                style={{
                                    fontSize: "11px",
                                    padding: "2px 6px",
                                    borderRadius: "10px",
                                    background: ref.confidence > 0.8 ? "#DCFCE7" : "#FEF3C7",
                                    color: ref.confidence > 0.8 ? "#166534" : "#92400E",
                                }}
                            >
                                {Math.round(ref.confidence * 100)}%
                            </span>
                        </div>
                        <p style={{ margin: "0 0 8px 0", color: "#374151" }}>{ref.canonical_summary}</p>
                        {ref.sources.length > 0 && (
                            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                                {ref.sources.map((source, i) => (
                                    <a
                                        key={i}
                                        href={source.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        title={source.snippet}
                                        style={{
                                            fontSize: "11px",
                                            color: "#2563EB",
                                            textDecoration: "none",
                                            background: "#EFF6FF",
                                            padding: "2px 6px",
                                            borderRadius: "4px",
                                        }}
                                    >
                                        {source.title.substring(0, 20)}...
                                    </a>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
