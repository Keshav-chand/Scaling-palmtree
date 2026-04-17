import json
import os
import time
from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are a conversation quality reviewer for an e-commerce AI assistant.
Your job: read the full conversation and flag ONLY messages with clear, obvious problems.
CORE RULE: When in doubt, do NOT flag. An empty flags list is correct and expected for most conversations.
CALIBRATION: You should expect to return empty flags for at least 60% of conversations. If you are flagging more than that, you are being too aggressive.
If no issues are found, return:
{"flags": []}
Rules:
- Read the ENTIRE conversation before deciding
- Assign flags to specific message_ids only
- message_id must exactly match the IDs provided in the conversation. Do not create new IDs
- Maximum 3 flags per conversation
Flag types:
"frustration" → user messages ONLY
Flag ONLY when the user explicitly says the assistant failed them, uses angry language, or has asked the same thing 2+ times with no resolution, or clearly expresses they are giving up.
Do NOT flag normal dissatisfaction, polite corrections, or mild impatience.
"hallucination" → assistant messages ONLY
Flag ONLY when the assistant makes a clearly false factual claim that contradicts the conversation OR is explicitly corrected by the user.
Do NOT flag vague or generic responses.
"irrelevant_product" → assistant messages ONLY
Flag ONLY when there is a HARD MISMATCH between user intent and recommendation.
Example: user asks for face wash, assistant recommends hair oil.
Do NOT flag similar or loosely related recommendations. Flag when the category is completely different from what the user asked for.
Output (STRICT JSON ONLY):
{
  "flags": [
    {"message_id": <integer>, "type": "<frustration|hallucination|irrelevant_product>", "reason": "<one line, specific>"}
  ]
}
Reason must be specific and reference the mismatch or issue clearly.
"""


def format_for_analysis(conv):
    lines = []
    for msg in conv.get("messages", []):
        mid = msg.get("message_id")
        sender = "Customer" if msg.get("sender") == "user" else "Assistant"
        text = (msg.get("text") or "").strip()[:400]
        if text and mid is not None:
            lines.append(f"[{mid}] {sender}: {text}")
    return "\n".join(lines)


def analyze_conversation(conv):
    conversation_text = format_for_analysis(conv)

    if not conversation_text.strip():
        return {"conversation_id": conv["conversation_id"], "widgetId": conv.get("widgetId", ""), "flags": []}

    messages = conv.get("messages", [])
    text_messages = [m for m in messages if (m.get("text") or "").strip()]
    if len(text_messages) < 3:
        return {"conversation_id": conv["conversation_id"], "widgetId": conv.get("widgetId", ""), "flags": []}

    response = None
    for _ in range(3):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze this conversation:\n\n{conversation_text}"}
                ],
                max_tokens=600,
                temperature=0
            )
            break
        except Exception as e:
            print(f"  Retrying due to error: {e}")
            time.sleep(2)

    if response is None:
        return {"conversation_id": conv["conversation_id"], "widgetId": conv.get("widgetId", ""), "flags": []}

    try:
        raw = response.choices[0].message.content.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        parsed = json.loads(raw.strip())
        flags = parsed.get("flags", [])

        valid_types = {"frustration", "hallucination", "irrelevant_product"}
        flags = [
            f for f in flags
            if isinstance(f.get("message_id"), int)
            and f.get("type") in valid_types
            and isinstance(f.get("reason"), str)
        ]

        seen_ids = set()
        deduplicated = []
        for f in flags:
            if f["message_id"] not in seen_ids:
                deduplicated.append(f)
                seen_ids.add(f["message_id"])

        return {"conversation_id": conv["conversation_id"], "widgetId": conv.get("widgetId", ""), "flags": deduplicated}

    except Exception as e:
        print(f"  [analyzer] Parse error for {conv['conversation_id'][:16]}: {e}")
        return {"conversation_id": conv["conversation_id"], "widgetId": conv.get("widgetId", ""), "flags": []}


def batch_analyze(structured_convs, cache_path="data/llm_flags.json"):
    # Resume from where we left off
    existing = []
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            existing = json.load(f)
        if len(existing) == len(structured_convs):
            print("  Loading cached LLM flags...")
            return existing
        print(f"  Resuming from conversation {len(existing)+1}...")

    results = list(existing)
    remaining = structured_convs[len(existing):]
    total = len(structured_convs)

    for i, conv in enumerate(remaining):
        actual_index = len(existing) + i + 1
        print(f"  [{actual_index}/{total}] Analyzing {conv['conversation_id'][:16]}...")
        result = analyze_conversation(conv)
        if result["flags"]:
            print(f"    → {len(result['flags'])} flag(s): {[f['type'] for f in result['flags']]}")
        results.append(result)

        os.makedirs("data", exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(results, f, indent=2)

        time.sleep(0.6)

    flagged = sum(1 for r in results if r["flags"])
    print(f"\n  Done. {flagged}/{total} conversations flagged.")
    return results