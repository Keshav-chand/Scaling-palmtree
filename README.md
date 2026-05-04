# AI Assistant Chat Audit — Message Flagging System

<img width="1913" height="868" alt="image" src="https://github.com/user-attachments/assets/9fcd6403-78fc-4ca4-865b-7511b47d6fc5" />

## Live Demo

Frontend: https://scaling-palmtree.vercel.app 

## What This Does

Automatically reads e-commerce AI assistant conversations and flags specific messages that need attention. Built for HelioAI to replace manual weekly conversation review.

For each flagged exchange, the system produces:
- The conversation context
- The flagged message
- A flag label (e.g. CONTEXT_IGNORED, UNANSWERED_QUESTION)
- A specific explanation of what went wrong

<img width="1918" height="877" alt="image" src="https://github.com/user-attachments/assets/f6e4e657-f6b3-40f9-8bf6-ed4c33612877" />
<img width="1606" height="606" alt="image" src="https://github.com/user-attachments/assets/b551cb79-c8c0-436a-8c94-046186fdc09b" />
<img width="1667" height="805" alt="image" src="https://github.com/user-attachments/assets/82c252f3-bec0-45a4-80cd-c8ee44bfba21" />
<img width="1635" height="652" alt="image" src="https://github.com/user-attachments/assets/2b4bae9d-e801-4d17-a65a-5fcad4ddbbad" />






## Brands Analyzed

| Brand | Widget ID | Conversations |
|---|---|---|
| Blue Tea | 680a0a8b... | 198 |
| Blue Nectar — Skincare | 6983153e... | 199 |
| Sri Sri Tattva | 69a92ad7... | 200 |

## Flag Types

| Flag | Target | Description |
|---|---|---|
| `frustration` | User messages | User expresses anger or repeats question with no resolution |
| `hallucination` | Assistant messages | Assistant answers about wrong product or states incorrect fact |
| `irrelevant_product` | Assistant messages | Assistant recommends product from different brand or domain |
| `unanswered_question` | Assistant messages | Assistant completely ignores user's direct question |
| `context_ignored` | Assistant messages | Assistant repeats same response after user provides new information |

## Architecture
conversations.json + messages.json (v1 March 2026)
conversations_v2.json + messages_v2.json (v2 April 2026)
↓
pipeline/ingest.py       — loads and merges both datasets
pipeline/clean.py        — groups by conversation, extracts page context from slugs and events
↓
llm/conversation_analyzer.py  — LLaMA 3.3 70B via Groq, analyzes each conversation
analysis/aggregation.py       — computes brand-level metrics
analysis/scoring.py           — ranks conversations by severity
↓
api/routes.py            — FastAPI backend serving flagged data
frontend/                — Next.js dashboard
utils/formatter.py       — generates plain text audit_report.txt

## Key Design Decisions

**Page context extraction** — user messages often contain the product slug they were browsing appended at the end (e.g. `"How do I use this? kumkumadi-face-oil-serum"`). The system extracts these slugs and passes them to the LLM so it knows what page the user was on when they typed their question.

**Event interleaving** — click and navigation events are merged into the conversation timeline chronologically so the LLM sees the full picture of what the user was doing between messages.

**Precision over recall** — the system targets ~10-15% flag rate. A false positive is treated as seriously as a miss. The LLM is instructed to only flag when there is clear or strongly likely evidence of a problem.

**Resume capability** — `llm_flags.json` is saved after every conversation. If the pipeline crashes or hits API rate limits, it resumes from the exact conversation it stopped at.

## Data Notes

v1 data (March 2026) has limited page context as the widget was not consistently passing product slugs at that time. v2 data (April 2026) has richer context and produces more accurate flagging. Both datasets are processed and included in the final analysis.

## Running Locally

```bash
# Backend
cd backend
python -m pipeline.built_dataset   # builds processed_data.json
python -m run_pipeline              # runs LLM analysis and scoring

# Start backend server
uvicorn main:app --reload

# Frontend
cd frontend
npm run dev
```

## Environment Variables
GROQ_API_KEY=your_key_here
