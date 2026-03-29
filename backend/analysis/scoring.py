def score_conversation(flag, feature):
    score = 0

    if flag["frustration"]:
        score += 40
    if flag["low_quality_response"]:
        score += 25
    if flag["hallucination"]:
        score += 20
    if flag["irrelevant_product"]:
        score += 10
    score += min(flag["repetition_score"] * 10, 5)  # max 5 points

    return round(score, 2)

def rank_conversations(flags, features_list):
    features_by_id = {f["conversation_id"]: f for f in features_list}

    scored = []
    for flag in flags:
        cid = flag["conversation_id"]
        feat = features_by_id.get(cid, {})
        scored.append({
            "conversation_id": cid,
            "widgetId": flag["widgetId"],
            "score": score_conversation(flag, feat),
            "flags": flag
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