import json
import os


def fetch_all():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base, "data")

    def load(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    conversations = []
    messages = []

    # v2 only — as requested
    v2_conv = os.path.join(data_dir, "conversations_v2.json")
    v2_msg = os.path.join(data_dir, "messages_v2.json")
    if os.path.exists(v2_conv) and os.path.exists(v2_msg):
        conversations = load(v2_conv)
        messages = load(v2_msg)
        print(f"  v2 loaded: {len(conversations)} conversations, {len(messages)} messages")
    else:
        raise RuntimeError("v2 data not found in data/ folder.")

    for c in conversations:
        c["_id"] = str(c["_id"])
        c["widgetId"] = str(c["widgetId"])

    for m in messages:
        m["_id"] = str(m["_id"])
        m["conversationId"] = str(m["conversationId"])

    return conversations, messages