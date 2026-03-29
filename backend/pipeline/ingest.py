from db.mongo import conversations_col, messages_col

def fetch_all():
    conversations = list(conversations_col.find())
    messages = list(messages_col.find())

    # Convert ObjectIds to strings
    for c in conversations:
        c["_id"] = str(c["_id"])
        c["widgetId"] = str(c["widgetId"])

    for m in messages:
        m["_id"] = str(m["_id"])
        m["conversationId"] = str(m["conversationId"])

    return conversations, messages