# Galileo Arena

Multi-model agentic debate evaluation platform with live SSE streaming and Postgres persistence.

## Features

- **4-Role Agentic Debate**: Orthodox, Heretic, Skeptic, Judge -- ALWAYS ON
- **6 LLM Providers**: OpenAI, Anthropic, Mistral, DeepSeek, Gemini, Grok
- **Live Streaming**: SSE-based real-time event stream to the frontend
- **Structured Judge Output**: JSON schema enforcement (Structured Outputs for OpenAI, Pydantic validation + retries for others)
- **Deterministic Scoring**: 0-100 scale (correctness, grounding, calibration, falsifiability)
- **Postgres Persistence**: Full audit trail, case replay, run history
- **Modern Dashboard**: Next.js App Router, Recharts, Tailwind CSS

## Quick Start

### Prerequisites

- Docker & Docker Compose
- API keys for at least one LLM provider

### Setup

```bash
# 1. Clone
git clone <repo-url>
cd galileo-arena

# 2. Configure API keys
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# 3. Start everything
docker-compose up

# 4. Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Local Development (without Docker)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/datasets` | List all datasets |
| GET | `/datasets/{id}` | Get dataset with cases |
| POST | `/runs` | Start an evaluation run |
| GET | `/runs/{run_id}` | Get run status |
| GET | `/runs/{run_id}/summary` | Per-model metrics |
| GET | `/runs/{run_id}/cases` | Paginated case results |
| GET | `/runs/{run_id}/cases/{case_id}` | Full case replay |
| GET | `/runs/{run_id}/events` | SSE live event stream |

## Architecture

```
backend/app/
  core/domain/    -- Pure logic: schemas, scoring, metrics
  usecases/       -- Orchestration: run_eval, compute_summary
  infra/          -- IO adapters: db, llm, debate, sse
  api/            -- FastAPI routes
```

## Datasets

4 prebuilt datasets with 20 cases each (80 total):
- `jobs_layoffs` -- Tech layoffs and employment trends
- `football` -- Football/soccer analytics
- `climate` -- Climate science claims
- `entertainment` -- Streaming, gaming, music industry

## Scoring

| Component | Points | Description |
|-----------|--------|-------------|
| Correctness | 0-50 | Verdict matches ground truth |
| Grounding | 0-25 | Valid evidence citations |
| Calibration | 0-10 | Confidence vs correctness |
| Falsifiable | 0-15 | Reasoning quality |

**PASS per case**: score >= 80 + no critical fails

**PASS per model**: >= 80% pass rate + 0 critical fails + >= 70% on high-pressure cases

## Testing

```bash
cd backend
pytest tests/ -v
```

## License

MIT
