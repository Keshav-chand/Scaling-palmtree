def intent_prompt(first_message):
    return f"""Classify this customer message into exactly one category.
Categories: product_question, order_issue, recommendation, policy, other

Message: "{first_message}"

Reply with only the category name, nothing else."""

def insights_prompt(conversation_text):
    return f"""You are analyzing a customer service conversation for an e-commerce AI assistant.

Conversation:
{conversation_text}

Answer in JSON with these exact keys:
{{
  "what_went_wrong": "...",
  "why": "...",
  "how_to_fix": "...",
  "severity": "low|medium|high"
}}

Reply with only the JSON, nothing else."""