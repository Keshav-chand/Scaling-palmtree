FRUSTRATION_KEYWORDS = [
    # Original
    "wrong", "not working", "useless", "bad", "terrible", "worst",
    "disappointed", "frustrated", "broken", "again", "still", "never",
    "waste", "pathetic", "ridiculous", "unacceptable",
    # Added
    "not helpful", "doesn't help", "doesnt help", "not understanding",
    "please help", "no response", "wrong product", "not what i asked",
    "same question", "already asked", "told you", "as i said",
    "cannot", "can't find", "confused", "makes no sense",
    "not what i wanted", "irrelevant", "stop", "enough", "give up"
]

def frustration_flag(conv, repetition_score):
    user_text = " ".join(
        m["text"].lower() for m in conv["messages"]
        if m["sender"] == "user" and m.get("text")
    )
    has_keywords = any(kw in user_text for kw in FRUSTRATION_KEYWORDS)
    # Relaxed: keyword alone is enough OR repetition + any negative signal
    return has_keywords or repetition_score > 0.85

def low_quality_flag(features):
    # Raised threshold from 10 to 20 words
    return features["avg_agent_response_length"] < 20

def hallucination_flag(conv):
    CONTRADICT_KEYWORDS = [
        "that's wrong", "thats wrong", "not correct", "actually",
        "that is wrong", "incorrect", "you said", "but you", "that's not",
        "thats not", "you mentioned", "not true", "false"
    ]
    user_texts = [
        m["text"].lower() for m in conv["messages"]
        if m["sender"] == "user" and m.get("text")
    ]
    return any(
        any(kw in txt for kw in CONTRADICT_KEYWORDS)
        for txt in user_texts
    )

def irrelevant_product_flag(features):
    return features["product_views"] > 0 and features["product_clicks"] == 0

def compute_all_flags(structured_convs, features_list, repetition_scores):
    features_by_id = {f["conversation_id"]: f for f in features_list}
    flags = []

    for conv in structured_convs:
        cid = conv["conversation_id"]
        feat = features_by_id[cid]
        rep_score = repetition_scores.get(cid, 0.0)

        flags.append({
            "conversation_id": cid,
            "widgetId": conv["widgetId"],
            "frustration": frustration_flag(conv, rep_score),
            "low_quality_response": low_quality_flag(feat),
            "hallucination": hallucination_flag(conv),
            "irrelevant_product": irrelevant_product_flag(feat),
            "repetition_score": rep_score
        })

    return flags