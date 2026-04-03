import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load all precomputed data once at startup
def load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return {}

brand_metrics = load("data/brand_metrics.json")
scored = load("data/scored.json")
intents = load("data/intents.json")
insights = load("data/insights.json")
processed = load("data/processed_data.json")

# Index conversations by id for fast lookup
conv_by_id = {c["conversation_id"]: c for c in processed}

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

    return {
        **brand_metrics[brand],
        "intent_distribution": intent_counts
    }

@app.get("/conversations/{brand}")
def get_conversations(brand: str):
    brand_scored = [s for s in scored if s["widgetId"] == brand]
    result = []
    for s in brand_scored[:50]:
        cid = s["conversation_id"]
        conv = conv_by_id.get(cid, {})
        result.append({
            "conversation_id": cid,
            "score": s["score"],
            "flags": s["flags"],
            "message_count": len(conv.get("messages", [])),
            "preview": conv.get("messages", [{}])[0].get("text", "")[:100] if conv.get("messages") else ""
        })
    return result

@app.get("/insights/{brand}")
def get_insights(brand: str):
    if brand not in insights:
        return []
    return insights[brand]


# ─── CROSS-BRAND FINDING ENDPOINT ────────────────────────────────────────────

CONFUSION_PATTERNS = [
    "confused between",
    "difference between",
    "which one",
    "which is better",
    "cant decide",
    "can't decide",
    "not sure which",
    "help me choose",
    "confused",
]

FRUSTRATION_KEYWORDS = [
    "wrong", "not working", "useless", "frustrated", "confused",
    "makes no sense", "not helpful", "doesnt help", "doesn't help",
    "please help", "not what i asked", "already asked", "give up",
]

@app.get("/cross-brand")
def get_cross_brand():
    results = []
    scored_by_id = {s["conversation_id"]: s for s in scored}

    for conv in processed:
        messages = conv.get("messages", [])
        user_messages = [m for m in messages if m.get("sender") == "user" and m.get("text")]
        full_user_text = " ".join(m["text"].lower() for m in user_messages)

        matched = [p for p in CONFUSION_PATTERNS if p in full_user_text]
        if not matched:
            continue

        score_data = scored_by_id.get(conv["conversation_id"], {})
        flags = score_data.get("flags", {})

        # Tag each message with relevant flags
        tagged_messages = []
        for m in messages:
            text = m.get("text", "")
            tags = []
            text_lower = text.lower()

            if m.get("sender") == "user":
                if any(p in text_lower for p in CONFUSION_PATTERNS):
                    tags.append("confusion")
                if any(kw in text_lower for kw in FRUSTRATION_KEYWORDS):
                    tags.append("frustration")

            # Strip raw JSON metadata that appears after "End of stream"
            clean_text = text.split("End of stream")[0].strip()

            tagged_messages.append({
                "sender": m.get("sender"),
                "text": clean_text,
                "timestamp": m.get("timestamp"),
                "tags": tags,
            })

        results.append({
            "conversation_id": conv["conversation_id"],
            "widgetId": conv["widgetId"],
            "matched_patterns": matched,
            "frustration": flags.get("frustration", False),
            "hallucination": flags.get("hallucination", False),
            "low_quality": flags.get("low_quality_response", False),
            "score": score_data.get("score", 0),
            "messages": tagged_messages,
        })

    # Sort: frustrated first, then by score descending
    results.sort(key=lambda x: (not x["frustration"], -x["score"]))

    frustrated = [r for r in results if r["frustration"]]
    not_frustrated = [r for r in results if not r["frustration"]]

    avg_frustrated_score = round(
        sum(r["score"] for r in frustrated) / len(frustrated), 1
    ) if frustrated else 0

    avg_normal_score = round(
        sum(r["score"] for r in not_frustrated) / len(not_frustrated), 1
    ) if not_frustrated else 0

    return {
        "summary": {
            "total_matched": len(results),
            "frustrated_count": len(frustrated),
            "avg_frustrated_score": avg_frustrated_score,
            "avg_normal_score": avg_normal_score,
            "pattern": "Users expressing confusion or comparison intent consistently score higher on frustration",
            "reason": "The assistant treats comparison queries as standard product queries instead of guiding users through a structured decision",
            "recommendation": "Add a dedicated comparison mode that presents products side by side with key differentiators highlighted, and detects confusion intent to trigger guided decision flows",
        },
        "conversations": results,
    }