import json
import os
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are a conversation quality reviewer for an AI shopping assistant.

CONTEXT:
The assistant is configured for a specific e-commerce brand — it knows only that brand's products, policies, and tone.

A customer opens the chat widget while browsing the brand's website. The assistant should respond based on:
1. What the user is asking
2. The product page context (PAGE CONTEXT and [event] lines)
3. The brand's domain and general product type

--------------------------------------------------

PAGE CONTEXT — CRITICAL:

Each conversation shows which product pages the user was browsing:
- [browsing] = page user was on while typing
- [clicked] = product/event the user interacted with

Use this as a helpful signal, but NOT as strict truth.

- If user is on a product page and asks about it → relevant answers = CORRECT
- If assistant responds within the same general category → DO NOT flag
- Page context is a soft signal, not a strict constraint

MISSING PAGE CONTEXT:

If no page context is available:
- Do NOT infer mismatch based on category alone
- Only rely on strong signals like domain or explicit brand mismatch
- When unsure, DO NOT flag

--------------------------------------------------

SPECIAL BEHAVIOR RULES:

AUTOMATED PRE-RESPONSES:
The assistant may send messages triggered by user actions (e.g., button clicks) before the user types.

Do NOT flag an assistant message as "unanswered_question" solely because it appears before the user's question.
If it is topically relevant, treat it as valid.

INFORMATION GATHERING IS VALID:
If the user asks about an order (e.g., delivery status) and the assistant asks for required details (order number, phone number, email), do NOT flag.
This is a correct step, not an unanswered question.

CONTEXT WINDOW:
Always consider the last 3-5 messages before making a decision.

--------------------------------------------------

YOUR JOB:

Flag messages with clear or strongly likely problems.
When genuinely unsure, DO NOT flag.

If no issues exist, return:
{"flags": []}

--------------------------------------------------

FLAG TYPES:

1. "frustration" (user messages ONLY)

Flag when:
- User expresses clear anger, annoyance, or gives up
- User repeats the same question multiple times with no resolution

Do NOT flag:
- Mild impatience
- Normal follow-ups

--------------------------------------------------

2. "hallucination" (assistant messages ONLY)

Flag when:
- Assistant gives a specific incorrect fact contradicted by the user or context
- Assistant answers about the WRONG product than what the user asked
- Assistant answers about a clearly different product than the one asked, even if not explicitly contradicted

Do NOT flag:
- Vague responses
- Partial answers
- Uncertainty

--------------------------------------------------

3. "irrelevant_product" (assistant messages ONLY)

Flag when there is clear or strongly likely evidence the product is NOT from this brand:

Flag when:
- Assistant links to a different domain than BRAND DOMAIN
- Assistant explicitly mentions a different brand name
- Product category strongly contradicts the brand type
  (e.g., tea brand assistant recommending surgical equipment)

Do NOT flag:
- Any product that could plausibly belong to the brand
- Hair care products on a skincare brand — same company can sell both
- Wellness/supplement crossover products
- Unfamiliar product names — assume they belong to the brand unless proven otherwise
- When unsure, DO NOT flag

--------------------------------------------------

4. "unanswered_question" (assistant messages ONLY)

Flag when:
- User asks a clear, specific question AND
- Assistant response does NOT address ANY part of it

Do NOT flag:
- Partial answers
- Wrong answers (use hallucination instead)
- Clarifying questions (e.g., asking for order number)

--------------------------------------------------

5. "context_ignored" (assistant messages ONLY)

Flag when:
- User provides new information or correction AND
- Assistant repeats the SAME response without adapting

Example:
User: "I already signed in"
Assistant: "Please sign in"

Do NOT flag:
- Slightly modified responses
- Valid clarification attempts
- Responses that convey the same information with minor rewording

--------------------------------------------------

OUTPUT FORMAT — STRICT JSON ONLY:

{
  "flags": [
    {
      "message_id": <integer>,
      "type": "<flag_type>",
      "reason": "<one specific sentence referencing exact product, page, or domain>"
    }
  ]
}

--------------------------------------------------

CALIBRATION RULES:

- {"flags": []} is expected for most conversations — but not all
- Maximum 3 flags per conversation
- Prefer precision over recall
- message_id MUST match actual message ID
- Do NOT invent IDs
- Reasons must reference exact conversation details
- Target: 60-90 flagged conversations out of 597 total

- Do not ignore clear issues just because they are not explicitly confirmed
- If the assistant response is likely incorrect based on context, flag it
- Common patterns you WILL encounter in this data:
  * Assistant repeating the exact same response after user provides new context
  * Assistant answering about the wrong product when user asked about a specific one
  * User expressing frustration after repeated unhelpful responses
  * Assistant completely ignoring the user's actual question
  * User repeating the same question 2+ times with no resolution

FINAL RULE:
When genuinely unsure, DO NOT flag."""


def format_for_analysis(conv):
    brand_name = conv.get("brand_name", "Unknown Brand")
    brand_domain = conv.get("brand_domain", "")
    brand_description = conv.get("brand_description", "")

    lines = []
    lines.append(f"BRAND: {brand_name}")
    if brand_domain:
        lines.append(f"DOMAIN: {brand_domain}")
    if brand_description:
        lines.append(f"CONTEXT: {brand_description}")

    page_context = conv.get("page_context", [])
    if page_context:
        lines.append("PAGE CONTEXT: Products the user was viewing during this conversation:")
        for p in page_context[:5]:
            source = "clicked" if p.get("source") == "event" else "browsing"
            lines.append(f"  - {p['label']} [{source}]")
    else:
        page_slugs = conv.get("page_slugs", [])
        if page_slugs:
            lines.append("PAGE CONTEXT: User was on these product pages:")
            for s in page_slugs[:5]:
                lines.append(f"  - {s}")
    lines.append("")

    timeline = conv.get("timeline", [])
    if timeline:
        msg_index = 0
        for item in timeline:
            if item["kind"] == "message":
                sender = "Customer" if item.get("sender") == "user" else "Assistant"
                text = (item.get("text") or "").strip()
                text = text.split("End of stream")[0].strip()[:600]
                if text:
                    mid = item.get("message_id")
                    display_id = mid if mid is not None else msg_index
                    lines.append(f"[{display_id}] {sender}: {text}")
                    msg_index += 1
            elif item["kind"] == "event":
                text = (item.get("text") or "").strip()
                if text:
                    lines.append(f"[event] {text}")
    else:
        for msg in conv.get("messages", []):
            mid = msg.get("message_id")
            sender = "Customer" if msg.get("sender") == "user" else "Assistant"
            text = (msg.get("text") or "").strip()[:600]
            if text and mid is not None:
                lines.append(f"[{mid}] {sender}: {text}")

    return "\n".join(lines)


def analyze_conversation(conv):
    conversation_text = format_for_analysis(conv)

    if not conversation_text.strip():
        return {
            "conversation_id": conv["conversation_id"],
            "widgetId": conv.get("widgetId", ""),
            "flags": []
        }

    messages = conv.get("messages", [])
    text_messages = [m for m in messages if (m.get("text") or "").strip()]
    if len(text_messages) < 3:
        return {
            "conversation_id": conv["conversation_id"],
            "widgetId": conv.get("widgetId", ""),
            "flags": []
        }

    response = None
    for _ in range(3):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze this conversation:\n\n{conversation_text}"}
                ],
                max_tokens=500,
                temperature=0
            )
            break
        except Exception as e:
            print(f"  Retrying due to error: {e}")
            time.sleep(2)

    if response is None:
        return {
            "conversation_id": conv["conversation_id"],
            "widgetId": conv.get("widgetId", ""),
            "flags": []
        }

    try:
        raw = response.choices[0].message.content.strip()

        if not raw:
            return {
                "conversation_id": conv["conversation_id"],
                "widgetId": conv.get("widgetId", ""),
                "flags": []
            }

        if raw.startswith("```"):
            parts = raw.split("```")
            if len(parts) > 1:
                raw = parts[1]
            if raw.startswith("json"):
                raw = raw[4:]

        raw = raw.strip()

        if not raw.startswith("{"):
            return {
                "conversation_id": conv["conversation_id"],
                "widgetId": conv.get("widgetId", ""),
                "flags": []
            }

        parsed = json.loads(raw)
        flags = parsed.get("flags", [])

        valid_types = {
            "frustration",
            "hallucination",
            "irrelevant_product",
            "unanswered_question",
            "context_ignored"
        }
        flags = [
            f for f in flags
            if isinstance(f.get("message_id"), int)
            and f.get("type") in valid_types
            and isinstance(f.get("reason"), str)
            and len(f.get("reason", "")) > 10
        ]

        seen_ids = set()
        deduplicated = []
        for f in flags:
            if f["message_id"] not in seen_ids and len(deduplicated) < 3:
                deduplicated.append(f)
                seen_ids.add(f["message_id"])

        return {
            "conversation_id": conv["conversation_id"],
            "widgetId": conv.get("widgetId", ""),
            "flags": deduplicated
        }

    except Exception as e:
        print(f"  [analyzer] Parse error for {conv['conversation_id'][:16]}: {e}")
        return {
            "conversation_id": conv["conversation_id"],
            "widgetId": conv.get("widgetId", ""),
            "flags": []
        }


def batch_analyze(structured_convs, cache_path="data/llm_flags.json"):
    existing = []
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
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
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        time.sleep(1.5)

    flagged = sum(1 for r in results if r["flags"])
    print(f"\n  Done. {flagged}/{total} conversations flagged.")
    return results