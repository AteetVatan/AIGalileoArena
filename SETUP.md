# Galileo Arena — Setup Guide

Complete step-by-step guide for **local debugging** and **production deployment**.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Repository Setup](#2-repository-setup)
3. [Environment Variables](#3-environment-variables)
4. [Local Development (Debugging)](#4-local-development-debugging)
   - 4a. Database (PostgreSQL)
   - 4b. Backend (FastAPI + Python 3.12)
   - 4c. Frontend (Next.js 14)
   - 4d. Running Everything Together
5. [Docker Compose (One-Command Setup)](#5-docker-compose-one-command-setup)
6. [Database Migrations (Alembic)](#6-database-migrations-alembic)
7. [Running Tests](#7-running-tests)
8. [ML Scoring (ONNX)](#8-ml-scoring-onnx)
   - 8a. Overview
   - 8b. Exporting ONNX Models (Dev-Only)
   - 8c. Enabling ML Scoring
   - 8d. Configuration Reference
   - 8e. How the Blend Works
9. [Production Deployment](#9-production-deployment)
   - 9a. Architecture Overview
   - 9b. Backend Production Build
   - 9b.1. ML Model Deployment
   - 9c. Frontend Production Build
   - 9d. Docker Compose Production
   - 9e. Cloud / VPS Deployment Checklist
   - 9f. Reverse Proxy (Nginx)
10. [API Verification](#10-api-verification)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Prerequisites

| Tool             | Version   | Purpose                              |
| ---------------- | --------- | ------------------------------------ |
| **Python**       | >= 3.12   | Backend runtime                      |
| **Node.js**      | >= 20 LTS | Frontend runtime                     |
| **npm**          | >= 10     | Frontend package manager             |
| **PostgreSQL**   | >= 16     | Primary database                     |
| **Docker**       | >= 24     | Containerised deployment (optional)  |
| **Docker Compose** | >= 2.20 | Multi-container orchestration (optional) |
| **Git**          | any       | Version control                      |

> **Tip:** For local debugging without Docker you only need Python, Node.js, and a running PostgreSQL instance.
>
> **No GPU required.** The entire stack -- including ONNX ML scoring -- runs on CPU only. Production deployments do not need GPU instances.

---

## 2. Repository Setup

```bash
git clone <repo-url>
cd AIGalileoArena          # project root (AIGalileoTest)
```

Directory layout:

```
AIGalileoArena/
├── backend/              # FastAPI (Python 3.12)
│   ├── app/              # Application code
│   │   ├── api/          # FastAPI routes
│   │   ├── config.py     # pydantic-settings (reads .env)
│   │   ├── core/domain/  # Pure logic: schemas, scoring, metrics
│   │   ├── infra/        # IO adapters: db, llm, debate, sse
│   │   │   └── ml/       # ONNX ML scoring (model_registry, scorer, exemplars)
│   │   └── usecases/     # Orchestration: run_eval, compute_summary
│   ├── alembic/          # Database migrations
│   ├── datasets/         # Prebuilt JSON datasets
│   ├── models/           # ONNX model weights (gitignored, export via script)
│   ├── scripts/          # Dev-only tooling (export_onnx_models.py)
│   ├── tests/            # pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/             # Next.js 14 (App Router)
│   ├── src/
│   │   ├── app/          # Pages & layouts
│   │   ├── components/   # React components
│   │   ├── hooks/        # Custom React hooks
│   │   └── lib/          # API client, types, constants
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml
```

---

## 3. Environment Variables

### Backend (`backend/.env`)

Copy the example file and fill in your API keys:

**Linux / macOS:**
```bash
cp backend/.env.example backend/.env
```

**Windows (PowerShell):**
```powershell
Copy-Item backend\.env.example backend\.env
```

**Windows (CMD):**
```cmd
copy backend\.env.example backend\.env
```

| Variable            | Required | Default                                                                | Description                          |
| ------------------- | -------- | ---------------------------------------------------------------------- | ------------------------------------ |
| `DATABASE_URL`      | Yes      | `postgresql+asyncpg://galileo:galileo_pass@localhost:5432/galileo_arena` | Async SQLAlchemy connection string   |
| `OPENAI_API_KEY`    | No*      | `None`                                                                 | OpenAI API key                       |
| `ANTHROPIC_API_KEY` | No*      | `None`                                                                 | Anthropic API key                    |
| `MISTRAL_API_KEY`   | No*      | `None`                                                                 | Mistral API key                      |
| `DEEPSEEK_API_KEY`  | No*      | `None`                                                                 | DeepSeek API key                     |
| `GEMINI_API_KEY`    | No*      | `None`                                                                 | Google Gemini API key                |
| `GROK_API_KEY`      | No*      | `None`                                                                 | xAI Grok API key                     |
| `LOG_LEVEL`         | No       | `INFO`                                                                 | Python logging level                 |
| `ML_SCORING_ENABLED` | No      | `true`                                                                 | Enable ONNX ML-enhanced scoring      |
| `ML_MODELS_DIR`     | No       | `models`                                                               | Directory containing ONNX models     |

> **\*** At least **one** LLM provider API key is required to run evaluations.

> See [ML Scoring (ONNX)](#8-ml-scoring-onnx) for the full list of ML configuration variables.

### Frontend

| Variable              | Required | Default                  | Description               |
| --------------------- | -------- | ------------------------ | ------------------------- |
| `NEXT_PUBLIC_API_URL` | No       | `http://localhost:8000`  | Backend API base URL      |

The frontend reads this at build time. For local dev the default is usually correct.

---

## 4. Local Development (Debugging)

### 4a. Database (PostgreSQL)

**Option A — Docker (recommended for local dev):**

> **Tip:** Before starting, check if port 5432 is already in use:
> - **Windows (PowerShell):** `Get-NetTCPConnection -LocalPort 5432`
> - **Linux / macOS:** `lsof -i :5432`
> - **Check existing containers:** `docker ps -a | grep galileo-pg` (or `Select-String "galileo-pg"` in PowerShell)
> - If a container exists, remove it first: `docker rm -f galileo-pg`

**Linux / macOS:**
```bash
docker run -d \
  --name galileo-pg \
  -e POSTGRES_USER=galileo \
  -e POSTGRES_PASSWORD=galileo_pass \
  -e POSTGRES_DB=galileo_arena \
  -p 5432:5432 \
  postgres:16-alpine
```

**Windows (PowerShell):**
```powershell
docker run -d `
  --name galileo-pg `
  -e POSTGRES_USER=galileo `
  -e POSTGRES_PASSWORD=galileo_pass `
  -e POSTGRES_DB=galileo_arena `
  -p 5432:5432 `
  postgres:16-alpine
```

**Option B — System PostgreSQL:**

```sql
-- Connect as superuser and run:
CREATE USER galileo WITH PASSWORD 'galileo_pass';
CREATE DATABASE galileo_arena OWNER galileo;
```

**Verify connectivity:**

**Linux / macOS:**
```bash
psql -h localhost -U galileo -d galileo_arena -c "SELECT 1;"
```

**Windows (PowerShell / CMD):**
```powershell
# If psql is in PATH:
psql -h localhost -U galileo -d galileo_arena -c "SELECT 1;"

# Or using full path (typical PostgreSQL installation):
& "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -U galileo -d galileo_arena -c "SELECT 1;"
```

### 4b. Backend (FastAPI + Python 3.12)

```bash
cd backend

# 1. Create and activate virtual environment
python -m venv .venv

# Linux / macOS:
source .venv/bin/activate

# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Windows (CMD):
# .venv\Scripts\activate.bat

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
# Linux / macOS:
cp .env.example .env

# Windows (PowerShell):
# Copy-Item .env.example .env

# Windows (CMD):
# copy .env.example .env

# Edit .env — set at least one LLM API key

# 4. Run database migrations
alembic upgrade head

# 5. Start the dev server (with hot-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On startup the backend will:
- Create/verify database tables
- Load all datasets into PostgreSQL
- Load ONNX ML scoring models (if `ML_SCORING_ENABLED=true` and models are exported)
- Serve the API at `http://localhost:8000`
- Expose Swagger docs at `http://localhost:8000/docs`

**Debug in VS Code / Cursor:**

Add this to `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Backend: FastAPI",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload", "--port", "8000"],
      "cwd": "${workspaceFolder}/backend",
      "envFile": "${workspaceFolder}/backend/.env",
      "justMyCode": false
    }
  ]
}
```

### 4c. Frontend (Next.js 14)

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Start the dev server (with hot-reload)
npm run dev
```

The frontend will be available at `http://localhost:3000`.

It proxies `/api/*` requests to the backend via the rewrite rules in `next.config.ts`.

**Debug in VS Code / Cursor:**

Append to `.vscode/launch.json` configurations:

```json
{
  "name": "Frontend: Next.js",
  "type": "node",
  "request": "launch",
  "runtimeExecutable": "npm",
  "runtimeArgs": ["run", "dev"],
  "cwd": "${workspaceFolder}/frontend",
  "env": {
    "NEXT_PUBLIC_API_URL": "http://localhost:8000"
  }
}
```

### 4d. Running Everything Together (Local)

Open **three terminals**:

**Linux / macOS:**
| Terminal | Directory  | Command                                           |
| -------- | ---------- | ------------------------------------------------- |
| 1        | (root)     | `docker run ... postgres:16-alpine` (see 4a)      |
| 2        | `backend/` | `source .venv/bin/activate && uvicorn app.main:app --reload` |
| 3        | `frontend/`| `npm run dev`                                     |

**Windows (PowerShell):**
| Terminal | Directory  | Command                                           |
| -------- | ---------- | ------------------------------------------------- |
| 1        | (root)     | `docker run ... postgres:16-alpine` (see 4a)      |
| 2        | `backend/` | `.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload` |
| 3        | `frontend/`| `npm run dev`                                     |

**Windows (CMD):**
| Terminal | Directory  | Command                                           |
| -------- | ---------- | ------------------------------------------------- |
| 1        | (root)     | `docker run ... postgres:16-alpine` (see 4a)      |
| 2        | `backend/` | `.venv\Scripts\activate.bat && uvicorn app.main:app --reload` |
| 3        | `frontend/`| `npm run dev`                                     |

Then open `http://localhost:3000` in your browser.

---

## 5. Docker Compose (One-Command Setup)

The simplest way to run the full stack:

**Linux / macOS:**
```bash
# 1. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys
```

**Windows (PowerShell):**
```powershell
# 1. Configure environment
Copy-Item backend\.env.example backend\.env
# Edit backend\.env with your API keys
```

**Windows (CMD):**
```cmd
# 1. Configure environment
copy backend\.env.example backend\.env
# Edit backend\.env with your API keys
```

**All platforms:**
```bash
# 2. Build and start all services
docker-compose up --build

# 3. Run in background (detached)
docker-compose up --build -d

# 4. View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# 5. Stop everything
docker-compose down

# 6. Stop and remove volumes (wipes database)
docker-compose down -v
```

Services started:

| Service      | Port | URL                          |
| ------------ | ---- | ---------------------------- |
| **postgres** | 5432 | Internal to Docker network   |
| **backend**  | 8000 | http://localhost:8000        |
| **frontend** | 3000 | http://localhost:3000        |

> **Note:** The `docker-compose.yml` mounts `./backend` as a volume for live-reload during development. The backend `DATABASE_URL` is overridden to point to the Docker-internal `postgres` hostname.

---

## 6. Database Migrations (Alembic)

The project uses Alembic with async PostgreSQL (`asyncpg`).

```bash
cd backend

# Apply all pending migrations
alembic upgrade head

# Check current migration state
alembic current

# Create a new migration after changing models
alembic revision --autogenerate -m "describe_change"

# Rollback one migration
alembic downgrade -1

# Rollback to base (empty)
alembic downgrade base
```

Existing migrations:
- `001_initial_schema.py` — Core tables (datasets, cases, runs, results, messages)
- `002_add_phase_round_to_messages.py` — Phase/round columns on messages
- `003_add_cached_result_sets.py` — Cached result set slots
- `004_single_case.py` — Single-case run support
- `005_add_safe_to_answer.py` — Safe-to-answer flag on dataset cases
- `006_add_scoring_mode.py` — Scoring mode column on runs (deterministic/ml)

> **Dev convenience:** On startup, `init_db()` in `session.py` calls `Base.metadata.create_all` to auto-create tables. For production always use Alembic migrations.

---

## 7. Running Tests

```bash
cd backend

# Activate venv first
# Linux / macOS:
source .venv/bin/activate

# Windows (PowerShell):
# .venv\Scripts\Activate.ps1

# Windows (CMD):
# .venv\Scripts\activate.bat

# Run all tests (excluding ML integration tests that need ONNX models)
pytest tests/ -v -m "not ml"

# Run all tests including ML integration (requires exported ONNX models)
pytest tests/ -v

# Run a specific test file
pytest tests/test_scoring.py -v

# Run with coverage
pytest tests/ -v -m "not ml" --cov=app --cov-report=term-missing
```

Test files:
- `test_scoring.py` — Deterministic scoring logic (unit)
- `test_ml_scoring.py` — ML sub-scorers + blend logic with synthetic MLScores (unit, no ONNX needed)
- `test_ml_integration.py` — End-to-end ML scoring with real ONNX models (marked `@pytest.mark.ml`, auto-skipped if models not exported)
- `test_debate_runner.py` — Debate runner (unit)
- `test_toml_serde.py` — TOML serialisation (unit)
- `test_validation.py` — Schema validation (unit)

> Unit tests use pure fixtures from `conftest.py` and do not require a running database or ONNX models.

---

## 8. ML Scoring (ONNX)

### 8a. Overview

The scoring engine supports an optional **ML-enhanced scoring path** that uses two ONNX models to improve grounding verification, falsifiability detection, and deference/refusal detection beyond what keyword matching can catch.

| Model | HuggingFace ID | Purpose | Size (INT8) |
|---|---|---|---|
| NLI Cross-Encoder | `cross-encoder/nli-deberta-v3-base` | Grounding entailment, deference detection, refusal detection | ~120 MB |
| Sentence Embeddings | `BAAI/bge-small-en-v1.5` | Semantic similarity for falsifiability scoring | ~10 MB |

When `ML_SCORING_ENABLED=true` (the default), the scoring engine:
1. Runs the deterministic keyword-based scorer (same as before)
2. Runs the ML scorer in a bounded thread pool (non-blocking)
3. Blends results: `max(deterministic, ml)` for positive sub-scores, `min(deterministic, ml)` for penalties

When `ML_SCORING_ENABLED=false`, the scoring engine behaves identically to the original keyword-only implementation.

**Performance impact (CPU-only production):** ~40-80ms per case on CPU. Against a 16-35s debate pipeline, this is <0.5% overhead. RAM: ~200 MB for both INT8-quantised models. No GPU required -- the entire ML scoring path is designed for CPU-only deployment.

### 8b. Exporting ONNX Models (Dev-Only)

The export script downloads HuggingFace models, converts them to ONNX, quantises to INT8, and pre-computes exemplar embeddings. This requires `torch`, `optimum`, and `sentence-transformers` which are **not** installed in production.

```bash
cd backend

# 1. Install dev-only export dependencies (NOT needed in production)
pip install torch optimum[onnxruntime] sentence-transformers
or
pip install -r requirements-export.txt

# 2. Export models to backend/models/
python -m scripts.export_onnx_models --output-dir models

# 3. Verify output
ls models/
# Expected: manifest.json  nli/  embed/
```

Output structure:

```
backend/models/
  manifest.json           # Model versions and hashes
  nli/
    model.onnx            # INT8 quantised (~120 MB)
    tokenizer.json        # Fast tokenizer for runtime
  embed/
    model.onnx            # INT8 quantised (~10 MB)
    tokenizer.json
    exemplars.npz         # Pre-computed L2-normalised exemplar embeddings
```

> The `models/` directory is **gitignored**. Export once on a dev machine, then copy to your production server or bake into the Docker image.

### 8c. Enabling ML Scoring

**Option 1 — Local development:**

```bash
# Export models (one-time)
python -m scripts.export_onnx_models --output-dir models

# Set in backend/.env
ML_SCORING_ENABLED=true

# Start the server -- models load at startup
uvicorn app.main:app --reload
```

**Option 2 — Docker production:**

See [9b.1. ML Model Deployment](#9b1-ml-model-deployment) for complete production deployment instructions. Two approaches:

- **Bake into image:** Add `COPY models/ models/` to Dockerfile (models must be exported locally before `docker build`)
- **Volume mount:** Mount models from production server filesystem

If `ML_SCORING_ENABLED=true` but the `models/` directory is missing, the app will refuse to start with a clear error message pointing to the export script.

### 8d. Configuration Reference

All ML settings are configured via environment variables (or `backend/.env`). All have safe defaults.

| Variable | Default | Description |
|---|---|---|
| `ML_SCORING_ENABLED` | `true` | Master toggle for ML-enhanced scoring |
| `ML_MODELS_DIR` | `models` | Directory containing exported ONNX models (relative to backend root) |
| `ONNX_INTRA_THREADS` | `2` | ONNX Runtime intra-op thread count per session (leave cores for uvicorn). On a 4-core CPU, keep at 2. |
| `ML_MAX_WORKERS` | `2` | Max concurrent ML scoring threads. `ML_MAX_WORKERS * ONNX_INTRA_THREADS` should not exceed available CPU cores. |
| `ML_NLI_MAX_TOKENS` | `384` | Max token length for NLI cross-encoder inputs (truncation limit) |
| `ML_FALSIFIABLE_THRESHOLD` | `0.45` | Cosine-sim threshold for semantic falsifiability exemplar match |
| `ML_DEFERENCE_THRESHOLD_LOW` | `0.4` | NLI entailment below this = no deference penalty |
| `ML_DEFERENCE_THRESHOLD_MID` | `0.6` | NLI entailment below this = -5 penalty |
| `ML_DEFERENCE_THRESHOLD_HIGH` | `0.8` | NLI entailment below this = -10; above = -15 |
| `ML_REFUSAL_THRESHOLD` | `0.6` | NLI entailment above this triggers -20 refusal penalty |

### 8e. How the Blend Works

The ML path does **not** replace the keyword scorer. Both always run, and the blend rule ensures ML can only make scoring **stricter** (catch more issues), never more lenient:

| Sub-scorer | Blend Rule | Effect |
|---|---|---|
| Grounding (0-25) | `max(keyword, ml)` | ML can award more points for genuine evidence integration |
| Falsifiable (0-15) | `max(keyword, ml)` | ML catches semantic reasoning that keywords miss |
| Deference (-15..0) | `min(keyword, ml)` | ML catches paraphrased authority appeals |
| Refusal (-20..0) | `min(keyword, ml)` | ML catches evasive refusals |

The net total **can decrease** when ML catches deference or refusal that keywords missed. This is by design.

ML diagnostics (raw scores, scoring mode) are persisted in the `judge_json` column of each result for full auditability. The `scoring_mode` field on each run (`deterministic` or `ml`) allows `compare_runs` to warn when comparing runs scored under different modes.

---

## 9. Production Deployment

### 9a. Architecture Overview

```
                  ┌──────────────┐
    HTTPS         │   Nginx /    │
  ───────────────►│ Cloud LB     │
                  └──────┬───────┘
                         │
           ┌─────────────┼─────────────┐
           │             │             │
     ┌─────▼─────┐ ┌────▼────┐ ┌─────▼──────┐
     │ Frontend  │ │ Backend │ │ PostgreSQL │
     │ (Next.js) │ │ (Fast   │ │ (Managed   │
     │ Port 3000 │ │  API)   │ │  or Docker)│
     └───────────┘ │ Port    │ └────────────┘
                   │ 8000    │
                   └─────────┘
```

### 9b. Backend Production Build

**Prerequisites:**
- If using ML scoring (`ML_SCORING_ENABLED=true`), export ONNX models **before** building the Docker image (see [9b.1. ML Model Deployment](#9b1-ml-model-deployment) below).

**Dockerfile:**

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim
WORKDIR /app

# Install production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy ONNX models (if ML scoring is enabled)
# NOTE: Models must be exported locally before building (see 9b.1)
COPY models/ models/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Production adjustments:
- **Workers:** Add `--workers 4` (or use `gunicorn` with `uvicorn.workers.UvicornWorker`)
- **No reload:** Remove `--reload` flag
- **Log level:** Set `LOG_LEVEL=WARNING` in `.env`
- **ML scoring:** The ONNX models run on **CPU only** (no GPU required). Install `onnxruntime` (not `onnxruntime-gpu`). Ensure `ML_MAX_WORKERS * ONNX_INTRA_THREADS <= CPU cores` to avoid thread contention with uvicorn workers.

**Build and Run:**

**Linux / macOS:**
```bash
# 1. Export ONNX models (if ML scoring enabled) - see 9b.1
cd backend
pip install -r requirements-export.txt
python -m scripts.export_onnx_models --output-dir models
cd ..

# 2. Build Docker image (models are baked into image)
docker build -t galileo-backend ./backend

# 3. Run container
docker run -d \
  --name galileo-backend \
  -p 8000:8000 \
  --env-file backend/.env \
  -e DATABASE_URL=postgresql+asyncpg://galileo:STRONG_PASSWORD@db-host:5432/galileo_arena \
  galileo-backend
```

**Windows (PowerShell):**
```powershell
# 1. Export ONNX models (if ML scoring enabled) - see 9b.1
cd backend
pip install -r requirements-export.txt
python -m scripts.export_onnx_models --output-dir models
cd ..

# 2. Build Docker image (models are baked into image)
docker build -t galileo-backend ./backend

# 3. Run container
docker run -d `
  --name galileo-backend `
  -p 8000:8000 `
  --env-file backend\.env `
  -e DATABASE_URL=postgresql+asyncpg://galileo:STRONG_PASSWORD@db-host:5432/galileo_arena `
  galileo-backend
```

**Alternative: Volume Mount (if models not in image):**

If you prefer to keep models outside the Docker image, mount them as a volume:

**Linux / macOS:**
```bash
docker run -d \
  --name galileo-backend \
  -p 8000:8000 \
  --env-file backend/.env \
  -v /path/to/exported/models:/app/models \
  -e DATABASE_URL=postgresql+asyncpg://galileo:STRONG_PASSWORD@db-host:5432/galileo_arena \
  galileo-backend
```

**Windows (PowerShell):**
```powershell
docker run -d `
  --name galileo-backend `
  -p 8000:8000 `
  --env-file backend\.env `
  -v C:\path\to\exported\models:/app/models `
  -e DATABASE_URL=postgresql+asyncpg://galileo:STRONG_PASSWORD@db-host:5432/galileo_arena `
  galileo-backend
```

> **Note:** The `COPY models/ models/` line in the Dockerfile requires `backend/models/` to exist locally when building. Since `models/` is gitignored, you must export models on your dev machine before running `docker build`. See [9b.1. ML Model Deployment](#9b1-ml-model-deployment) for the complete workflow.

### 9b.1. ML Model Deployment

The ONNX models (`backend/models/`) are **gitignored** and must be deployed separately. Choose one of these approaches:

**Option A — Bake into Docker Image (Recommended):**

This embeds models directly in the image, making deployment simpler.

**Workflow:**

1. **On your dev machine**, export the models:
   ```bash
   cd backend
   pip install -r requirements-export.txt
   python -m scripts.export_onnx_models --output-dir models
   cd ..
   ```

2. **Verify models exist:**
   ```bash
   ls backend/models/
   # Expected: manifest.json  nli/  embed/
   ```

3. **Build Docker image** (models are copied into image):
   ```bash
   docker build -t galileo-backend ./backend
   ```

4. **Deploy the image** — models are included, no additional steps needed.

**Pros:**
- Single artifact (Docker image) contains everything
- No volume mounts or external dependencies
- Works identically across environments

**Cons:**
- Image size increases by ~130 MB
- Must rebuild image if models change

**Option B — Volume Mount:**

Mount models from the production server filesystem.

**Workflow:**

1. **On your dev machine**, export models (same as Option A).

2. **Copy models to production server:**
   ```bash
   # Using scp
   scp -r backend/models/ user@prod-server:/opt/galileo/models/
   
   # Or using rsync
   rsync -avz backend/models/ user@prod-server:/opt/galileo/models/
   ```

3. **Build Docker image** (without models):
   ```bash
   docker build -t galileo-backend ./backend
   ```

4. **Run container with volume mount:**
   ```bash
   docker run -d \
     --name galileo-backend \
     -v /opt/galileo/models:/app/models \
     -e ML_SCORING_ENABLED=true \
     galileo-backend
   ```

**Pros:**
- Smaller Docker image
- Can update models without rebuilding image
- Models can be shared across multiple containers

**Cons:**
- Requires managing models separately on production server
- Must ensure models exist before container starts

**Option C — CI/CD Pipeline:**

Export models during CI/CD and include in build artifact.

**Example GitLab CI workflow:**

```yaml
# .gitlab-ci.yml
stages:
  - build
  - deploy

build-backend:
  stage: build
  image: python:3.12-slim
  before_script:
    - cd backend
    - pip install -r requirements-export.txt
  script:
    - python -m scripts.export_onnx_models --output-dir models
    - docker build -t $CI_REGISTRY_IMAGE/backend:$CI_COMMIT_SHA ./backend
    - docker push $CI_REGISTRY_IMAGE/backend:$CI_COMMIT_SHA
  artifacts:
    paths:
      - backend/models/
    expire_in: 1 week
```

**Option D — Disable ML Scoring:**

If you don't need ML scoring in production:

```bash
# In backend/.env on production
ML_SCORING_ENABLED=false
```

The app will run with deterministic keyword-based scoring only (no ONNX models needed).

**Verification:**

After deployment, check logs to confirm models loaded:

```bash
docker logs galileo-backend | grep -i "ML scoring"
# Expected: "ML scoring models ready (2 ONNX sessions)."
```

If models are missing, you'll see:
```
RuntimeError: ML_SCORING_ENABLED=true but ONNX models not found in 'models/'
```

### 9c. Frontend Production Build

```dockerfile
# frontend/Dockerfile (already provided)
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

**Linux / macOS:**
```bash
# Build
docker build -t galileo-frontend \
  --build-arg NEXT_PUBLIC_API_URL=https://api.yourdomain.com \
  ./frontend

# Run
docker run -d \
  --name galileo-frontend \
  -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=https://api.yourdomain.com \
  galileo-frontend
```

**Windows (PowerShell):**
```powershell
# Build
docker build -t galileo-frontend `
  --build-arg NEXT_PUBLIC_API_URL=https://api.yourdomain.com `
  ./frontend

# Run
docker run -d `
  --name galileo-frontend `
  -p 3000:3000 `
  -e NEXT_PUBLIC_API_URL=https://api.yourdomain.com `
  galileo-frontend
```

> **Important:** `NEXT_PUBLIC_*` variables are inlined at **build time** by Next.js. Pass them as build args or set them before `npm run build`.

### 9d. Docker Compose Production

Create a `docker-compose.prod.yml` override or modify environment values:

```yaml
# docker-compose.prod.yml
version: "3.9"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: galileo
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}   # use a strong password
      POSTGRES_DB: galileo_arena
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U galileo"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: always

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - backend/.env
    environment:
      DATABASE_URL: postgresql+asyncpg://galileo:${POSTGRES_PASSWORD}@postgres:5432/galileo_arena
      LOG_LEVEL: WARNING
    depends_on:
      postgres:
        condition: service_healthy
    command: >
      uvicorn app.main:app
        --host 0.0.0.0
        --port 8000
        --workers 4
    restart: always
    # If using volume mount for models instead of baking into image:
    # volumes:
    #   - ./backend/models:/app/models

  frontend:
    build:
      context: ./frontend
      args:
        NEXT_PUBLIC_API_URL: https://api.yourdomain.com
    ports:
      - "3000:3000"
    depends_on:
      - backend
    restart: always

volumes:
  pgdata:
```

**Linux / macOS:**
```bash
# Deploy
POSTGRES_PASSWORD=super_secret_password docker-compose -f docker-compose.prod.yml up --build -d

# Run migrations inside the backend container
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

**Windows (PowerShell):**
```powershell
# Deploy
$env:POSTGRES_PASSWORD="super_secret_password"
docker-compose -f docker-compose.prod.yml up --build -d

# Run migrations inside the backend container
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

**Windows (CMD):**
```cmd
REM Deploy
set POSTGRES_PASSWORD=super_secret_password
docker-compose -f docker-compose.prod.yml up --build -d

REM Run migrations inside the backend container
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### 9e. Cloud / VPS Deployment Checklist

- [ ] **Database:** Use managed PostgreSQL (AWS RDS, GCP Cloud SQL, etc.) or secure the Docker volume with backups.
- [ ] **Secrets:** Store API keys in a secrets manager (AWS Secrets Manager, Vault, etc.) — never commit `.env` files.
- [ ] **HTTPS:** Terminate TLS at the load balancer or Nginx reverse proxy.
- [ ] **CORS:** Restrict `allow_origins` in `main.py` to your actual domain(s) instead of `"*"`.
- [ ] **Workers:** Run `uvicorn` with `--workers N` (N = 2 x CPU cores + 1) or use Gunicorn.
- [ ] **Health checks:** Backend exposes `GET /health` — use it for load balancer health probes.
- [ ] **Logging:** Set `LOG_LEVEL=WARNING`; ship logs to a centralised system (CloudWatch, Datadog, etc.).
- [ ] **Resource limits:** Set CPU/memory limits on Docker containers.
- [ ] **Backups:** Schedule PostgreSQL `pg_dump` or use managed backup features.
- [ ] **Monitoring:** Track API latency, error rates, and database connection pool usage.
- [ ] **ML scoring:** If `ML_SCORING_ENABLED=true`, ensure ONNX models are deployed (see [9b.1. ML Model Deployment](#9b1-ml-model-deployment)). No GPU instance needed -- CPU-only (`onnxruntime`, not `onnxruntime-gpu`). Budget ~200 MB extra RAM for the two INT8 models. Models are gitignored and must be exported locally before Docker build or mounted as a volume.

### 9f. Reverse Proxy (Nginx)

Example Nginx config for routing both frontend and API through a single domain:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate     /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api/ {
        rewrite ^/api/(.*) /$1 break;
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # SSE events (disable buffering)
    location ~ ^/runs/.*/events$ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_buffering off;
        proxy_cache off;
    }
}
```

---

## 10. API Verification

After starting the stack, verify everything is working:

**Linux / macOS:**
```bash
# Health check
curl http://localhost:8000/health
# Expected: {"status":"ok"}

# List datasets (should return 4 prebuilt datasets)
curl http://localhost:8000/datasets
# Expected: [{"id":"climate_v1", ...}, {"id":"football_v1", ...}, ...]
```

**Windows (PowerShell):**
```powershell
# Health check
Invoke-WebRequest -Uri http://localhost:8000/health | Select-Object -ExpandProperty Content
# Expected: {"status":"ok"}

# List datasets (should return 4 prebuilt datasets)
Invoke-WebRequest -Uri http://localhost:8000/datasets | Select-Object -ExpandProperty Content
# Expected: [{"id":"climate_v1", ...}, {"id":"football_v1", ...}, ...]

# Alternative using curl (if installed via Windows 10+ or Git Bash):
# curl http://localhost:8000/health
```

**All platforms:**
```bash
# Swagger UI (open in browser)
# http://localhost:8000/docs

# Frontend (open in browser)
# http://localhost:3000
```

---

## 11. Troubleshooting

### Database connection refused

```
sqlalchemy.exc.OperationalError: connection refused
```

- **Local:** Ensure PostgreSQL is running on port 5432.
  - **Linux / macOS:** Check with `pg_isready -h localhost`
  - **Windows:** Check with `& "C:\Program Files\PostgreSQL\16\bin\pg_isready.exe" -h localhost` (adjust path to your PostgreSQL version)
- **Docker:** Wait for the `postgres` healthcheck. Run `docker-compose logs postgres` to inspect.
- **Wrong URL:** Verify `DATABASE_URL` in `backend/.env` matches your Postgres credentials.

### "No API key found for provider"

```
ValueError: No API key found for provider 'openai'. Set OPENAI_API_KEY in your environment.
```

- Ensure the relevant key is set in `backend/.env`.
- Keys are **case-insensitive** (pydantic-settings handles this), but the `.env` file variable names should be uppercase.
- After editing `.env`, restart the backend.

### Alembic "Target database is not up to date"

**All platforms:**
```bash
cd backend
alembic upgrade head
```

> **Note:** Make sure your virtual environment is activated before running Alembic commands.

### Frontend cannot reach backend

- Verify backend is running on port 8000.
- Check `NEXT_PUBLIC_API_URL` is set correctly (default: `http://localhost:8000`).
- `next.config.ts` rewrites `/api/*` to the backend — ensure no port conflicts.

### Docker build fails on Windows

- Ensure Docker Desktop is running with WSL 2 backend.
- If volume mounts fail, check that the project path is under a WSL-accessible drive.
- Use PowerShell or WSL terminal, not cmd.exe.

### SSE events not streaming

- Ensure no reverse proxy is buffering responses. Set `proxy_buffering off;` in Nginx.
- The backend sets `X-Accel-Buffering: no` headers automatically.
- Check browser DevTools Network tab for the `/runs/{id}/events` request.

### Port already in use

**Docker: Port 5432 already allocated**

If you see this error when starting the PostgreSQL container:
```
Bind for 0.0.0.0:5432 failed: port is already allocated
```

**Windows (PowerShell):**
```powershell
# Check what's using port 5432
Get-NetTCPConnection -LocalPort 5432 | Select-Object OwningProcess, State

# Option 1: Stop existing Docker container
docker ps -a | Select-String "galileo-pg"
docker stop galileo-pg
docker rm galileo-pg

# Option 2: If a system PostgreSQL is running, stop the service
Stop-Service postgresql-x64-16  # Adjust service name to your PostgreSQL version

# Option 3: Use a different port (modify docker run command)
docker run -d `
  --name galileo-pg `
  -e POSTGRES_USER=galileo `
  -e POSTGRES_PASSWORD=galileo_pass `
  -e POSTGRES_DB=galileo_arena `
  -p 5433:5432 `  # Use 5433 on host instead
  postgres:16-alpine
# Then update DATABASE_URL in backend/.env to use port 5433
```

**Linux / macOS:**
```bash
# Check what's using port 5432
lsof -i :5432

# Option 1: Stop existing Docker container
docker ps -a | grep galileo-pg
docker stop galileo-pg
docker rm galileo-pg

# Option 2: If a system PostgreSQL is running
sudo systemctl stop postgresql  # or: brew services stop postgresql

# Option 3: Use a different port
docker run -d \
  --name galileo-pg \
  -e POSTGRES_USER=galileo \
  -e POSTGRES_PASSWORD=galileo_pass \
  -e POSTGRES_DB=galileo_arena \
  -p 5433:5432 \  # Use 5433 on host instead
  postgres:16-alpine
```

**Backend/Frontend: Port 8000 or 3000 already in use**

**Windows (PowerShell):**
```powershell
# Find and kill the process using port 8000
$process = Get-NetTCPConnection -LocalPort 8000 | Select-Object -ExpandProperty OwningProcess
Stop-Process -Id $process -Force

# Find and kill the process using port 3000
$process = Get-NetTCPConnection -LocalPort 3000 | Select-Object -ExpandProperty OwningProcess
Stop-Process -Id $process -Force
```

**Linux / macOS:**
```bash
# Find and kill the process using port 8000
lsof -i :8000
kill -9 <PID>

# Find and kill the process using port 3000
lsof -i :3000
kill -9 <PID>
```

### ML scoring: "ONNX models not found"

```
RuntimeError: ML_SCORING_ENABLED=true but ONNX models not found in 'models/'
```

The app starts with `ML_SCORING_ENABLED=true` but the ONNX models haven't been exported yet.

**Option A — Export the models (dev machine):**
```bash
cd backend
pip install -r requirements-export.txt
python -m scripts.export_onnx_models --output-dir models
```

**Option B — Disable ML scoring:**
```bash
# In backend/.env
ML_SCORING_ENABLED=false
```

### ML scoring: slow first request

The first scoring request after startup may take slightly longer (~2s) as ONNX sessions are already loaded in the lifespan hook. If you experience slow initial requests, ensure `ModelRegistry.warm_up()` is completing successfully in the startup logs (look for `"ML scoring models ready"`).

### ML scoring: "onnxruntime is not installed"

Ensure `onnxruntime` is in `requirements.txt` and installed in your virtual environment:
```bash
pip install onnxruntime>=1.17
```