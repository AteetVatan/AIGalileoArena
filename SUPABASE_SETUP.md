# Supabase Setup Guide — AIGalileoArena

Complete walkthrough: create project → connect app → migrate schema → migrate data.

---

## 1. Create a Supabase Project

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard) and sign in (or create an account).
2. Click **New Project**.
3. Fill in:
   - **Organization**: pick or create one
   - **Project name**: e.g. `galileo-arena`
   - **Database password**: generate a strong one — **save it somewhere safe** (you'll need it for connection strings)
   - **Region**: pick the closest to you (e.g. `eu-central-1` for Europe)
4. Click **Create new project** and wait ~2 minutes for provisioning.

---

## 2. Collect Connection Strings

Go to **Project Settings → Database** (left sidebar → gear icon → Database).

You need **three** connection strings. Supabase shows them under **Connection String → URI**.

### 2a. Session Pooler (for app + migrations)

- Tab: **Connection Pooling** → Mode: **Session**
- Port: `5432`
- Host: `aws-0-<region>.pooler.supabase.com`
- Format:
  ```
  postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
  ```
- **Used for**: app runtime, Alembic migrations, CI/CD
- **Why**: supports prepared statements, works on IPv4 + IPv6

### 2b. Direct Connection (optional — admin only)

- Tab: **Connection Info** (not pooled)
- Port: `5432`
- Host: `db.<project-ref>.supabase.co`
- Format:
  ```
  postgresql://postgres.<project-ref>:<password>@db.<project-ref>.supabase.co:5432/postgres
  ```
- **Used for**: manual `psql` sessions, `pg_dump`/`pg_restore`
- **Caveat**: IPv6 by default — only use where IPv6 is confirmed

### 2c. Transaction Pooler (NOT recommended for this app)

- Port: `6543` — does NOT support prepared statements
- Only needed for serverless/autoscaling. Ignore for now.

---

## 3. Create a Dedicated App User

Don't run the app as `postgres` superuser. Create a least-privilege role.

1. Go to **SQL Editor** in the Supabase dashboard (left sidebar).
2. Run:

```sql
-- 1. Create the role
CREATE ROLE app_user WITH LOGIN PASSWORD 'REPLACE_WITH_STRONG_PASSWORD';

-- 2. Grant connect + schema usage
GRANT CONNECT ON DATABASE postgres TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;

-- 3. Grant DML on all current tables
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;

-- 4. Grant DML on future tables too
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user;

-- 5. Grant sequence usage (for autoincrement columns)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO app_user;
```

> **Note**: Run the `ALTER DEFAULT PRIVILEGES` statements again after running Alembic migrations, since the tables are created by `postgres`, not `app_user`.

3. Build the `app_user` connection string for the Session Pooler:
   ```
   postgresql://app_user.<project-ref>:REPLACE_WITH_STRONG_PASSWORD@aws-0-<region>.pooler.supabase.com:5432/postgres
   ```

---

## 4. Configure Environment Variables

Edit `backend/.env`:

```ini
# -----------------------------------------------
# Database — Supabase
# -----------------------------------------------

# App runtime (app_user, Session pooler)
DATABASE_URL=postgresql+asyncpg://app_user.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres

# Migrations / admin (postgres role, Session pooler)
DATABASE_URL_MIGRATIONS=postgresql+asyncpg://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
```

Replace `<project-ref>`, `<password>`, and `<region>` with your actual values from Step 2.

> **Important**: Keep the `postgresql+asyncpg://` prefix — it tells SQLAlchemy to use the `asyncpg` driver.

---

## 5. Run Alembic Migrations (Create Tables on Supabase)

```bash
cd backend
.venv\Scripts\activate

# This creates all 13 tables + indexes on Supabase
alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001, initial schema
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002, add phase round to messages
...
INFO  [alembic.runtime.migration] Running upgrade 006 -> 007, galileo analytics
```

**If you get an SSL error**: make sure you're using the Session pooler URL (not Direct) and that `alembic/env.py` has `connect_args={"ssl": "require"}` (already applied in the code changes).

### Re-grant privileges to `app_user`

After Alembic creates the tables (owned by `postgres`), re-run the grants in the SQL Editor:

```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
```

---

## 6. Verify App Connects to Supabase

```bash
cd backend
uvicorn app.main:app --reload
```

✅ Check for: no connection errors in terminal output  
✅ Open `http://localhost:8000/docs` → try `GET /datasets` → should return `[]` (empty, no data yet)

---

## 7. Migrate Existing Data from Local PostgreSQL

### 7a. Stop writes (freeze local DB)

Stop the backend if it's currently running against the local DB.

### 7b. Export data from local Docker PostgreSQL

Make sure your local Docker PostgreSQL is running:
```bash
docker compose up postgres -d
```

Set SSL mode and dump data only (schema is handled by Alembic):

```bash
# Custom format (best for large datasets)
pg_dump -h localhost -U galileo -d galileo_arena ^
  --data-only --format=custom ^
  -f galileo_data.dump
```

Or as plain SQL (simpler, reviewable):
```bash
pg_dump -h localhost -U galileo -d galileo_arena ^
  --data-only --column-inserts --format=plain ^
  -f galileo_data.sql
```

### 7c. Import into Supabase

Set SSL for CLI tools:
```bash
set PGSSLMODE=require
```

**From custom dump:**
```bash
pg_restore ^
  -h db.<project-ref>.supabase.co -p 5432 ^
  -U postgres -d postgres ^
  --data-only --no-owner --no-privileges ^
  galileo_data.dump
```

**From SQL dump:**
```bash
psql "postgresql://postgres.<project-ref>:<password>@db.<project-ref>.supabase.co:5432/postgres?sslmode=require" ^
  -f galileo_data.sql
```

> You'll be prompted for the password (the one from Step 1).

### 7d. Fix sequences after restore

Auto-increment sequences may be out of sync. Run in the Supabase **SQL Editor**:

```sql
SELECT setval(pg_get_serial_sequence('dataset_cases', 'id'),      COALESCE(MAX(id), 1)) FROM dataset_cases;
SELECT setval(pg_get_serial_sequence('run_case_status', 'id'),     COALESCE(MAX(id), 1)) FROM run_case_status;
SELECT setval(pg_get_serial_sequence('run_messages', 'id'),        COALESCE(MAX(id), 1)) FROM run_messages;
SELECT setval(pg_get_serial_sequence('run_results', 'id'),         COALESCE(MAX(id), 1)) FROM run_results;
SELECT setval(pg_get_serial_sequence('run_events', 'id'),          COALESCE(MAX(id), 1)) FROM run_events;
SELECT setval(pg_get_serial_sequence('cached_result_sets', 'id'),  COALESCE(MAX(id), 1)) FROM cached_result_sets;
```

### 7e. Verify data

Run in SQL Editor:
```sql
SELECT 'datasets' AS t, COUNT(*) FROM datasets
UNION ALL SELECT 'dataset_cases',    COUNT(*) FROM dataset_cases
UNION ALL SELECT 'runs',             COUNT(*) FROM runs
UNION ALL SELECT 'run_results',      COUNT(*) FROM run_results
UNION ALL SELECT 'run_messages',     COUNT(*) FROM run_messages
UNION ALL SELECT 'llm_model',        COUNT(*) FROM llm_model
UNION ALL SELECT 'galileo_eval_run', COUNT(*) FROM galileo_eval_run;
```

Compare counts against local DB to confirm all data transferred.

---

## 8. Final Verification

1. Start backend: `uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Open the app → verify:
   - Start page loads with datasets
   - Graphs page renders charts
   - Can run an evaluation → new data appears in Supabase Table Editor
4. Check **Supabase Logs → Postgres** for any query errors.

---

## 9. Cleanup

```bash
# Stop local Docker PostgreSQL
docker compose down

# (Optional) Remove the Docker volume
docker volume rm aigalileoarena_pgdata
```

The local postgres service in `docker-compose.yml` is commented out but preserved for offline development fallback.

---

## Quick Reference

| What | Value |
|---|---|
| Supabase Dashboard | https://supabase.com/dashboard |
| Project Settings → Database | Connection strings live here |
| SQL Editor | Run SQL directly on the DB |
| Table Editor | Browse/verify data visually |
| Logs → Postgres | Monitor query errors |
| App user | `app_user` (least-privilege) |
| Admin user | `postgres` (migrations only) |
| App connection | Session pooler, port `5432` |
| Migrations connection | Session pooler, port `5432` |
