from datetime import datetime

def compute_features(conv):
    messages = conv["messages"]
    events = conv["events"]

    user_msgs = [m for m in messages if m["sender"] == "user"]
    agent_msgs = [m for m in messages if m["sender"] == "agent"]

    # Duration
    try:
        t_start = datetime.fromisoformat(str(messages[0]["timestamp"]).replace("Z", "+00:00"))
        t_end = datetime.fromisoformat(str(messages[-1]["timestamp"]).replace("Z", "+00:00"))
        duration_seconds = (t_end - t_start).total_seconds()
    except:
        duration_seconds = 0

    # Drop-off: last message is from user (agent never replied)
    drop_off = messages[-1]["sender"] == "user" if messages else False

    # Avg agent response length
    agent_lengths = [len(m["text"].split()) for m in agent_msgs if m.get("text")]
    avg_agent_length = sum(agent_lengths) / len(agent_lengths) if agent_lengths else 0

    # Product engagement from events
    product_views = sum(1 for e in events if e.get("metadata", {}).get("eventType") == "product_view")
    product_clicks = sum(1 for e in events if e.get("metadata", {}).get("eventType") == "quick_action_click")

    return {
        "conversation_id": conv["conversation_id"],
        "widgetId": conv["widgetId"],
        "message_count": len(messages),
        "user_message_count": len(user_msgs),
        "agent_message_count": len(agent_msgs),
        "duration_seconds": duration_seconds,
        "drop_off_flag": drop_off,
        "avg_agent_response_length": round(avg_agent_length, 2),
        "product_views": product_views,
        "product_clicks": product_clicks,
        "product_engagement": product_clicks > 0 if product_views > 0 else None
    }

def compute_all_features(structured_convs):
    return [compute_features(c) for c in structured_convs]