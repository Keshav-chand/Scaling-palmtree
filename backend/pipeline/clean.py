from collections import defaultdict

def clean_and_group(conversations, messages):
    # Separate text vs event messages
    text_messages = [m for m in messages if m.get("messageType") == "text" and m.get("text", "").strip()]
    event_messages = [m for m in messages if m.get("messageType") == "event"]

    # Group by conversationId
    text_by_conv = defaultdict(list)
    events_by_conv = defaultdict(list)

    for m in text_messages:
        text_by_conv[m["conversationId"]].append(m)

    for m in event_messages:
        events_by_conv[m["conversationId"]].append(m)

    # Sort by timestamp
    for cid in text_by_conv:
        text_by_conv[cid].sort(key=lambda x: x["timestamp"])
    for cid in events_by_conv:
        events_by_conv[cid].sort(key=lambda x: x["timestamp"])

    # Build structured conversations
    structured = []
    for conv in conversations:
        cid = conv["_id"]
        msgs = text_by_conv.get(cid, [])
        if not msgs:
            continue  # skip empty conversations

        structured.append({
            "conversation_id": cid,
            "widgetId": conv["widgetId"],
            "createdAt": str(conv.get("createdAt", "")),
            "updatedAt": str(conv.get("updatedAt", "")),
            "messages": msgs,
            "events": events_by_conv.get(cid, [])
        })

    return structured