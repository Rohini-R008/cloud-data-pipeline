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