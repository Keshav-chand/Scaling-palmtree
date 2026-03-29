import json
import os
from groq import Groq
from config import GROQ_API_KEY, INTENT_MODEL, INTENTS_PATH
from llm.prompts import intent_prompt

client = Groq(api_key=GROQ_API_KEY)

def classify_intent(message):
    response = client.chat.completions.create(
        model=INTENT_MODEL,
        messages=[{"role": "user", "content": intent_prompt(message)}],
        max_tokens=10,
        temperature=0
    )
    return response.choices[0].message.content.strip().lower()

def batch_classify(structured_convs):
    if os.path.exists(INTENTS_PATH):
        print("Loading cached intents...")
        with open(INTENTS_PATH) as f:
            return json.load(f)

    print("Classifying intents...")
    intents = {}
    for i, conv in enumerate(structured_convs):
        user_msgs = [m for m in conv["messages"] if m["sender"] == "user"]
        if not user_msgs:
            intents[conv["conversation_id"]] = "other"
            continue

        first_msg = user_msgs[0]["text"]
        try:
            intents[conv["conversation_id"]] = classify_intent(first_msg)
        except Exception as e:
            print(f"  Error on conv {i}: {e}")
            intents[conv["conversation_id"]] = "other"

        if i % 20 == 0:
            print(f"  Classified {i}/{len(structured_convs)}")

    with open(INTENTS_PATH, "w") as f:
        json.dump(intents, f, indent=2)

    print(f"Saved intents to {INTENTS_PATH}")
    return intents