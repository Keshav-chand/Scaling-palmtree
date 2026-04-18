# Helio Analysis — AI Conversation Intelligence

Automated system to analyse e-commerce AI assistant conversations, surface actionable insights, and flag real problems across brands.

<img width="1918" height="917" alt="image" src="https://github.com/user-attachments/assets/9a0dee1c-f9e7-4c31-b8ee-017e0342cbc1" />


---

## Live Demo

**Frontend:** https://scaling-palmtree.vercel.app  

---

## What This Does

Helio's team manually reviewed conversations every week to find issues with their AI assistants. This doesn't scale.

This system automates that end-to-end:

1. Ingests raw MongoDB conversation data
2. Uses an LLM to read every conversation in full context before deciding anything
3. Flags specific messages — not whole conversations — with precise one-line reasons
4. Ranks flagged conversations by severity
5. Serves everything via a FastAPI backend
6. Displays a clean Next.js dashboard where reviewers see exactly what went wrong in under 3 seconds

---

## What the Data Showed

**3 brands · 298 conversations · 18 flagged with confirmed issues**

| Brand | Frustration | Drop-off | Top Issue |
|---|---|---|---|
| Blue Nectar — Wellness | 6.1% | 13.3% | Wrong category recommendations when intent is unclear |
| Blue Nectar — Skincare | 3% | 6% | Generic responses without tailoring to specific queries |
| Sri Sri Tattva | 4% | 12% | Deflects order queries to account login instead of resolving |


<img width="1918" height="917" alt="image" src="https://github.com/user-attachments/assets/2fee744e-e4dc-474e-a995-e8439956b769" />


<img width="1919" height="925" alt="image" src="https://github.com/user-attachments/assets/2afff7f3-271e-426b-90de-80c26285b297" />


<img width="1645" height="758" alt="image" src="https://github.com/user-attachments/assets/217533d0-229e-4deb-9f81-a2f3ad9b2b93" />



---

## Architecture

```
MongoDB
↓
pipeline/ingest.py              — fetch raw conversation + message data
pipeline/clean.py               — group messages by conversation, filter noise
analysis/feature.py             — per-conversation metrics (duration, drop-off, message count)
llm/conversation_analyzer.py   — LLM reads full conversation, flags specific messages
analysis/scoring.py             — score each conversation from flag count and type
analysis/aggregation.py         — brand-level rollups
llm/intent.py                   — classify first user message intent
llm/insights.py                 — LLM analysis of top 15 worst conversations per brand
↓
data/ (cached JSON)
↓
FastAPI (6 endpoints)
↓
Next.js dashboard
```

Pipeline outputs are cached. The API never recomputes — it only reads from `data/`.

---

## The Flagging System

### Old approach (removed)
Keyword lists — flagged 80%+ of conversations. Produced noise, not signal.

### New approach
LLM reads the **full conversation** before deciding anything. Never analyzes messages in isolation.

| Type | Applied to | When |
|---|---|---|
| `frustration` | User messages only | User explicitly angry, repeats same request with no resolution, or gives up |
| `hallucination` | Assistant messages only | Assistant states something factually wrong that user explicitly corrects |
| `irrelevant_product` | Assistant messages only | Hard mismatch — user asked for product type A, assistant recommended type B |

Each flag contains:
- `message_id` — exact index of the flagged message
- `type` — frustration / hallucination / irrelevant_product
- `reason` — one line, specific to that conversation

**Result:** 18 flagged out of 298 (~6%) — only real problems surface.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Database | MongoDB |
| Backend | FastAPI + Python |
| LLM (flagging) | Groq API — LLaMA 3.3 70b Versatile |
| LLM (insights) | Groq API — LLaMA 3.1 8b Instant |
| Frontend | Next.js 15 + TypeScript |
| Charts | Recharts |

---

## API Endpoints

```
GET /health                  — health check
GET /brands                  — all brands with key metrics
GET /metrics/{brand}         — deep metrics + intent distribution
GET /conversations/{brand}   — flagged conversations first, then clean
GET /conversation/{id}       — full thread with flags mapped to exact message_ids
GET /flagged                 — all flagged conversations sorted by severity
```

---

## Dashboard Pages

| Page | Purpose |
|---|---|
| Overview | Brand performance summary — metrics, comparison table, charts |
| Issues | All flagged conversations — click to expand thread with highlighted messages |
| Brand detail | Per-brand deep dive — intent distribution, flag breakdown, conversation list |

---

## Setup

### 1. Import data
```bash
mongoimport --db helio_intern --collection conversations --file conversations.json --jsonArray
mongoimport --db helio_intern --collection messages --file messages.json --jsonArray
```

### 2. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `.env`:
```
MONGODB_URI=mongodb://localhost:27017
DB_NAME=helio_intern
GROQ_API_KEY=gsk_...
```

```bash
python run_pipeline.py
uvicorn main:app --reload
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## Key Design Decisions

**Why LLM flagging instead of keywords?**  
Keywords flagged 80%+ of conversations. The LLM reads full context, dropping flag rate to ~6% — only genuine problems.

**Why LLaMA 3.3 70b for flagging?**  
The 8b model couldn't reliably follow nuanced instructions. The 70b model understands the distinction correctly.

**Why message-level flags?**  
Conversation-level flags tell a reviewer "something went wrong". Message-level flags tell them exactly where and why.

**Why cache everything?**  
Pipeline runs once. API reads JSON. Response times under 50ms.

---

