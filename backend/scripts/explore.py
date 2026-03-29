import sys
sys.path.append("..")

from collections import Counter
from db.mongo import conversations_col, messages_col

convs = list(conversations_col.find())
msgs = list(messages_col.find())

# Brands
widget_ids = [str(c["widgetId"]) for c in convs]
brand_counts = Counter(widget_ids)
print(f"Total brands: {len(brand_counts)}")
print(f"Total conversations: {len(convs)}")
print(f"Total messages: {len(msgs)}")
print()
print("Conversations per brand:")
for wid, count in brand_counts.most_common():
    print(f"  {wid}: {count}")

# Message types
type_counts = Counter(m.get("messageType") for m in msgs)
print(f"\nMessage types: {dict(type_counts)}")

# Event types
event_types = Counter(
    m.get("metadata", {}).get("eventType")
    for m in msgs if m.get("messageType") == "event"
)
print(f"Event types: {dict(event_types)}")

# Avg messages per conversation
from collections import defaultdict
msgs_per_conv = defaultdict(int)
for m in msgs:
    msgs_per_conv[str(m["conversationId"])] += 1
avg = sum(msgs_per_conv.values()) / len(msgs_per_conv) if msgs_per_conv else 0
print(f"\nAvg messages per conversation: {avg:.1f}")