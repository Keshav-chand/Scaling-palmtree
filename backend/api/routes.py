import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


brand_metrics = load("data/brand_metrics.json")
scored = load("data/scored.json")
intents = load("data/intents.json")
insights = load("data/insights.json")
processed = load("data/processed_data.json")

conv_by_id = {c["conversation_id"]: c for c in processed}
scored_by_id = {s["conversation_id"]: s for s in scored}

BRAND_NAMES_MAP = {
    "680a0a8b70a26f7a0e24eedd": "Blue Nectar — Wellness",
    "6983153e1497a62e8542a0ad": "Blue Nectar — Skincare",
    "69a92ad76dcbf2da868e0f9b": "Sri Sri Tattva",
}


def build_messages_with_flags(conv, flags):
    flag_by_mid = {f["message_id"]: f for f in flags}
    messages = []
    for i, m in enumerate(conv.get("messages", [])):
        text = (m.get("text") or "").split("End of stream")[0].strip()
        flag_data = flag_by_mid.get(i)
        messages.append({
            "message_id": i,
            "sender": m.get("sender"),
            "text": text,
            "timestamp": m.get("timestamp"),
            "flag": {"type": flag_data["type"], "reason": flag_data["reason"]} if flag_data else None,
        })
    return messages


@app.get("/brands")
def get_brands():
    return [
        {
            "widgetId": wid,
            "total_conversations": m["total_conversations"],
            "drop_off_pct": m["drop_off_pct"],
            "frustration_pct": m["frustration_pct"],
            "hallucination_pct": m["hallucination_pct"],
            "avg_messages": m["avg_messages"],
            "avg_duration_seconds": m["avg_duration_seconds"],
        }
        for wid, m in brand_metrics.items()
    ]


@app.get("/metrics/{brand}")
def get_metrics(brand: str):
    if brand not in brand_metrics:
        raise HTTPException(status_code=404, detail="Brand not found")
    brand_convs = [c for c in processed if c["widgetId"] == brand]
    intent_counts = {}
    for c in brand_convs:
        intent = intents.get(c["conversation_id"], "other")
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
    return {**brand_metrics[brand], "intent_distribution": intent_counts}


@app.get("/conversations/{brand}")
def get_conversations(brand: str):
    brand_scored = [s for s in scored if s["widgetId"] == brand]
    brand_scored.sort(key=lambda x: (-len(x.get("flags", [])), -x["score"]))

    result = []
    for s in brand_scored[:50]:
        cid = s["conversation_id"]
        conv = conv_by_id.get(cid, {})
        flags = s.get("flags", [])
        messages = conv.get("messages", [])
        result.append({
            "conversation_id": cid,
            "score": s["score"],
            "has_flags": len(flags) > 0,
            "flag_count": len(flags),
            "flag_types": list({f["type"] for f in flags}),
            "flags": flags,
            "message_count": len(messages),
            "preview": messages[0].get("text", "")[:120] if messages else "",
        })
    return result


@app.get("/conversation/{conversation_id}")
def get_conversation_detail(conversation_id: str):
    conv = conv_by_id.get(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    score_data = scored_by_id.get(conversation_id, {})
    flags = score_data.get("flags", [])

    return {
        "conversation_id": conversation_id,
        "widgetId": conv.get("widgetId"),
        "score": score_data.get("score", 0),
        "flags": flags,
        "messages": build_messages_with_flags(conv, flags),
    }


@app.get("/insights/{brand}")
def get_insights(brand: str):
    if brand not in insights:
        return []
    brand_insights = insights[brand]
    for item in brand_insights:
        cid = item.get("conversation_id")
        if cid and cid in scored_by_id:
            item["flags"] = scored_by_id[cid].get("flags", [])
            item["score"] = scored_by_id[cid].get("score", 0)
    return brand_insights

#flagged updates
@app.get("/flagged")
def get_flagged():
    results = []
    for s in scored:
        flags = s.get("flags", [])
        if not flags:
            continue
        cid = s["conversation_id"]
        wid = s["widgetId"]
        conv = conv_by_id.get(cid, {})
        messages = conv.get("messages", [])

        # Attach actual message text to each flag
        enriched_flags = []
        for f in flags:
            mid = f.get("message_id")
            msg_text = ""
            if mid is not None and mid < len(messages):
                raw = (messages[mid].get("text") or "").split("End of stream")[0].strip()
                # Strip markdown
                import re
                raw = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', raw)
                raw = raw.replace("**", "")
                msg_text = raw[:300]
            enriched_flags.append({
                **f,
                "message_text": msg_text,
            })

        preview = messages[0].get("text", "")[:120] if messages else ""
        results.append({
            "conversation_id": cid,
            "widgetId": wid,
            "brand_name": BRAND_NAMES_MAP.get(wid, wid[:8]),
            "score": s["score"],
            "flag_count": len(flags),
            "flag_types": list({f["type"] for f in flags}),
            "flags": enriched_flags,
            "preview": preview,
        })

    results.sort(key=lambda x: (-x["flag_count"], -x["score"]))
    return results

#consfusion updates
CONFUSION_PATTERNS = [
    "confused between", "difference between", "which one",
    "which is better", "cant decide", "can't decide",
    "not sure which", "help me choose", "confused",
]


@app.get("/cross-brand")
def get_cross_brand():
    results = []
    for conv in processed:
        messages = conv.get("messages", [])
        user_text = " ".join(
            m["text"].lower() for m in messages
            if m.get("sender") == "user" and m.get("text")
        )
        matched = [p for p in CONFUSION_PATTERNS if p in user_text]
        if not matched:
            continue

        score_data = scored_by_id.get(conv["conversation_id"], {})
        flags = score_data.get("flags", [])
        flag_types = {f["type"] for f in flags}

        results.append({
            "conversation_id": conv["conversation_id"],
            "widgetId": conv["widgetId"],
            "matched_patterns": matched,
            "has_frustration": "frustration" in flag_types,
            "has_hallucination": "hallucination" in flag_types,
            "flag_count": len(flags),
            "score": score_data.get("score", 0),
            "messages": build_messages_with_flags(conv, flags),
        })

    results.sort(key=lambda x: (-x["flag_count"], -x["score"]))
    frustrated = [r for r in results if r["has_frustration"]]
    not_frustrated = [r for r in results if not r["has_frustration"]]

    return {
        "summary": {
            "total_matched": len(results),
            "frustrated_count": len(frustrated),
            "avg_frustrated_score": round(sum(r["score"] for r in frustrated) / len(frustrated), 1) if frustrated else 0,
            "avg_normal_score": round(sum(r["score"] for r in not_frustrated) / len(not_frustrated), 1) if not_frustrated else 0,
            "pattern": "Users expressing confusion or comparison intent consistently score higher on frustration",
            "reason": "The assistant treats comparison queries as standard product queries instead of guiding users through a structured decision",
            "recommendation": "Add a dedicated comparison mode that presents products side by side with key differentiators highlighted",
        },
        "conversations": results,
    }