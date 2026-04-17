import json
import time
from llm.conversation_analyzer import analyze_conversation

CACHE_PATH = "data/llm_flags.json"
PROCESSED_PATH = "data/processed_data.json"

# Load existing results
with open(CACHE_PATH) as f:
    results = json.load(f)

# Load original conversations
with open(PROCESSED_PATH) as f:
    structured = json.load(f)

# Assign message_ids
for conv in structured:
    for i, msg in enumerate(conv.get("messages", [])):
        msg["message_id"] = i

# Re-analyze only index 254 to 297 (conversations 255-298)
target_range = structured[254:298]
updated = 0

for conv in target_range:
    cid = conv["conversation_id"]
    
    # Find this conversation in existing results
    for i, r in enumerate(results):
        if r["conversation_id"] == cid:
            old_flags = r["flags"]
            print(f"Re-analyzing {cid[:16]}...")
            new_result = analyze_conversation(conv)
            
            # Only update if new result has flags OR old was empty
            results[i] = new_result
            if new_result["flags"]:
                print(f"  → {len(new_result['flags'])} flag(s): {[f['type'] for f in new_result['flags']]}")
            updated += 1
            break
    
    # Save after each one
    with open(CACHE_PATH, "w") as f:
        json.dump(results, f, indent=2)
    
    time.sleep(0.6)

flagged = sum(1 for r in results if r["flags"])
print(f"\nDone. Updated {updated} conversations.")
print(f"Total flagged now: {flagged}/298")