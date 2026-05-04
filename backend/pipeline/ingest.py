import json
import os


def fetch_all():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base, "data")

    def load(path):
        with open(path, encoding="utf-8") as f:  # utf-8 fixes unicode error
            return json.load(f)

    conversations = []
    messages = []

    # Load v1 if available
    v1_conv = os.path.join(data_dir, "conversations.json")
    v1_msg = os.path.join(data_dir, "messages.json")
    if os.path.exists(v1_conv) and os.path.exists(v1_msg):
        conversations += load(v1_conv)
        messages += load(v1_msg)
        print(f"  v1 loaded: {len(conversations)} conversations")
    else:
        print("  v1 data not found — skipping")

    # Load v2 if available
    v2_conv = os.path.join(data_dir, "conversations_v2.json")
    v2_msg = os.path.join(data_dir, "messages_v2.json")
    if os.path.exists(v2_conv) and os.path.exists(v2_msg):
        prev = len(conversations)
        conversations += load(v2_conv)
        messages += load(v2_msg)
        print(f"  v2 loaded: {len(conversations) - prev} conversations")
    else:
        print("  v2 data not found — skipping")

    print(f"  Total: {len(conversations)} conversations, {len(messages)} messages")

    if not conversations:
        raise RuntimeError("No data found in data/ folder.")

    for c in conversations:
        c["_id"] = str(c["_id"])
        c["widgetId"] = str(c["widgetId"])

    for m in messages:
        m["_id"] = str(m["_id"])
        m["conversationId"] = str(m["conversationId"])

    return conversations, messages