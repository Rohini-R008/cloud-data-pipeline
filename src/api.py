from fastapi import FastAPI, HTTPException
from psycopg2.extras import RealDictCursor
from fastapi.responses import RedirectResponse
from src import db

app = FastAPI(title="Cloud Data Pipeline API", version="1.0")


def query(sql, params=None):
    conn = db.connect_with_retries()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()
    finally:
        conn.close()

@app.get("/")
def root():
    return RedirectResponse(url="/docs")

@app.get("/health")
def health():
    try:
        query("SELECT 1 AS ok;")
        return {"status": "ok", "database": "reachable"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"database unreachable: {e}")


@app.get("/countries")
def countries():
    """Reconciled view: the two sources joined on canonical country name."""
    return query(
        "SELECT country, population, year, region, income_group "
        "FROM country_reconciled ORDER BY population DESC;"
    )


@app.get("/population")
def population():
    return query(
        "SELECT country, population, year FROM population "
        "ORDER BY population DESC;"
    )


@app.get("/quarantine")
def quarantine():
    """The bad rows and why they failed — great for the broken-file demo."""
    return query(
        "SELECT source, error_reason, raw_data, quarantined_at "
        "FROM quarantine ORDER BY id;"
    )


@app.get("/runs")
def runs(limit: int = 20):
    """Pipeline run history: durations, statuses, counts."""
    return query(
        "SELECT run_id, started_at, finished_at, duration_seconds, status, "
        "rows_loaded, rows_quarantined, reconciled_rows, error "
        "FROM pipeline_runs ORDER BY started_at DESC LIMIT %s;",
        (limit,),
    )


@app.get("/stats")
def stats():
    row = query("""
        SELECT
          (SELECT count(*) FROM population)         AS population_rows,
          (SELECT count(*) FROM regions)            AS regions_rows,
          (SELECT count(*) FROM quarantine)         AS quarantine_rows,
          (SELECT count(*) FROM country_reconciled) AS reconciled_rows,
          (SELECT count(*) FROM pipeline_runs)      AS total_runs,
          (SELECT count(*) FROM pipeline_runs WHERE status='success')
                                                    AS successful_runs;
    """)[0]
    total = row["population_rows"] + row["quarantine_rows"]
    row["validation_failure_pct"] = (
        round(100 * row["quarantine_rows"] / total, 2) if total else 0.0
    )
    return row