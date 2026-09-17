# Cloud-Deployed Data Pipeline

A reconciling data pipeline: ingest → clean/validate → load to cloud Postgres → serve.

## Phase 1 — Ingest & Landing Zone
Raw ingest copies untouched source files into a timestamped landing zone.
Each run is isolated and re-runnable with no side effects.

### Run
python -m src.ingest

Output lands in `data/landing/<run_id>/` with a `manifest.json` (per-file size + SHA-256).

### Sources
Two intentionally messy sources that reconcile on country name
(`population` and `regions`) — see `config/sources.yaml`.

## Phase 2 — Clean, Validate, Load
Cleans the raw landing files (whitespace, casing, comma-formatted numbers,
missing values, duplicates), reconciles two sources on a canonical country
name, validates every row against a Pydantic schema, then loads into
cloud-hosted Postgres (Neon).

- Valid rows -> `population` / `regions` tables, plus a reconciled
  `country_reconciled` join table.
- Invalid rows -> `quarantine` table (JSONB of the raw row + the failure
  reason). Never silently dropped.

### Run
python -m src.ingest # land raw files
python -m src.load # clean, validate, load to Postgres
python -m src.report # verify counts + inspect quarantine


### Config
`DATABASE_URL` (Neon connection string) lives in `.env` — see `.env.example`.

## Phase 3 — Orchestration & Serving
- **Orchestration:** `src/pipeline.py` runs ingest -> load end-to-end. A
  scheduled GitHub Action (`.github/workflows/pipeline.yml`) runs it daily,
  and can be triggered manually.
- **Retries:** DB connections retry with exponential backoff to absorb
  Neon's cold starts (scale-to-zero).
- **Run history:** every run is logged to a `pipeline_runs` table
  (status, duration, rows loaded/quarantined) — queryable in SQL or via the API.
- **Serving (FastAPI):** read-only API over the loaded data.

### Run locally
python -m src.pipeline # full run, logs to pipeline_runs
uvicorn src.api:app # serve the API at http://127.0.0.1:8000

Interactive docs at http://127.0.0.1:8000/docs

### API endpoints
`/health` `/countries` `/population` `/quarantine` `/runs` `/stats`

### Scheduling
The GitHub Action needs a `DATABASE_URL` repository secret
(Settings -> Secrets and variables -> Actions).