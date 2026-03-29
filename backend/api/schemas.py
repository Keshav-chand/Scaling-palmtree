from pydantic import BaseModel
from typing import Optional

class BrandSummary(BaseModel):
    widgetId: str
    total_conversations: int
    drop_off_pct: float
    frustration_pct: float
    hallucination_pct: float
    avg_messages: float

class FlagSchema(BaseModel):
    frustration: bool
    low_quality_response: bool
    hallucination: bool
    irrelevant_product: bool
    repetition_score: float

class ConversationSummary(BaseModel):
    conversation_id: str
    score: float
    flags: FlagSchema
    message_count: int
    preview: str

class InsightSchema(BaseModel):
    what_went_wrong: str
    why: str
    how_to_fix: str
    severity: str