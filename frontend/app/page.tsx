"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getBrands, BRAND_NAMES, BRAND_COLORS } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

export default function Home() {
  const [brands, setBrands] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    getBrands().then(data => { setBrands(data); setLoading(false); });
  }, []);

  if (loading) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", color: "#4a5568" }}>
      Loading...
    </div>
  );

  const dropOffData = brands.map(b => ({
    name: BRAND_NAMES[b.widgetId]?.split("—")[1]?.trim() || b.widgetId.slice(0, 8),
    value: b.drop_off_pct,
    color: BRAND_COLORS[b.widgetId],
  }));

  const frustrationData = brands.map(b => ({
    name: BRAND_NAMES[b.widgetId]?.split("—")[1]?.trim() || b.widgetId.slice(0, 8),
    value: b.frustration_pct,
    color: BRAND_COLORS[b.widgetId],
  }));

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar active="overview" />
      <main style={{ flex: 1, padding: "28px 32px", overflowY: "auto" }}>
        <div style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: 20, fontWeight: 600, color: "#e2e8f0" }}>Brand performance overview</h1>
          <p style={{ fontSize: 12, color: "#4a5568", marginTop: 4 }}>3 brands · 298 conversations analysed · 45 insights generated</p>
        </div>

        {/* Top metric cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 24 }}>
          {[
            { label: "Total conversations", value: "298", color: "#818cf8" },
            { label: "Avg frustration", value: "6.7%", color: "#fbbf24" },
            { label: "Avg drop-off", value: "10.4%", color: "#f87171" },
            { label: "Insights generated", value: "45", color: "#34d399" },
          ].map(m => (
            <div key={m.label} style={{ background: "#161b27", border: "1px solid #1e2535", borderRadius: 10, padding: "14px 16px" }}>
              <div style={{ fontSize: 11, color: "#4a5568", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 8 }}>{m.label}</div>
              <div style={{ fontSize: 24, fontWeight: 600, color: m.color }}>{m.value}</div>
            </div>
          ))}
        </div>

        {/* Brand cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 14, marginBottom: 24 }}>
          {brands.map(b => (
            <div key={b.widgetId} onClick={() => router.push(`/brand/${b.widgetId}`)}
              style={{ background: "#161b27", border: "1px solid #1e2535", borderRadius: 10, padding: 18, cursor: "pointer", transition: "border-color 0.15s" }}
              onMouseEnter={e => (e.currentTarget.style.borderColor = BRAND_COLORS[b.widgetId])}
              onMouseLeave={e => (e.currentTarget.style.borderColor = "#1e2535")}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                <div style={{ width: 8, height: 8, borderRadius: "50%", background: BRAND_COLORS[b.widgetId] }} />
                <span style={{ fontSize: 13, fontWeight: 600, color: "#e2e8f0" }}>{BRAND_NAMES[b.widgetId]}</span>
              </div>
              <div style={{ fontSize: 28, fontWeight: 700, color: b.frustration_pct > 8 ? "#f87171" : b.frustration_pct > 4 ? "#fbbf24" : "#34d399" }}>
                {b.frustration_pct}%
              </div>
              <div style={{ fontSize: 11, color: "#4a5568", marginBottom: 10 }}>frustration rate</div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <Badge color={b.drop_off_pct > 10 ? "amber" : "green"} text={`${b.drop_off_pct}% drop-off`} />
                <Badge color="blue" text={`${b.total_conversations} convos`} />
              </div>
              <div style={{ height: 3, background: "#1e2535", borderRadius: 2, marginTop: 14, overflow: "hidden" }}>
                <div style={{ height: "100%", width: `${b.frustration_pct * 5}%`, background: BRAND_COLORS[b.widgetId], borderRadius: 2 }} />
              </div>
            </div>
          ))}
        </div>

        {/* Comparison table */}
        <div style={{ background: "#161b27", border: "1px solid #1e2535", borderRadius: 10, padding: 20, marginBottom: 20 }}>
          <div style={{ fontSize: 11, color: "#4a5568", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 14 }}>Brand comparison</div>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12.5 }}>
            <thead>
              <tr>
                {["Brand", "Conversations", "Drop-off %", "Frustration %", "Hallucination %", "Avg messages", "Avg duration", "Status"].map(h => (
                  <th key={h} style={{ textAlign: "left", color: "#4a5568", fontWeight: 500, padding: "8px 10px", borderBottom: "1px solid #1e2535", fontSize: 11, textTransform: "uppercase" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {brands.map(b => (
                <tr key={b.widgetId} onClick={() => router.push(`/brand/${b.widgetId}`)}
                  style={{ cursor: "pointer" }}
                  onMouseEnter={e => Array.from(e.currentTarget.cells).forEach(c => (c.style.background = "#1e2535"))}
                  onMouseLeave={e => Array.from(e.currentTarget.cells).forEach(c => (c.style.background = "transparent"))}>
                  <td style={{ padding: "10px", borderBottom: "1px solid #1a2030", color: "#e2e8f0", fontWeight: 500 }}>{BRAND_NAMES[b.widgetId]}</td>
                  <td style={{ padding: "10px", borderBottom: "1px solid #1a2030", color: "#a0aec0" }}>{b.total_conversations}</td>
                  <td style={{ padding: "10px", borderBottom: "1px solid #1a2030" }}><Badge color={b.drop_off_pct > 10 ? "amber" : "green"} text={`${b.drop_off_pct}%`} /></td>
                  <td style={{ padding: "10px", borderBottom: "1px solid #1a2030" }}><Badge color={b.frustration_pct > 8 ? "red" : b.frustration_pct > 4 ? "amber" : "green"} text={`${b.frustration_pct}%`} /></td>
                  <td style={{ padding: "10px", borderBottom: "1px solid #1a2030", color: "#a0aec0" }}>{b.hallucination_pct}%</td>
                  <td style={{ padding: "10px", borderBottom: "1px solid #1a2030", color: "#a0aec0" }}>{b.avg_messages}</td>
                  <td style={{ padding: "10px", borderBottom: "1px solid #1a2030", color: "#a0aec0" }}>{b.avg_duration_seconds}s</td>
                  <td style={{ padding: "10px", borderBottom: "1px solid #1a2030" }}>
                    <Badge color={b.frustration_pct > 8 ? "red" : b.drop_off_pct > 10 ? "amber" : "green"}
                      text={b.frustration_pct > 8 ? "High frustration" : b.drop_off_pct > 10 ? "Needs attention" : "Best performing"} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Charts */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          <ChartCard title="Drop-off % by brand" data={dropOffData} />
          <ChartCard title="Frustration % by brand" data={frustrationData} />
        </div>
      </main>
    </div>
  );
}

function ChartCard({ title, data }: { title: string; data: any[] }) {
  return (
    <div style={{ background: "#161b27", border: "1px solid #1e2535", borderRadius: 10, padding: 20 }}>
      <div style={{ fontSize: 11, color: "#4a5568", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 14 }}>{title}</div>
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={data} barSize={32}>
          <XAxis dataKey="name" tick={{ fill: "#4a5568", fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: "#4a5568", fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={{ background: "#161b27", border: "1px solid #1e2535", borderRadius: 8, color: "#e2e8f0", fontSize: 12 }} />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((d, i) => <Cell key={i} fill={d.color} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function Badge({ color, text }: { color: string; text: string }) {
  const colors: Record<string, { bg: string; fg: string }> = {
    red: { bg: "#3b1515", fg: "#f87171" },
    amber: { bg: "#2d2010", fg: "#fbbf24" },
    green: { bg: "#0d2b1e", fg: "#34d399" },
    blue: { bg: "#1a1f3d", fg: "#818cf8" },
    purple: { bg: "#1e1535", fg: "#c084fc" },
    gray: { bg: "#1e2535", fg: "#718096" },
  };
  const c = colors[color] || colors.gray;
  return (
    <span style={{ display: "inline-block", padding: "2px 8px", borderRadius: 20, fontSize: 10.5, fontWeight: 500, background: c.bg, color: c.fg }}>
      {text}
    </span>
  );
}

export function Sidebar({ active }: { active: string }) {
  const router = useRouter();
  const items = [
    { key: "overview", label: "All brands", path: "/", dot: "#818cf8", section: "Overview" },
    { key: "brand-a", label: "Blue Nectar — Wellness", path: "/brand/680a0a8b70a26f7a0e24eedd", dot: "#f87171", section: "Brands" },
    { key: "brand-b", label: "Blue Nectar — Skincare", path: "/brand/6983153e1497a62e8542a0ad", dot: "#fbbf24", section: null },
    { key: "brand-c", label: "Sri Sri Tattva", path: "/brand/69a92ad76dcbf2da868e0f9b", dot: "#34d399", section: null },
    { key: "insights-a", label: "Blue Nectar — Wellness", path: "/insights/680a0a8b70a26f7a0e24eedd", dot: "#f87171", section: "Insights" },
    { key: "insights-b", label: "Blue Nectar — Skincare", path: "/insights/6983153e1497a62e8542a0ad", dot: "#fbbf24", section: null },
    { key: "insights-c", label: "Sri Sri Tattva", path: "/insights/69a92ad76dcbf2da868e0f9b", dot: "#34d399", section: null },
  ];

  return (
    <aside style={{ width: 210, minWidth: 210, background: "#161b27", borderRight: "1px solid #1e2535", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "18px 16px 14px", borderBottom: "1px solid #1e2535" }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: "#e2e8f0" }}>Helio Analysis</div>
        <div style={{ fontSize: 11, color: "#4a5568", marginTop: 3 }}>AI assistant insights</div>
      </div>
      {items.map(item => (
        <div key={item.key}>
          {item.section && (
            <div style={{ fontSize: 10, color: "#4a5568", padding: "14px 16px 6px", textTransform: "uppercase", letterSpacing: "0.08em" }}>{item.section}</div>
          )}
          <div onClick={() => router.push(item.path)}
            style={{ padding: "7px 16px", fontSize: 12.5, color: active === item.key ? "#818cf8" : "#718096", cursor: "pointer", borderLeft: active === item.key ? "2px solid #818cf8" : "2px solid transparent", background: active === item.key ? "#1e2535" : "transparent", transition: "all 0.15s" }}
            onMouseEnter={e => { if (active !== item.key) { e.currentTarget.style.color = "#e2e8f0"; e.currentTarget.style.background = "#1e2535"; } }}
            onMouseLeave={e => { if (active !== item.key) { e.currentTarget.style.color = "#718096"; e.currentTarget.style.background = "transparent"; } }}>
            <span style={{ display: "inline-block", width: 6, height: 6, borderRadius: "50%", background: item.dot, marginRight: 8, verticalAlign: "middle" }} />
            {item.label}
          </div>
        </div>
      ))}
    </aside>
  );
}