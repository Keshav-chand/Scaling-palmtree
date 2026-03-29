from collections import defaultdict

def aggregate_by_brand(flags, features_list):
    features_by_id = {f["conversation_id"]: f for f in features_list}
    brand_data = defaultdict(lambda: {
        "total_conversations": 0,
        "drop_offs": 0,
        "frustration_count": 0,
        "low_quality_count": 0,
        "hallucination_count": 0,
        "irrelevant_product_count": 0,
        "total_duration": 0,
        "total_messages": 0,
        "product_views": 0,
        "product_clicks": 0,
    })

    for flag in flags:
        wid = flag["widgetId"]
        feat = features_by_id.get(flag["conversation_id"], {})
        b = brand_data[wid]

        b["total_conversations"] += 1
        b["frustration_count"] += int(flag["frustration"])
        b["low_quality_count"] += int(flag["low_quality_response"])
        b["hallucination_count"] += int(flag["hallucination"])
        b["irrelevant_product_count"] += int(flag["irrelevant_product"])
        b["drop_offs"] += int(feat.get("drop_off_flag", False))
        b["total_duration"] += feat.get("duration_seconds", 0)
        b["total_messages"] += feat.get("message_count", 0)
        b["product_views"] += feat.get("product_views", 0)
        b["product_clicks"] += feat.get("product_clicks", 0)

    # Compute percentages
    result = {}
    for wid, b in brand_data.items():
        total = b["total_conversations"] or 1
        result[wid] = {
            **b,
            "drop_off_pct": round(b["drop_offs"] / total * 100, 1),
            "frustration_pct": round(b["frustration_count"] / total * 100, 1),
            "low_quality_pct": round(b["low_quality_count"] / total * 100, 1),
            "hallucination_pct": round(b["hallucination_count"] / total * 100, 1),
            "avg_messages": round(b["total_messages"] / total, 1),
            "avg_duration_seconds": round(b["total_duration"] / total, 1),
        }

    return result