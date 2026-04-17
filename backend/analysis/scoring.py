FLAG_WEIGHTS = {
    "frustration": 40,
    "hallucination": 30,
    "irrelevant_product": 20,
}


def score_conversation(llm_result):
    score = 0
    for flag in llm_result.get("flags", []):
        score += FLAG_WEIGHTS.get(flag["type"], 0)
    return round(min(score, 100), 2)


def rank_conversations(llm_flags):
    scored = []
    for item in llm_flags:
        scored.append({
            "conversation_id": item["conversation_id"],
            "widgetId": item["widgetId"],
            "score": score_conversation(item),
            "flags": item["flags"],
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def top_per_brand(scored, n=15):
    brands = {}
    for conv in scored:
        wid = conv["widgetId"]
        if wid not in brands:
            brands[wid] = []
        if len(brands[wid]) < n:
            brands[wid].append(conv)
    return brands