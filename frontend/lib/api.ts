import axios from "axios";

const BASE = "http://localhost:8000";

export const BRAND_NAMES: Record<string, string> = {
  "680a0a8b70a26f7a0e24eedd": "Blue Nectar — Wellness",
  "6983153e1497a62e8542a0ad": "Blue Nectar — Skincare",
  "69a92ad76dcbf2da868e0f9b": "Sri Sri Tattva",
};

export const BRAND_COLORS: Record<string, string> = {
  "680a0a8b70a26f7a0e24eedd": "#f87171",
  "6983153e1497a62e8542a0ad": "#fbbf24",
  "69a92ad76dcbf2da868e0f9b": "#34d399",
};

export const getBrands = () => axios.get(`${BASE}/brands`).then(r => r.data);
export const getMetrics = (id: string) => axios.get(`${BASE}/metrics/${id}`).then(r => r.data);
export const getConversations = (id: string) => axios.get(`${BASE}/conversations/${id}`).then(r => r.data);
export const getInsights = (id: string) => axios.get(`${BASE}/insights/${id}`).then(r => r.data);