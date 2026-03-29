import json
import os
from groq import Groq
from config import GROQ_API_KEY, INSIGHTS_MODEL, INSIGHTS_PATH
from llm.prompts import insights_prompt

client = Groq(api_key=GROQ_API_KEY)

def format_conversation(conv):
    messages = conv["messages"][:10]  # max 10 messages
    lines = []
    for m in messages:
        sender = "Customer" if m["sender"] == "user" else "Assistant"
        lines.append(f"{sender}: {m['text'][:300]}")  # max 300 chars per message
    return "\n".join(lines)

def get_insight(conv):
    text = format_conversation(conv)
    response = client.chat.completions.create(
        model=INSIGHTS_MODEL,
        messages=[{"role": "user", "content": insights_prompt(text)}],
        max_tokens=400,
        temperature=0
    )
    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except:
        return {"what_went_wrong": raw, "why": "", "how_to_fix": "", "severity": "medium"}

def batch_insights(top_per_brand, structured_convs):
    if os.path.exists(INSIGHTS_PATH):
        print("Loading cached insights...")
        with open(INSIGHTS_PATH) as f:
            return json.load(f)

    conv_by_id = {c["conversation_id"]: c for c in structured_convs}
    insights = {}

    for brand, convs in top_per_brand.items():
        print(f"Getting insights for brand {brand}...")
        insights[brand] = []
        for item in convs:
            cid = item["conversation_id"]
            conv = conv_by_id.get(cid)
            if not conv:
                continue
            try:
                insight = get_insight(conv)
                insights[brand].append({
                    "conversation_id": cid,
                    "score": item["score"],
                    "flags": item["flags"],
                    "insight": insight
                })
                print(f"  Done: {cid}")
            except Exception as e:
                print(f"  Error: {e}")

    with open(INSIGHTS_PATH, "w") as f:
        json.dump(insights, f, indent=2)

    print(f"Saved insights to {INSIGHTS_PATH}")
    return insights