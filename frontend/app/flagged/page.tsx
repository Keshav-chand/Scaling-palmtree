"use client";
import { useEffect, useState, useRef } from "react";
import { getFlagged, getConversationDetail, BRAND_COLORS } from "@/lib/api";
import { Sidebar, Badge } from "@/app/page";

const FLAG_COLORS: Record<string, string> = {
  frustration: "#f87171",
  hallucination: "#c084fc",
  irrelevant_product: "#fbbf24",
  unanswered_question: "#38bdf8",
  context_ignored: "#fb923c",
};

const FLAG_BG: Record<string, string> = {
  frustration: "#2d0f0f",
  hallucination: "#150d2d",
  irrelevant_product: "#1f1500",
  unanswered_question: "#0a1a24",
  context_ignored: "#241200",
};

const FLAG_BORDER: Record<string, string> = {
  frustration: "#7f1d1d",
  hallucination: "#4c1d95",
  irrelevant_product: "#78350f",
  unanswered_question: "#075985",
  context_ignored: "#7c2d12",
};

const FLAG_LABELS: Record<string, string> = {
  frustration: "Frustration",
  hallucination: "Hallucination",
  irrelevant_product: "Irrelevant Product",
  unanswered_question: "Unanswered Question",
  context_ignored: "Context Ignored",
};

export default function FlaggedPage() {
  const [flagged, setFlagged] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [threadData, setThreadData] = useState<Record<string, any>>({});
  const [loadingThread, setLoadingThread] = useState<string | null>(null);
  const firstFlagRefs = useRef<Record<string, HTMLDivElement | null>>({});

  useEffect(() => {
    getFlagged().then(data => {
      data.sort((a: any, b: any) => b.flag_count - a.flag_count || b.score - a.score);
      setFlagged(data);
      setLoading(false);
    });
  }, []);

  const handleExpand = async (convId: string) => {
    if (expanded === convId) { setExpanded(null); return; }
    setExpanded(convId);
    if (!threadData[convId]) {
      setLoadingThread(convId);
      try {
        const detail = await getConversationDetail(convId);
        setThreadData(prev => ({ ...prev, [convId]: detail }));
        setTimeout(() => {
          firstFlagRefs.current[convId]?.scrollIntoView({ behavior: "smooth", block: "center" });
        }, 150);
      } finally {
        setLoadingThread(null);
      }
    } else {
      setTimeout(() => {
        firstFlagRefs.current[convId]?.scrollIntoView({ behavior: "smooth", block: "center" });
      }, 100);
    }
  };

  if (loading) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", color: "#4a5568" }}>
      Loading...
    </div>
  );

  if (flagged.length === 0) return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar active="flagged" />
      <main style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ textAlign: "center", color: "#4a5568" }}>
          <div style={{ fontSize: 16, marginBottom: 8, color: "#34d399" }}>✓ No issues detected</div>
          <div style={{ fontSize: 12 }}>All conversations are clean</div>
        </div>
      </main>
    </div>
  );

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar active="flagged" />
      <main style={{ flex: 1, padding: "28px 32px", overflowY: "auto" }}>

        <div style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: 20, fontWeight: 600, color: "#e2e8f0" }}>Issues</h1>
          <p style={{ fontSize: 12, color: "#4a5568", marginTop: 4 }}>
            {flagged.length} conversations with detected issues · sorted by severity
          </p>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {flagged.map(c => {
            const isExpanded = expanded === c.conversation_id;
            const thread = threadData[c.conversation_id];
            const isLoading = loadingThread === c.conversation_id;
            const brandColor = BRAND_COLORS[c.widgetId] || "#818cf8";
            let firstFlagSet = false;

            return (
              <div key={c.conversation_id} style={{
                background: "#161b27", borderRadius: 10,
                border: `1px solid ${isExpanded ? brandColor : "#1e2535"}`,
                overflow: "hidden", transition: "border-color 0.15s",
              }}>

                {/* Card header */}
                <div
                  onClick={() => handleExpand(c.conversation_id)}
                  style={{ padding: "14px 16px", cursor: "pointer" }}
                  onMouseEnter={e => { if (!isExpanded) e.currentTarget.style.background = "#1a1f35"; }}
                  onMouseLeave={e => { if (!isExpanded) e.currentTarget.style.background = "transparent"; }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
                        <div style={{ width: 7, height: 7, borderRadius: "50%", background: brandColor }} />
                        <span style={{ fontSize: 11.5, color: brandColor, fontWeight: 600 }}>{c.brand_name}</span>
                      </div>
                      <span style={{ fontSize: 10.5, color: "#4a5568", fontFamily: "monospace" }}>
                        {c.conversation_id.slice(0, 16)}...
                      </span>
                      <span style={{
                        fontSize: 10, fontWeight: 700, color: "#e2e8f0",
                        background: "#2d3748", border: "1px solid #4a5568",
                        padding: "2px 8px", borderRadius: 20,
                      }}>
                        {c.flag_count} issue{c.flag_count > 1 ? "s" : ""} detected
                      </span>
                      <Badge color="gray" text={`score ${c.score}`} />
                      {c.flag_types?.includes("frustration") && <Badge color="red" text="frustration" />}
                      {c.flag_types?.includes("hallucination") && <Badge color="purple" text="hallucination" />}
                      {c.flag_types?.includes("irrelevant_product") && <Badge color="amber" text="irrelevant product" />}
                      {c.flag_types?.includes("unanswered_question") && <Badge color="blue" text="unanswered question" />}
                      {c.flag_types?.includes("context_ignored") && <Badge color="orange" text="context ignored" />}
                    </div>
                    <span style={{ color: "#4a5568", fontSize: 12, flexShrink: 0 }}>
                      {isExpanded ? "▲ collapse" : "▼ view thread"}
                    </span>
                  </div>

                  {/* Flag cards */}
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    {c.flags.map((flag: any, i: number) => {
                      const isUserFlag = flag.type === "frustration";
                      const senderLabel = isUserFlag ? "Customer" : "Assistant";
                      const fc = FLAG_COLORS[flag.type] || "#a0aec0";
                      const fb = FLAG_BG[flag.type] || "#1a1f3d";
                      const fbr = FLAG_BORDER[flag.type] || "#2d3748";

                      return (
                        <div key={i} style={{
                          background: "#0f1117",
                          borderLeft: `3px solid ${fc}`,
                          borderRadius: "0 6px 6px 0",
                          padding: "10px 12px",
                        }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 7 }}>
                            <span style={{ fontSize: 9.5, fontWeight: 700, color: fc, textTransform: "uppercase", letterSpacing: "0.06em" }}>
                              {FLAG_LABELS[flag.type] || flag.type}
                            </span>
                            <span style={{ fontSize: 10, color: "#4a5568" }}>
                              · {senderLabel} · msg #{flag.message_id}
                            </span>
                          </div>
                          {flag.message_text && (
                            <div style={{
                              fontSize: 12, color: "#e2e8f0",
                              background: fb, border: `1px solid ${fbr}`,
                              borderRadius: 6, padding: "7px 10px",
                              marginBottom: 7, lineHeight: 1.5, wordBreak: "break-word",
                            }}>
                              {flag.message_text}
                            </div>
                          )}
                          <div style={{ fontSize: 11, color: fc, opacity: 0.85, fontStyle: "italic" }}>
                            → {flag.reason}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Expanded full thread */}
                {isExpanded && (
                  <div style={{ borderTop: "1px solid #1e2535", padding: "16px" }}>
                    {isLoading ? (
                      <div style={{ color: "#4a5568", fontSize: 12, textAlign: "center", padding: "20px 0" }}>
                        Loading conversation...
                      </div>
                    ) : thread ? (
                      <>
                        {/* Page context strip */}
                        {thread.page_context?.length > 0 && (
                          <div style={{ marginBottom: 12, padding: "8px 10px", background: "#0f1a2d", borderRadius: 6, border: "1px solid #1e3a5f" }}>
                            <div style={{ fontSize: 10, color: "#4a5568", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>Pages viewed</div>
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

                        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
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
                            const isFlagged = !!flag;
                            const fc = FLAG_COLORS[flagType] || "#a0aec0";
                            const fb = FLAG_BG[flagType] || (isUser ? "#1e2535" : "#1a1f3d");
                            const fbr = FLAG_BORDER[flagType] || "#2d3748";

                            let isFirstFlag = false;
                            if (isFlagged && !firstFlagSet) {
                              isFirstFlag = true;
                              firstFlagSet = true;
                            }

                            return (
                              <div
                                key={idx}
                                ref={isFirstFlag ? (el) => { firstFlagRefs.current[c.conversation_id] = el; } : undefined}
                                style={{ display: "flex", flexDirection: "column", alignItems: isUser ? "flex-start" : "flex-end" }}
                              >
                                <div style={{ fontSize: 10, color: "#4a5568", marginBottom: 3, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                                  {isUser ? "Customer" : "Assistant"}
                                </div>
                                <div style={{
                                  background: isFlagged ? fb : (isUser ? "#1e2535" : "#1a1f3d"),
                                  border: `1px solid ${isFlagged ? fbr : "#2d3748"}`,
                                  borderRadius: 8, padding: "10px 14px",
                                  maxWidth: "75%", fontSize: 12.5,
                                  color: isFlagged ? "#e2e8f0" : "#a0aec0",
                                  lineHeight: 1.6, wordBreak: "break-word",
                                  boxShadow: isFlagged ? `0 0 0 1px ${fc}33` : "none",
                                }}>
                                  {(msg.text || "(empty)").replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').replace(/\*\*/g, '')}
                                </div>
                                {flag && (
                                  <div style={{ marginTop: 5, display: "flex", flexDirection: "column", gap: 3, alignItems: isUser ? "flex-start" : "flex-end" }}>
                                    <span style={{
                                      fontSize: 10, fontWeight: 700, color: fc,
                                      background: fb, border: `1px solid ${fbr}`,
                                      padding: "2px 8px", borderRadius: 4,
                                      letterSpacing: "0.05em", textTransform: "uppercase",
                                    }}>
                                      {FLAG_LABELS[flagType] || flagType}
                                    </span>
                                    <div style={{ fontSize: 11, color: fc, maxWidth: "75%", fontStyle: "italic", opacity: 0.9 }}>
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