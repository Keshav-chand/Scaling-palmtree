"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getMetrics, getConversations, getConversationDetail, BRAND_NAMES, BRAND_COLORS } from "@/lib/api";
import { Sidebar, Badge } from "@/app/page";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

const FLAG_COLORS: Record<string, string> = {
  frustration: "#f87171",
  hallucination: "#c084fc",
  irrelevant_product: "#fbbf24",
  unanswered_question: "#38bdf8",
  context_ignored: "#fb923c",
};

const FLAG_BG: Record<string, string> = {
  frustration: "#3b1515",
  hallucination: "#1e1040",
  irrelevant_product: "#2d2000",
  unanswered_question: "#0c1f2d",
  context_ignored: "#2d1500",
};

const FLAG_LABELS: Record<string, string> = {
  frustration: "Frustration",
  hallucination: "Hallucination",
  irrelevant_product: "Irrelevant Product",
  unanswered_question: "Unanswered Question",
  context_ignored: "Context Ignored",
};

export default function BrandPage() {
  const { id } = useParams() as { id: string };
  const [metrics, setMetrics] = useState<any>(null);
  const [conversations, setConversations] = useState<any[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [threadData, setThreadData] = useState<Record<string, any>>({});
  const [loadingThread, setLoadingThread] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    getMetrics(id).then(setMetrics);
    getConversations(id).then(setConversations);
  }, [id]);

  const handleExpand = async (convId: string) => {
    if (expanded === convId) { setExpanded(null); return; }
    setExpanded(convId);
    if (!threadData[convId]) {
      setLoadingThread(convId);
      try {
        const detail = await getConversationDetail(convId);
        setThreadData(prev => ({ ...prev, [convId]: detail }));
      } catch (e) {
        console.error("Failed to load conversation", e);
      } finally {
        setLoadingThread(null);
      }
    }
  };

  if (!metrics) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", color: "#4a5568" }}>Loading...</div>
  );

  const brandColor = BRAND_COLORS[id] || "#818cf8";
  const brandName = BRAND_NAMES[id] || id.slice(0, 8);
  const activeKey = id === "680a0a8b70a26f7a0e24eedd" ? "brand-a" : id === "6983153e1497a62e8542a0ad" ? "brand-b" : "brand-c";
  const intentData = Object.entries(metrics.intent_distribution || {}).map(([name, value]) => ({ name, value }));
  const INTENT_COLORS = ["#818cf8", "#34d399", "#fbbf24", "#f87171", "#c084fc"];
  const flagData = [
    { name: "Frustration", value: metrics.frustration_count || 0, color: "#f87171" },
    { name: "Hallucination", value: metrics.hallucination_count || 0, color: "#c084fc" },
    { name: "Irrelevant Product", value: metrics.irrelevant_product_count || 0, color: "#fbbf24" },
    { name: "Unanswered Q", value: metrics.unanswered_question_count || 0, color: "#38bdf8" },
    { name: "Context Ignored", value: metrics.context_ignored_count || 0, color: "#fb923c" },
    { name: "Drop-offs", value: metrics.drop_offs || 0, color: "#818cf8" },
  ];

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar active={activeKey} />
      <main style={{ flex: 1, padding: "28px 32px", overflowY: "auto" }}>

        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ width: 10, height: 10, borderRadius: "50%", background: brandColor }} />
              <h1 style={{ fontSize: 20, fontWeight: 600, color: "#e2e8f0" }}>{brandName} — detailed analysis</h1>
            </div>
            <p style={{ fontSize: 12, color: "#4a5568", marginTop: 4 }}>widgetId: {id.slice(0, 8)}... · {metrics.total_conversations} conversations</p>
          </div>
          <button onClick={() => router.push(`/insights/${id}`)}
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
            { label: "Context ignored", value: `${metrics.context_ignored_pct || 0}%`, color: (metrics.context_ignored_pct || 0) > 8 ? "#fb923c" : "#fbbf24" },
          ].map(m => (
            <div key={m.label} style={{ background: "#161b27", border: "1px solid #1e2535", borderRadius: 10, padding: "14px 16px" }}>
              <div style={{ fontSize: 11, color: "#4a5568", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 8 }}>{m.label}</div>
              <div style={{ fontSize: 24, fontWeight: 600, color: m.color }}>{m.value}</div>
            </div>
          ))}
        </div>

        {/* Charts */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, marginBottom: 20 }}>
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

          <div style={{ background: "#161b27", border: "1px solid #1e2535", borderRadius: 10, padding: 20 }}>
            <div style={{ fontSize: 11, color: "#4a5568", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 14 }}>Flag breakdown</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {flagData.map(f => {
                const max = Math.max(...flagData.map(x => x.value)) || 1;
                return (
                  <div key={f.name} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}>
                    <div style={{ width: 110, color: "#718096", fontSize: 11 }}>{f.name}</div>
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
          <div style={{ fontSize: 11, color: "#4a5568", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 14 }}>
            Conversations — flagged sorted first · click to expand thread
          </div>

          {conversations.slice(0, 15).map(c => {
            const isExpanded = expanded === c.conversation_id;
            const thread = threadData[c.conversation_id];
            const isLoading = loadingThread === c.conversation_id;

            return (
              <div key={c.conversation_id} style={{
                background: "#0f1117",
                borderRadius: 8,
                marginBottom: 8,
                border: `1px solid ${isExpanded ? brandColor : c.has_flags ? "#2d2535" : "#1a2030"}`,
                overflow: "hidden",
                transition: "border-color 0.15s",
              }}>

                {/* Row header */}
                <div
                  onClick={() => handleExpand(c.conversation_id)}
                  style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 12px", cursor: "pointer" }}
                  onMouseEnter={e => { if (!isExpanded) e.currentTarget.style.background = "#1a1f35"; }}
                  onMouseLeave={e => { if (!isExpanded) e.currentTarget.style.background = "transparent"; }}
                >
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                      <span style={{ fontSize: 11, color: "#4a5568", fontFamily: "monospace" }}>{c.conversation_id.slice(0, 16)}...</span>
                      <Badge color="gray" text={`score ${c.score}`} />
                      {c.flag_types?.includes("frustration") && <Badge color="red" text="frustration" />}
                      {c.flag_types?.includes("hallucination") && <Badge color="purple" text="hallucination" />}
                      {c.flag_types?.includes("irrelevant_product") && <Badge color="amber" text="irrelevant product" />}
                      {c.flag_types?.includes("unanswered_question") && <Badge color="blue" text="unanswered question" />}
                      {c.flag_types?.includes("context_ignored") && <Badge color="orange" text="context ignored" />}
                      {!c.has_flags && <span style={{ fontSize: 10, color: "#4a5568", fontStyle: "italic" }}>no issues</span>}
                    </div>
                    <div style={{ fontSize: 11, color: "#4a5568", marginTop: 4, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: "90%" }}>
                      {c.preview || "No preview available"}
                    </div>
                  </div>
                  <span style={{ color: "#4a5568", fontSize: 13, marginLeft: 8, flexShrink: 0 }}>
                    {isExpanded ? "▲ collapse" : "▼ view thread"}
                  </span>
                </div>

                {/* Expanded thread */}
                {isExpanded && (
                  <div style={{ borderTop: "1px solid #1e2535", padding: "16px 14px" }}>
                    {isLoading ? (
                      <div style={{ color: "#4a5568", fontSize: 12, textAlign: "center", padding: "16px 0" }}>Loading conversation...</div>
                    ) : thread ? (
                      <>
                        {thread.flags.length === 0 && (
                          <div style={{ fontSize: 11, color: "#34d399", marginBottom: 12, padding: "6px 10px", background: "#0d2018", borderRadius: 6, border: "1px solid #1a3a28", display: "inline-block" }}>
                            ✓ No issues detected in this conversation
                          </div>
                        )}

                        {/* Page context strip */}
                        {thread.page_context?.length > 0 && (
                          <div style={{ marginBottom: 12, padding: "8px 10px", background: "#0f1a2d", borderRadius: 6, border: "1px solid #1e3a5f" }}>
                            <div style={{ fontSize: 10, color: "#4a5568", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>Pages viewed in this conversation</div>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                              {thread.page_context.map((p: any, i: number) => (
                                <span key={i} style={{
                                  fontSize: 10.5, color: "#38bdf8",
                                  background: "#0c1f2d", border: "1px solid #1e3a5f",
                                  borderRadius: 4, padding: "2px 7px",
                                }}>
                                  {p.label} <span style={{ color: "#4a5568" }}>({p.source})</span>
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                          {thread.messages.map((msg: any, idx: number) => {

                            // ── EVENT ROW ──
                            if (msg.kind === "event" || msg.sender === "event") {
                              return (
                                <div key={idx} style={{
                                  display: "flex", alignItems: "center", gap: 6,
                                  padding: "3px 10px", fontSize: 11,
                                  color: "#4a5568", fontStyle: "italic",
                                  borderLeft: "2px solid #1f2937",
                                }}>
                                  <span style={{ color: "#374151", fontSize: 10 }}>⬡</span>
                                  <span>[event] {msg.text}</span>
                                </div>
                              );
                            }

                            // ── MESSAGE ROW ──
                            const isUser = msg.sender === "user";
                            const flag = msg.flag;
                            const flagType = flag?.type;
                            const bgColor = flagType ? FLAG_BG[flagType] : (isUser ? "#1e2535" : "#1a1f3d");
                            const borderColor = flagType ? FLAG_COLORS[flagType] : "#2d3748";

                            return (
                              <div key={idx} style={{ display: "flex", flexDirection: "column", alignItems: isUser ? "flex-start" : "flex-end" }}>
                                <div style={{ fontSize: 10, color: "#4a5568", marginBottom: 3, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                                  {isUser ? "Customer" : "Assistant"}
                                </div>
                                <div style={{
                                  background: bgColor,
                                  border: `1px solid ${borderColor}`,
                                  borderRadius: 8, padding: "9px 13px",
                                  maxWidth: "75%", fontSize: 12.5,
                                  color: "#a0aec0", lineHeight: 1.6,
                                  wordBreak: "break-word",
                                }}>
                                  {msg.text || "(empty)"}
                                </div>
                                {flag && (
                                  <div style={{ marginTop: 5, alignItems: isUser ? "flex-start" : "flex-end", display: "flex", flexDirection: "column", gap: 3 }}>
                                    <span style={{
                                      fontSize: 10, fontWeight: 600,
                                      color: FLAG_COLORS[flagType],
                                      background: FLAG_BG[flagType],
                                      border: `1px solid ${FLAG_COLORS[flagType]}`,
                                      padding: "2px 8px", borderRadius: 4,
                                      letterSpacing: "0.04em", textTransform: "uppercase",
                                    }}>
                                      {FLAG_LABELS[flagType]}
                                    </span>
                                    <div style={{ fontSize: 10.5, color: FLAG_COLORS[flagType], maxWidth: "75%", fontStyle: "italic", opacity: 0.85 }}>
                                      {flag.reason}
                                    </div>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </>
                    ) : (
                      <div style={{ color: "#4a5568", fontSize: 12 }}>Failed to load conversation.</div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
}