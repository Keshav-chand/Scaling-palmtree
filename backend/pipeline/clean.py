from collections import defaultdict
import re


BRAND_CONTEXT = {
    "680a0a8b70a26f7a0e24eedd": {
        "name": "Blue Tea",
        "domain": "https://bluetea.co.in",
        "description": (
            "Blue Tea sells herbal and wellness teas only — butterfly pea flower tea, "
            "belly fat tea, chamomile, hibiscus, green tea blends. "
            "The assistant must ONLY recommend tea products from bluetea.co.in. "
            "Any recommendation of skincare, supplements, or other brand domains is wrong."
        ),
    },
    "6983153e1497a62e8542a0ad": {
        "name": "Blue Nectar — Skincare",
        "domain": "https://www.bluenectar.co.in",
        "description": (
            "Blue Nectar sells Ayurvedic skincare products only — face serums, creams, "
            "oils, cleansers, brightening treatments like Kumkumadi and Nalpamaradi Thailam. "
            "The assistant must ONLY recommend skincare products from bluenectar.co.in. "
            "Any recommendation of tea, food, or other brand domains is wrong."
        ),
    },
    "69a92ad76dcbf2da868e0f9b": {
        "name": "Sri Sri Tattva",
        "domain": "https://www.srisritattva.com",
        "description": (
            "Sri Sri Tattva sells Ayurvedic wellness products — supplements, herbal medicines, "
            "hair oils, skin care, groceries like ghee. "
            "The assistant must ONLY recommend products from srisritattva.com. "
            "Any recommendation from other brand domains is wrong."
        ),
    },
}


def _safe_timestamp(item):
    """
    Push invalid timestamps (-1, None) to the end.
    """
    ts = item.get("timestamp", -1)

    if ts in [-1, None]:
        return float("inf")

    return ts


def _extract_slug_from_text(text):
    """
    User messages often have the product slug appended at the end.
    Example:
    "How do I use it daily? shop-prakesha-gold-hair-oil-100ml"

    Extract ALL slugs found anywhere in the text.
    """
    if not text:
        return []

    slugs = []
    tokens = text.strip().split()

    for token in tokens:
        token = token.strip("?.,!\"'()")

        if token.count("-") >= 2 and len(token) > 8 and " " not in token:
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", token):
                slugs.append(token)

    return slugs


def _extract_slug_from_event(text):
    """
    Extract product slug from event URLs.
    """
    if not text:
        return None

    match = re.search(
        r"https?://[^\s]+/products/([^\s?#]+)",
        text
    )

    if match:
        return match.group(1)

    match = re.search(
        r"https?://[^\s]+/collections/([^\s?#]+)",
        text
    )

    if match:
        return "collection/" + match.group(1)

    return None


def _humanize_slug(slug):
    """
    Convert:
    belly-fat-tea-100g -> Belly Fat Tea 100g
    """
    slug = re.sub(r"^(shop|buy|product|view)-", "", slug)
    return slug.replace("-", " ").title()


def clean_and_group(conversations, messages):
    text_messages = [
        m for m in messages
        if m.get("messageType") == "text"
        and m.get("text", "").strip()
    ]

    event_messages = [
        m for m in messages
        if m.get("messageType") == "event"
    ]

    text_by_conv = defaultdict(list)
    events_by_conv = defaultdict(list)

    for m in text_messages:
        text_by_conv[m["conversationId"]].append(m)

    for m in event_messages:
        events_by_conv[m["conversationId"]].append(m)

    # Sort safely using timestamp + Mongo _id tie-breaker
    for cid in text_by_conv:
        text_by_conv[cid].sort(
            key=lambda x: (
                _safe_timestamp(x),
                str(x.get("_id", ""))
            )
        )

    for cid in events_by_conv:
        events_by_conv[cid].sort(
            key=lambda x: (
                _safe_timestamp(x),
                str(x.get("_id", ""))
            )
        )

    structured = []

    for conv in conversations:
        cid = conv["_id"]

        msgs = text_by_conv.get(cid, [])

        if not msgs:
            continue

        wid = conv["widgetId"]

        brand_info = BRAND_CONTEXT.get(
            wid,
            {
                "name": "Unknown Brand",
                "domain": "",
                "description": "E-commerce AI assistant.",
            },
        )

        all_events = events_by_conv.get(cid, [])

        page_context = _build_page_context(msgs, all_events)

        interleaved = _interleave_events(msgs, all_events)

        structured.append({
            "conversation_id": cid,
            "widgetId": wid,
            "brand_name": brand_info["name"],
            "brand_domain": brand_info["domain"],
            "brand_description": brand_info["description"],
            "page_context": page_context,
            "page_slugs": [p["slug"] for p in page_context],
            "createdAt": str(conv.get("createdAt", "")),
            "updatedAt": str(conv.get("updatedAt", "")),
            "messages": msgs,
            "events": all_events,
            "timeline": interleaved,
        })

    return structured


def _build_page_context(msgs, events):
    """
    Build deduplicated list of pages user visited.
    """
    seen = set()
    context = []

    # Extract slugs from user text
    for m in msgs:
        if m.get("sender") != "user":
            continue

        slugs = _extract_slug_from_text(m.get("text", ""))

        for slug in slugs:
            if slug not in seen:
                seen.add(slug)

                context.append({
                    "slug": slug,
                    "label": _humanize_slug(slug),
                    "source": "message",
                })

    # Extract slugs from event URLs
    for e in events:
        slug = _extract_slug_from_event(e.get("text", ""))

        if slug and slug not in seen:
            seen.add(slug)

            context.append({
                "slug": slug,
                "label": _humanize_slug(slug),
                "source": "event",
            })

    return context


def _interleave_events(text_msgs, events):
    """
    Merge messages + events into one chronological timeline.
    """
    combined = []

    # Add text messages
    for m in text_msgs:
        combined.append({
            "_id": m.get("_id", ""),
            "timestamp": m.get("timestamp", -1),
            "kind": "message",
            "sender": m.get("sender"),
            "text": m.get("text", ""),
            "message_id": None,
        })

    # Add event messages
    for e in events:
        raw = e.get("text", "").strip()

        if not raw:
            continue

        slug = _extract_slug_from_event(raw)

        if slug:
            display = (
                f"User navigated to: "
                f"{_humanize_slug(slug)} ({slug})"
            )
        else:
            display = raw

        combined.append({
            "_id": e.get("_id", ""),
            "timestamp": e.get("timestamp", -1),
            "kind": "event",
            "sender": "user",
            "text": display,
            "event_type": e.get("metadata", {}).get("eventType", ""),
            "message_id": None,
        })

    # Final chronological sort
    combined.sort(
        key=lambda x: (
            _safe_timestamp(x),
            str(x.get("_id", ""))
        )
    )

    return combined