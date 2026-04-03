# Helio Analysis — AI Assistant Conversation Intelligence

 ### Automated system to analyse e-commerce AI assistant conversations, surface actionable insights, and compare performance across brands.

<img width="1919" height="872" alt="image" src="https://github.com/user-attachments/assets/6dcba593-c3b5-4652-a851-9442b79fb5fd" />



---

## What This Is

Helio's team manually reviews conversations every week to find issues with their AI assistants. This doesn't scale.

This system automates that process end-to-end:

1. Ingests raw MongoDB conversation data
2. Computes quality signals per conversation (frustration, drop-off, hallucination, irrelevant products)
3. Ranks conversations by severity score
4. Uses an LLM to analyse the top 15 worst conversations per brand
5. Serves everything via a FastAPI backend
6. Displays insights in a clean Next.js dashboard

---

## What the Data Showed

**3 brands analysed · 298 conversations · 1,525 messages · 45 LLM-generated insights**

### Blue Nectar Wellness (`680a0a8b`)
- **13.3% drop-off rate** highest across all brands
- **20 irrelevant product flags**  users viewed products but never clicked, suggesting the assistant recommends wrong items
- Avg conversation duration: 4,298 seconds  users spend a long time before giving up
- Top issue: assistant repeatedly asks for order details the customer already provided

### Blue Nectar Skincare (`6983153e`)
- **11% frustration rate**  highest across all brands
- Only 3.3 avg messages per conversation  users leave very quickly
- Recurring pattern: assistant gives the same response twice without detecting repetition
- Top issue: no context retention between turns, leading to copy-paste replies

### Sri Sri Tattva (`69a92ad7`)
- **Best performing brand**  2% frustration, zero hallucination flags
- Avg conversation resolves in 779 seconds  5x faster than Blue Nectar Wellness
- 12% drop-off still present  driven mostly by low quality short responses
- Top issue: assistant gives generic answers without tailoring to product-specific queries

### Cross-brand finding (not asked, discovered independently)
Conversations starting with "I am confused between" consistently score higher on frustration. These users need comparison help  the assistant treats them as standard product queries instead of guiding them through a decision.

---

## Architecture
### Pipeline runs once → results cached → API serves instantly
```
MongoDB
  ↓
pipeline/ingest.py      — fetch raw data
pipeline/clean.py       — separate text vs event messages, group by brand
analysis/features.py    — per-conversation metrics (duration, drop-off, message count)
analysis/repetition.py  — sentence-transformer embeddings, cosine similarity
analysis/flags.py       — frustration, hallucination, low quality, irrelevant product
analysis/scoring.py     — weighted score per conversation
analysis/aggregation.py — brand-level rollups
llm/intent.py           — Groq LLaMA 8b: classify first user message
llm/insights.py         — Groq LLaMA 8b: analyse top 15 per brand
  ↓
data/ (cached JSON)
  ↓
FastAPI (4 endpoints)
  ↓
Next.js dashboard
```

All pipeline outputs are cached. The API never recomputes it only reads from `data/`.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Database | MongoDB |
| Backend | FastAPI + Python |
| NLP | sentence-transformers (all-MiniLM-L6-v2) |
| LLM | Groq API — LLaMA 3.1 8b Instant |
| Frontend | Next.js 15 (App Router) + TypeScript |
| Charts | Recharts |
| Styling | Tailwind + inline styles |

---

## API Endpoints

```
GET /brands                  — all brands with key metrics
GET /metrics/{brand}         — deep metrics + intent distribution for one brand
GET /conversations/{brand}   — top 50 scored conversations with flags and preview
GET /insights/{brand}        — LLM analysis for top 15 worst conversations
```

---

## Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB running locally
- Groq API key (free at console.groq.com)

### 1. Import data

```bash
mongoimport --db helio_intern --collection conversations --file conversations.json --jsonArray
mongoimport --db helio_intern --collection messages --file messages.json --jsonArray
```

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Create `.env`:
```
MONGODB_URI=mongodb://localhost:27017
DB_NAME=helio_intern
GROQ_API_KEY=gsk_...
```

Run pipeline (once):
```bash
python run_pipeline.py
```

Start API:
```bash
uvicorn main:app --reload
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`

---

## Project Structure

```
helio-analysis/
├── backend/
│   ├── data/                  # cached pipeline outputs (gitignored)
│   ├── db/mongo.py
│   ├── pipeline/              # ingest, clean, build_dataset
│   ├── analysis/              # features, repetition, flags, scoring, aggregation
│   ├── llm/                   # intent, insights, prompts
│   ├── api/                   # FastAPI routes and schemas
│   ├── config.py
│   ├── run_pipeline.py
│   └── main.py
└── frontend/
    ├── app/
    │   ├── page.tsx            # overview — all brands
    │   ├── brand/[id]/         # brand detail — charts and conversations
    │   └── insights/[id]/      # top 15 LLM insights per brand
    └── lib/api.ts              # API client
```

---

## Screenshots
### Overview → Brand deep dive → LLM insights

<img width="1919" height="872" alt="image" src="https://github.com/user-attachments/assets/44577c40-58d7-4e00-878b-6054f9916d92" />


<img width="1919" height="879" alt="image" src="https://github.com/user-attachments/assets/57a118cc-8e81-47ba-9e99-62939d28c465" />


<img width="1918" height="866" alt="image" src="https://github.com/user-attachments/assets/88efeaef-8a88-4324-aa06-7a84cb29664b" />


<img width="1915" height="866" alt="image" src="https://github.com/user-attachments/assets/8abf1dc0-5572-4e58-ac0b-c064da8def37" />




## Key Design Decisions

**Why not just paste conversations into ChatGPT?** That's a one-time manual analysis. It doesn't scale, can't compare brands, and produces no structured output. This system runs on any new data automatically.

**Why top 15 per brand, not global top 45?** Picking globally could give 40 results from one brand and 0 from another. Per-brand selection ensures every assistant gets equal analysis regardless of conversation volume.

**Why cache everything?** The pipeline runs once. The API just reads JSON. Response times stay under 50ms regardless of dataset size.

**Why LLaMA 8b instead of a larger model?** For 5-message e-commerce conversations, 8b is more than sufficient and fits comfortably within Groq's free tier (500k tokens/day vs 100k for 70b).
