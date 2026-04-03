"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getCrossBrand, BRAND_NAMES, BRAND_COLORS } from "@/lib/api";
import { Badge, Sidebar } from "@/app/page";

export default function CrossBrandPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    getCrossBrand().then((d) => { setData(d); setLoading(false); });
  }, []);

  if (loading) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", color: "#4a5568" }}>
      Loading...
    </div>
  );

  const { summary, conversations } = data;

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0f1117" }}>
      <Sidebar active="cross-brand" />
      <main style={{ flex: 1, padding: "28px 32px", overflowY: "auto" }}>

        {/* Header */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
            <div style={{ background: "#3b1515", border: "1px solid #f87171", borderRadius: 6, padding: "3px 10px", fontSize: 11, color: "#f87171", fontWeight: 600, letterSpacing: "0.05em" }}>
              CROSS-BRAND FINDING
            </div>
            <div style={{ fontSize: 11, color: "#4a5568" }}>Discovered independently · not part of original brief</div>
          </div>
          <h1 style={{ fontSize: 18, fontWeight: 600, color: "#e2e8f0", marginBottom: 6 }}>
            Comparison-intent conversations score higher on frustration
          </h1>
          <p style={{ fontSize: 13, color: "#718096", maxWidth: 700, lineHeight: 1.6 }}>
            {summary.pattern}. {summary.reason}.
          </p>
        </div>

        {/* Summary metric cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 20 }}>
          {[
            { label: "Matched conversations", value: summary.total_matched, color: "#818cf8" },
            { label: "With frustration flag", value: summary.frustrated_count, color: "#f87171" },
            { label: "Avg score (frustrated)", value: summary.avg_frustrated_score, color: "#fbbf24" },
            { label: "Avg score (others)", value: summary.avg_normal_score, color: "#34d399" },
          ].map((m) => (
            <div key={m.label} style={{ background: "#161b27", border: "1px solid #1e2535", borderRadius: 10, padding: "14px 16px" }}>
              <div style={{ fontSize: 11, color: "#4a5568", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 8 }}>{m.label}</div>
              <div style={{ fontSize: 26, fontWeight: 600, color: m.color }}>{m.value}</div>
            </div>
          ))}
        </div>

        {/* Recommendation box */}
        <div style={{ background: "#0d2b1e", border: "1px solid #34d399", borderRadius: 10, padding: "14px 18px", marginBottom: 24 }}>
          <div style={{ fontSize: 11, color: "#34d399", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6, fontWeight: 600 }}>
            Recommended fix
          </div>
          <div style={{ fontSize: 13, color: "#a0aec0", lineHeight: 1.6 }}>{summary.recommendation}</div>
        </div>

        {/* Conversations list */}
        <div style={{ fontSize: 11, color: "#4a5568", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 12 }}>
          Flagged conversations ({conversations.length}) — click to expand full thread
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {conversations.map((conv: any) => (
            <div
              key={conv.conversation_id}
              style={{
                background: "#161b27",
                border: `1px solid ${conv.frustration ? "#3b1515" : "#1e2535"}`,
                borderRadius: 10,
                overflow: "hidden",
              }}
            >
              {/* Conversation header row */}
              <div
                onClick={() => setExpanded(expanded === conv.conversation_id ? null : conv.conversation_id)}
                style={{ padding: "13px 18px", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "space-between" }}
                onMouseEnter={e => (e.currentTarget.style.background = "#1a2030")}
                onMouseLeave={e => (e.currentTarget.style.background = "transparent")}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                  <div style={{ width: 8, height: 8, borderRadius: "50%", background: BRAND_COLORS[conv.widgetId] || "#718096", flexShrink: 0 }} />
                  <span style={{ fontSize: 12.5, color: "#e2e8f0", fontWeight: 500 }}>
                    {BRAND_NAMES[conv.widgetId] || conv.widgetId}
                  </span>
                  {conv.frustration && <Badge color="red" text="Frustrated" />}
                  {conv.hallucination && <Badge color="purple" text="Hallucination" />}
                  {conv.low_quality && <Badge color="gray" text="Low quality response" />}
                  {conv.matched_patterns.includes("confused between") && <Badge color="amber" text="confused between" />}
                  {conv.matched_patterns.includes("difference between") && <Badge color="amber" text="difference between" />}
                  {conv.matched_patterns.includes("confused") &&
                    !conv.matched_patterns.includes("confused between") &&
                    <Badge color="amber" text="confused" />}
                  <span style={{ fontSize: 11, color: "#4a5568" }}>· score: {conv.score}</span>
                </div>
                <span style={{ fontSize: 11, color: "#4a5568", flexShrink: 0 }}>
                  {expanded === conv.conversation_id ? "▲ collapse" : "▼ view conversation"}
                </span>
              </div>

              {/* Expanded full conversation thread */}
              {expanded === conv.conversation_id && (
                <div style={{ borderTop: "1px solid #1e2535", padding: "16px 18px", display: "flex", flexDirection: "column", gap: 12 }}>
                  {conv.messages.map((msg: any, i: number) => {
                    const isUser = msg.sender === "user";
                    const hasFrustration = msg.tags.includes("frustration");
                    const hasConfusion = msg.tags.includes("confusion");

                    return (
                      <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: isUser ? "flex-start" : "flex-end" }}>
                        <div style={{ fontSize: 10, color: "#4a5568", marginBottom: 3, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                          {isUser ? "Customer" : "Assistant"}
                        </div>
                        <div style={{
                          background: isUser
                            ? hasFrustration ? "#3b1515"
                              : hasConfusion ? "#2d2010"
                                : "#1e2535"
                            : "#1a1f3d",
                          border: `1px solid ${hasFrustration ? "#f87171" : hasConfusion ? "#fbbf24" : "#2d3748"}`,
                          borderRadius: 8,
                          padding: "9px 13px",
                          maxWidth: "72%",
                          fontSize: 12.5,
                          color: "#a0aec0",
                          lineHeight: 1.6,
                          whiteSpace: "pre-wrap",
                          wordBreak: "break-word",
                        }}>
                          {msg.text || "(empty)"}
                        </div>
                        {msg.tags.length > 0 && (
                          <div style={{ display: "flex", gap: 5, marginTop: 4 }}>
                            {msg.tags.map((tag: string) => (
                              <Badge
                                key={tag}
                                color={tag === "frustration" ? "red" : "amber"}
                                text={tag.charAt(0).toUpperCase() + tag.slice(1) + " detected"}
                              />
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}