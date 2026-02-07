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
8. [Production Deployment](#8-production-deployment)
   - 8a. Architecture Overview
   - 8b. Backend Production Build
   - 8c. Frontend Production Build
   - 8d. Docker Compose Production
   - 8e. Cloud / VPS Deployment Checklist
   - 8f. Reverse Proxy (Nginx)
9. [API Verification](#9-api-verification)
10. [Troubleshooting](#10-troubleshooting)

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

---

## 2. Repository Setup

```bash
git clone <repo-url>
cd galileo-arena          # project root (AIGalileoTest)
```

Directory layout:

```
galileo-arena/
├── backend/              # FastAPI (Python 3.12)
│   ├── app/              # Application code
│   │   ├── api/          # FastAPI routes
│   │   ├── config.py     # pydantic-settings (reads .env)
│   │   ├── core/domain/  # Pure logic: schemas, scoring, metrics
│   │   ├── infra/        # IO adapters: db, llm, debate, sse
│   │   └── usecases/     # Orchestration: run_eval, compute_summary
│   ├── alembic/          # Database migrations
│   ├── datasets/         # 4 prebuilt JSON datasets (80 cases)
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

```bash
cp backend/.env.example backend/.env
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

> **\*** At least **one** LLM provider API key is required to run evaluations.

### Frontend

| Variable              | Required | Default                  | Description               |
| --------------------- | -------- | ------------------------ | ------------------------- |
| `NEXT_PUBLIC_API_URL` | No       | `http://localhost:8000`  | Backend API base URL      |

The frontend reads this at build time. For local dev the default is usually correct.

---

## 4. Local Development (Debugging)

### 4a. Database (PostgreSQL)

**Option A — Docker (recommended for local dev):**

```bash
docker run -d \
  --name galileo-pg \
  -e POSTGRES_USER=galileo \
  -e POSTGRES_PASSWORD=galileo_pass \
  -e POSTGRES_DB=galileo_arena \
  -p 5432:5432 \
  postgres:16-alpine
```

**Option B — System PostgreSQL:**

```sql
-- Connect as superuser and run:
CREATE USER galileo WITH PASSWORD 'galileo_pass';
CREATE DATABASE galileo_arena OWNER galileo;
```

**Verify connectivity:**

```bash
psql -h localhost -U galileo -d galileo_arena -c "SELECT 1;"
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

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — set at least one LLM API key

# 4. Run database migrations
alembic upgrade head

# 5. Start the dev server (with hot-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On startup the backend will:
- Create/verify database tables
- Load all 4 datasets (80 cases) into PostgreSQL
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

| Terminal | Directory  | Command                                           |
| -------- | ---------- | ------------------------------------------------- |
| 1        | (root)     | `docker run ... postgres:16-alpine` (see 4a)      |
| 2        | `backend/` | `.venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload` |
| 3        | `frontend/`| `npm run dev`                                     |

Then open `http://localhost:3000` in your browser.

---

## 5. Docker Compose (One-Command Setup)

The simplest way to run the full stack:

```bash
# 1. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

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

> **Dev convenience:** On startup, `init_db()` in `session.py` calls `Base.metadata.create_all` to auto-create tables. For production always use Alembic migrations.

---

## 7. Running Tests

```bash
cd backend

# Activate venv first
source .venv/bin/activate    # or .venv\Scripts\Activate.ps1

# Run all tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_scoring.py -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=term-missing
```

Test files:
- `test_scoring.py` — Scoring logic (unit)
- `test_debate_runner.py` — Debate runner (unit)
- `test_toml_serde.py` — TOML serialisation (unit)
- `test_validation.py` — Schema validation (unit)

> Tests use pure unit fixtures from `conftest.py` and do not require a running database.

---

## 8. Production Deployment

### 8a. Architecture Overview

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

### 8b. Backend Production Build

```dockerfile
# backend/Dockerfile (already provided)
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Production adjustments:
- **Workers:** Add `--workers 4` (or use `gunicorn` with `uvicorn.workers.UvicornWorker`)
- **No reload:** Remove `--reload` flag
- **Log level:** Set `LOG_LEVEL=WARNING` in `.env`

```bash
# Build
docker build -t galileo-backend ./backend

# Run
docker run -d \
  --name galileo-backend \
  -p 8000:8000 \
  --env-file backend/.env \
  -e DATABASE_URL=postgresql+asyncpg://galileo:STRONG_PASSWORD@db-host:5432/galileo_arena \
  galileo-backend
```

### 8c. Frontend Production Build

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

> **Important:** `NEXT_PUBLIC_*` variables are inlined at **build time** by Next.js. Pass them as build args or set them before `npm run build`.

### 8d. Docker Compose Production

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

```bash
# Deploy
POSTGRES_PASSWORD=super_secret_password docker-compose -f docker-compose.prod.yml up --build -d

# Run migrations inside the backend container
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### 8e. Cloud / VPS Deployment Checklist

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

### 8f. Reverse Proxy (Nginx)

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

## 9. API Verification

After starting the stack, verify everything is working:

```bash
# Health check
curl http://localhost:8000/health
# Expected: {"status":"ok"}

# List datasets (should return 4 prebuilt datasets)
curl http://localhost:8000/datasets
# Expected: [{"id":"climate_v1", ...}, {"id":"football_v1", ...}, ...]

# Swagger UI (open in browser)
# http://localhost:8000/docs

# Frontend (open in browser)
# http://localhost:3000
```

---

## 10. Troubleshooting

### Database connection refused

```
sqlalchemy.exc.OperationalError: connection refused
```

- **Local:** Ensure PostgreSQL is running on port 5432. Check with `pg_isready -h localhost`.
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

```bash
cd backend
alembic upgrade head
```

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

```bash
# Find and kill the process (Windows PowerShell)
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
Stop-Process -Id <PID>

# Linux / macOS
lsof -i :8000
kill -9 <PID>
```
