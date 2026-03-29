"use client";
import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { getInsights, BRAND_NAMES, BRAND_COLORS } from "@/lib/api";
import { Sidebar, Badge } from "@/app/page";

export default function InsightsPage() {
  const { id } = useParams() as { id: string };
  const searchParams = useSearchParams();
  const convFilter = searchParams.get("conv");
  const [insights, setInsights] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getInsights(id).then(data => { setInsights(data); setLoading(false); });
  }, [id]);

  const brandColor = BRAND_COLORS[id] || "#818cf8";
  const brandName = BRAND_NAMES[id] || id.slice(0, 8);
  const activeKey = id === "680a0a8b70a26f7a0e24eedd" ? "insights-a" : id === "6983153e1497a62e8542a0ad" ? "insights-b" : "insights-c";

  if (loading) return <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", color: "#4a5568" }}>Loading insights...</div>;

  const filtered = insights.filter(item => !convFilter || item.conversation_id === convFilter);

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar active={activeKey} />
      <main style={{ flex: 1, padding: "28px 32px", overflowY: "auto" }}>
        <div style={{ marginBottom: 24 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: brandColor }} />
            <h1 style={{ fontSize: 20, fontWeight: 600, color: "#e2e8f0" }}>
              {convFilter ? "Conversation insight" : `Top issues — ${brandName}`}
            </h1>
          </div>
          <p style={{ fontSize: 12, color: "#4a5568", marginTop: 4 }}>
            {convFilter ? `Showing 1 conversation` : `${insights.length} worst conversations · LLM-analysed`}
          </p>
        </div>

        {convFilter && (
          <div onClick={() => window.history.back()}
            style={{ fontSize: 12, color: "#818cf8", cursor: "pointer", marginBottom: 20 }}>
            ← Back to all insights
          </div>
        )}

        {filtered.length === 0 && (
          <div style={{ color: "#4a5568", textAlign: "center", marginTop: 60 }}>No insights available.</div>
        )}

        {filtered.map((item, i) => {
          const severity = item.insight?.severity || "medium";
          const sevColor = severity === "high" ? "red" : severity === "medium" ? "amber" : "green";
          return (
            <div key={item.conversation_id || i} style={{ background: "#161b27", border: "1px solid #1e2535", borderRadius: 10, padding: 18, marginBottom: 12 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 10 }}>
                <span style={{ fontSize: 11, color: "#4a5568", fontFamily: "monospace" }}>{item.conversation_id?.slice(0, 16)}...</span>
                <Badge color="gray" text={`score ${item.score}`} />
                <Badge color={sevColor} text={`${severity} severity`} />
                {item.flags?.frustration && <Badge color="red" text="frustration" />}
                {item.flags?.hallucination && <Badge color="purple" text="hallucination" />}
                {item.flags?.low_quality_response && <Badge color="amber" text="low quality" />}
                {item.flags?.irrelevant_product && <Badge color="amber" text="irrelevant product" />}
                {item.flags?.drop_off_flag && <Badge color="gray" text="drop-off" />}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
                {[
                  { label: "What went wrong", val: item.insight?.what_went_wrong },
                  { label: "Why", val: item.insight?.why },
                  { label: "How to fix", val: item.insight?.how_to_fix },
                ].map(f => (
                  <div key={f.label} style={{ background: "#0f1117", borderRadius: 8, padding: "10px 12px" }}>
                    <div style={{ fontSize: 10, color: "#4a5568", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>{f.label}</div>
                    <div style={{ fontSize: 12, color: "#a0aec0", lineHeight: 1.6 }}>{f.val || "—"}</div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </main>
    </div>
  );
}