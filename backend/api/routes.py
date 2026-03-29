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

    # Intent distribution for this brand
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