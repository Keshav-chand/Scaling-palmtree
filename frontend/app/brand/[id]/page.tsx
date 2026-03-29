"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getMetrics, getConversations, BRAND_NAMES, BRAND_COLORS } from "@/lib/api";
import { Sidebar, Badge } from "@/app/page";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis } from "recharts";
import { useRouter } from "next/navigation";

export default function BrandPage() {
  const { id } = useParams() as { id: string };
  const [metrics, setMetrics] = useState<any>(null);
  const [conversations, setConversations] = useState<any[]>([]);
  const router = useRouter();

  useEffect(() => {
    getMetrics(id).then(setMetrics);
    getConversations(id).then(setConversations);
  }, [id]);

  if (!metrics) return <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", color: "#4a5568" }}>Loading...</div>;

  const brandColor = BRAND_COLORS[id] || "#818cf8";
  const brandName = BRAND_NAMES[id] || id.slice(0, 8);
  const activeKey = id === "680a0a8b70a26f7a0e24eedd" ? "brand-a" : id === "6983153e1497a62e8542a0ad" ? "brand-b" : "brand-c";

  const intentData = Object.entries(metrics.intent_distribution || {}).map(([name, value]) => ({ name, value }));
  const INTENT_COLORS = ["#818cf8", "#34d399", "#fbbf24", "#f87171", "#c084fc"];

  const flagData = [
    { name: "Frustration", value: metrics.frustration_count || 0, color: "#f87171" },
    { name: "Irrelevant product", value: metrics.irrelevant_product_count || 0, color: "#fbbf24" },
    { name: "Drop-offs", value: metrics.drop_offs || 0, color: "#818cf8" },
    { name: "Low quality", value: metrics.low_quality_count || 0, color: "#4a5568" },
    { name: "Hallucination", value: metrics.hallucination_count || 0, color: "#c084fc" },
  ];

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar active={activeKey} />
      <main style={{ flex: 1, padding: "28px 32px", overflowY: "auto" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ width: 10, height: 10, borderRadius: "50%", background: brandColor }} />
              <h1 style={{ fontSize: 20, fontWeight: 600, color: "#e2e8f0" }}>{brandName} — detailed analysis</h1>
            </div>
            <p style={{ fontSize: 12, color: "#4a5568", marginTop: 4 }}>widgetId: {id.slice(0, 8)}... · {metrics.total_conversations} conversations</p>
          </div>
          <button onClick={() => router.push(`/insights/${id}?conv=${c.conversation_id}`)}
            style={{ background: "#1a1f3d", border: "1px solid #818cf8", color: "#818cf8", padding: "8px 16px", borderRadius: 8, cursor: "pointer", fontSize: 12 }}>
            View top insights →
          </button>
        </div>

        {/* Metric cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 20 }}>
          {[
            { label: "Total conversations", value: metrics.total_conversations, color: "#818cf8" },
            { label: "Drop-off rate", value: `${metrics.drop_off_pct}%`, color: metrics.drop_off_pct > 10 ? "#fbbf24" : "#34d399" },
            { label: "Frustration rate", value: `${metrics.frustration_pct}%`, color: metrics.frustration_pct > 8 ? "#f87171" : "#fbbf24" },
            { label: "Irrelevant products", value: metrics.irrelevant_product_count, color: metrics.irrelevant_product_count > 10 ? "#f87171" : "#fbbf24" },
          ].map(m => (
            <div key={m.label} style={{ background: "#161b27", border: "1px solid #1e2535", borderRadius: 10, padding: "14px 16px" }}>
              <div style={{ fontSize: 11, color: "#4a5568", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 8 }}>{m.label}</div>
              <div style={{ fontSize: 24, fontWeight: 600, color: m.color }}>{m.value}</div>
            </div>
          ))}
        </div>

        {/* Charts row */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 20 }}>
          {/* Intent pie */}
          <div style={{ background: "#161b27", border: "1px solid #1e2535", borderRadius: 10, padding: 20 }}>
            <div style={{ fontSize: 11, color: "#4a5568", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 14 }}>Intent distribution</div>
            <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
              <ResponsiveContainer width={130} height={130}>
                <PieChart>
                  <Pie data={intentData} cx="50%" cy="50%" innerRadius={35} outerRadius={60} dataKey="value" strokeWidth={0}>
                    {intentData.map((_, i) => <Cell key={i} fill={INTENT_COLORS[i % INTENT_COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: "#161b27", border: "1px solid #1e2535", color: "#e2e8f0", fontSize: 11 }} />
                </PieChart>
              </ResponsiveContainer>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {intentData.map((d, i) => (
                  <div key={d.name} style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 12, color: "#718096" }}>
                    <div style={{ width: 8, height: 8, borderRadius: "50%", background: INTENT_COLORS[i % INTENT_COLORS.length], flexShrink: 0 }} />
                    {d.name} · {String(d.value)}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Flag bar chart */}
          <div style={{ background: "#161b27", border: "1px solid #1e2535", borderRadius: 10, padding: 20 }}>
            <div style={{ fontSize: 11, color: "#4a5568", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 14 }}>Flag breakdown</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {flagData.map(f => {
                const max = Math.max(...flagData.map(x => x.value)) || 1;
                return (
                  <div key={f.name} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}>
                    <div style={{ width: 100, color: "#718096", fontSize: 11, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{f.name}</div>
                    <div style={{ flex: 1, height: 8, background: "#1e2535", borderRadius: 4, overflow: "hidden" }}>
                      <div style={{ height: "100%", width: `${(f.value / max) * 100}%`, background: f.color, borderRadius: 4 }} />
                    </div>
                    <div style={{ width: 24, textAlign: "right", color: "#a0aec0", fontSize: 11, fontWeight: 500 }}>{f.value}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Conversations list */}
        <div style={{ background: "#161b27", border: "1px solid #1e2535", borderRadius: 10, padding: 20 }}>
          <div style={{ fontSize: 11, color: "#4a5568", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 14 }}>Top scored conversations</div>
          {conversations.slice(0, 15).map(c => (
            <div key={c.conversation_id} onClick={() => router.push(`/insights/${id}?conv=${c.conversation_id}`)}
              style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 12px", background: "#0f1117", borderRadius: 8, marginBottom: 6, cursor: "pointer", border: "1px solid #1a2030" }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = brandColor; e.currentTarget.style.background = "#1a1f35"; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = "#1a2030"; e.currentTarget.style.background = "#0f1117"; }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                  <span style={{ fontSize: 11, color: "#4a5568", fontFamily: "monospace" }}>{c.conversation_id.slice(0, 16)}...</span>
                  <Badge color="gray" text={`score ${c.score}`} />
                  {c.flags?.frustration && <Badge color="red" text="frustration" />}
                  {c.flags?.hallucination && <Badge color="purple" text="hallucination" />}
                  {c.flags?.low_quality_response && <Badge color="amber" text="low quality" />}
                  {c.flags?.irrelevant_product && <Badge color="amber" text="irrelevant product" />}
                </div>
                <div style={{ fontSize: 11, color: "#4a5568", marginTop: 4, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: "90%" }}>
                  {c.preview || "No preview available"}
                </div>
              </div>
              <span style={{ color: "#4a5568", fontSize: 18, marginLeft: 8 }}>›</span>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}