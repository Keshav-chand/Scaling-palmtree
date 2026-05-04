import json
import textwrap


BRAND_NAMES = {
    "680a0a8b70a26f7a0e24eedd": "Blue Tea",
    "6983153e1497a62e8542a0ad": "Blue Tea (Secondary)",
    "69a92ad76dcbf2da868e0f9b": "Sri Sri Tattva",
}

FLAG_DISPLAY = {
    "frustration":          "FRUSTRATION",
    "hallucination":        "HALLUCINATION",
    "irrelevant_product":   "IRRELEVANT_PRODUCT",
    "unanswered_question":  "UNANSWERED_QUESTION",
    "context_ignored":      "CONTEXT_IGNORED",
}

CONTEXT_BEFORE = 3   # how many messages to show before a flagged message
WRAP_WIDTH     = 90  # wrap long messages at this column


def _wrap(text, indent="         "):
    """Wrap long text with consistent indent."""
    text = (text or "").split("End of stream")[0].strip()
    lines = textwrap.wrap(text, width=WRAP_WIDTH - len(indent))
    return ("\n" + indent).join(lines)


def _sender_label(sender):
    if sender == "user":
        return "[user] "
    elif sender == "agent":
        return "[agent]"
    else:
        return "[event]"


def format_conversation_block(conv_id, widgetId, messages, flags):
    """
    Format a single conversation into the readable audit block.

    messages — list of dicts with keys: message_id, sender, text, timestamp
    flags    — list of dicts with keys: message_id, type, reason
    """
    brand = BRAND_NAMES.get(widgetId, widgetId[:12])
    sep = "-" * 56

    # Index messages by message_id for fast lookup
    msg_by_id = {m["message_id"]: m for m in messages if m.get("message_id") is not None}

    # Limit to max 2 flags per block for readability
    flags_to_show = flags[:2]

    # Collect which message windows we need to render
    # For each flag, show CONTEXT_BEFORE messages before the flagged one
    windows = []
    for flag in flags_to_show:
        fid = flag["message_id"]
        start = max(0, fid - CONTEXT_BEFORE)
        window_ids = list(range(start, fid + 1))
        windows.append((window_ids, flag))

    # Merge overlapping windows into single sorted list
    all_ids_needed = sorted({mid for ids, _ in windows for mid in ids})

    lines = []
    lines.append(f"\nCONVERSATION {conv_id[:24]}...  [brand: {brand}]")
    lines.append(sep)

    # Track which flags we've already printed to avoid duplicates
    printed_flags = set()

    prev_id = None
    for mid in all_ids_needed:
        msg = msg_by_id.get(mid)
        if not msg:
            continue

        # Print ellipsis if there's a gap from previous printed message
        if prev_id is not None and mid > prev_id + 1:
            lines.append("  ...")
        prev_id = mid

        sender = msg.get("sender", "")
        text   = _wrap(msg.get("text", ""))
        label  = _sender_label(sender)

        lines.append(f"\n{label}  {text}")

        # Check if this message is flagged
        for flag in flags_to_show:
            if flag["message_id"] == mid and mid not in printed_flags:
                flag_label = FLAG_DISPLAY.get(flag["type"], flag["type"].upper())
                reason     = _wrap(flag["reason"], indent="         ")
                lines.append(f"\n         ^ {flag_label}")
                lines.append(f"         {reason}")
                printed_flags.add(mid)

    lines.append(f"\n{sep}")
    return "\n".join(lines)


def format_all(llm_flags, conv_by_id, output_path=None):
    """
    Transform all flagged conversations into readable audit report.

    llm_flags  — list from llm_flags.json or batch_analyze()
    conv_by_id — dict keyed by conversation_id, value is structured conv
                 (must have 'messages' list with message_id, sender, text)
    output_path — if provided, writes to file. Always returns string.
    """
    only_flagged = [r for r in llm_flags if r.get("flags")]
    only_flagged.sort(key=lambda x: -len(x["flags"]))

    blocks = []
    blocks.append("=" * 56)
    blocks.append(f"  AI ASSISTANT CHAT AUDIT — {len(only_flagged)} conversations flagged")
    blocks.append("=" * 56)

    for result in only_flagged:
        cid     = result["conversation_id"]
        wid     = result["widgetId"]
        flags   = result["flags"]
        conv    = conv_by_id.get(cid, {})
        messages = conv.get("messages", [])

        if not messages:
            continue

        block = format_conversation_block(cid, wid, messages, flags)
        blocks.append(block)

    report = "\n".join(blocks)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"  Report written to {output_path}")

    return report


# ── Standalone usage ────────────────────────────────────────────
if __name__ == "__main__":
    import os

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    with open(os.path.join(base, "data", "llm_flags.json")) as f:
        llm_flags = json.load(f)

    with open(os.path.join(base, "data", "processed_data.json")) as f:
        processed = json.load(f)

    # Assign message_ids if not already set
    for conv in processed:
        for i, msg in enumerate(conv.get("messages", [])):
            msg["message_id"] = i

    conv_by_id = {c["conversation_id"]: c for c in processed}

    report = format_all(llm_flags, conv_by_id, output_path="data/audit_report.txt")
    print(report[:3000])  # preview first 3000 chars