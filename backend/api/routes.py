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

conv_by_id = {c["conversation_id"]: c for c in processed}
scored_by_id = {s["conversation_id"]: s for s in scored}

FRUSTRATION_KEYWORDS = [
    "wrong", "not working", "useless", "bad", "terrible", "worst",
    "disappointed", "frustrated", "broken", "again", "still", "never",
    "waste", "pathetic", "ridiculous", "unacceptable",
    "not helpful", "doesn't help", "doesnt help", "not understanding",
    "please help", "no response", "wrong product", "not what i asked",
    "same question", "already asked", "told you", "as i said",
    "cannot", "can't find", "confused", "makes no sense",
    "not what i wanted", "irrelevant", "stop", "enough", "give up"
]

HALLUCINATION_CONTRADICTION_KEYWORDS = [
    "that's wrong", "thats wrong", "not correct",
    "that is wrong", "incorrect", "you said",
    "but you", "that's not", "thats not",
    "you mentioned", "not true", "false",
    "got vanished", "not available", "not showing",
    "doesn't exist", "doesnt exist", "not there",
    "disappeared", "no longer", "not live"
]

def tag_messages(messages):
    """
    Tag each message with relevant flags.
    - Frustration: detected on USER messages via keywords
    - Hallucination: detected on ASSISTANT messages that are immediately
      followed by a user contradiction. The assistant message is flagged,
      not the user message, because the assistant produced the wrong info.
    """
    tagged = []

    # First pass: find indices where user contradicts the assistant
    contradiction_indices = set()
    for i, m in enumerate(messages):
        if m.get("sender") == "user" and m.get("text"):
            text_lower = m["text"].lower()
            if any(kw in text_lower for kw in HALLUCINATION_CONTRADICTION_KEYWORDS):
                # Tag the previous assistant message as hallucination
                for j in range(i - 1, -1, -1):
                    if messages[j].get("sender") == "agent":
                        contradiction_indices.add(j)
                        break

    # Second pass: build tagged messages
    for i, m in enumerate(messages):
        text = m.get("text", "")
        text_lower = text.lower()
        tags = []
        why = None

        if m.get("sender") == "user":
            if any(kw in text_lower for kw in FRUSTRATION_KEYWORDS):
                tags.append("frustration")
                why = "User expressed frustration via negative language or repeated complaint"

        if m.get("sender") == "agent":
            if i in contradiction_indices:
                tags.append("hallucination")
                why = "The user contradicted this response in a follow-up message, indicating the assistant may have provided incorrect information"

        clean_text = text.split("End of stream")[0].strip()

        tagged.append({
            "sender": m.get("sender"),
            "text": clean_text,
            "timestamp": m.get("timestamp"),
            "tags": tags,
            "why": why,
        })

    return tagged


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


@app.get("/conversation/{conversation_id}")
def get_conversation_detail(conversation_id: str):
    conv = conv_by_id.get(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    score_data = scored_by_id.get(conversation_id, {})
    flags = score_data.get("flags", {})
    tagged = tag_messages(conv.get("messages", []))

    return {
        "conversation_id": conversation_id,
        "widgetId": conv.get("widgetId"),
        "score": score_data.get("score", 0),
        "flags": flags,
        "messages": tagged,
    }


@app.get("/insights/{brand}")
def get_insights(brand: str):
    if brand not in insights:
        return []
    brand_insights = insights[brand]
    for item in brand_insights:
        cid = item.get("conversation_id")
        if cid and cid in scored_by_id:
            item["flags"] = scored_by_id[cid].get("flags", item.get("flags", {}))
            item["score"] = scored_by_id[cid].get("score", item.get("score", 0))
    return brand_insights


# ─── CROSS-BRAND FINDING ENDPOINT ────────────────────────────────────────────

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
        user_messages = [m for m in messages if m.get("sender") == "user" and m.get("text")]
        full_user_text = " ".join(m["text"].lower() for m in user_messages)

        matched = [p for p in CONFUSION_PATTERNS if p in full_user_text]
        if not matched:
            continue

        score_data = scored_by_id.get(conv["conversation_id"], {})
        flags = score_data.get("flags", {})
        tagged = tag_messages(messages)

        results.append({
            "conversation_id": conv["conversation_id"],
            "widgetId": conv["widgetId"],
            "matched_patterns": matched,
            "frustration": flags.get("frustration", False),
            "hallucination": flags.get("hallucination", False),
            "low_quality": flags.get("low_quality_response", False),
            "score": score_data.get("score", 0),
            "messages": tagged,
        })

    results.sort(key=lambda x: (not x["frustration"], -x["score"]))
    frustrated = [r for r in results if r["frustration"]]
    not_frustrated = [r for r in results if not r["frustration"]]

    return {
        "summary": {
            "total_matched": len(results),
            "frustrated_count": len(frustrated),
            "avg_frustrated_score": round(sum(r["score"] for r in frustrated) / len(frustrated), 1) if frustrated else 0,
            "avg_normal_score": round(sum(r["score"] for r in not_frustrated) / len(not_frustrated), 1) if not_frustrated else 0,
            "pattern": "Users expressing confusion or comparison intent consistently score higher on frustration",
            "reason": "The assistant treats comparison queries as standard product queries instead of guiding users through a structured decision",
            "recommendation": "Add a dedicated comparison mode that presents products side by side with key differentiators highlighted, and detects confusion intent to trigger guided decision flows",
        },
        "conversations": results,
    }