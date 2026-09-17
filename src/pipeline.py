import sys
from datetime import datetime, timezone

from src import db
from src.ingest import ingest
from src.load import run_load


def main():
    started = datetime.now(timezone.utc)
    run_id = None
    status = "success"
    error = None
    metrics = {"rows_loaded": 0, "rows_quarantined": 0, "reconciled_rows": 0}

    try:
        run_dir = ingest()                       # land raw files
        run_id = run_dir.name
        conn = db.connect_with_retries()         # retries handle Neon cold start
        try:
            metrics = run_load(conn, run_dir, run_id)
        finally:
            conn.close()
    except Exception as e:
        status = "failed"
        error = f"{type(e).__name__}: {e}"
        print(f"[pipeline] FAILED: {error}")

    finished = datetime.now(timezone.utc)

    # Always record the run — even a failure — on a fresh connection so a
    # broken load transaction can't stop us from logging it.
    try:
        log_conn = db.connect_with_retries()
        try:
            db.init_db(log_conn)
            db.log_run(
                log_conn,
                run_id or started.strftime("%Y%m%dT%H%M%SZ"),
                started, finished, status,
                metrics["rows_loaded"], metrics["rows_quarantined"],
                metrics["reconciled_rows"], error,
            )
        finally:
            log_conn.close()
    except Exception as e:
        print(f"[pipeline] WARNING: could not write run log: {e}")

    print("\n=== Pipeline run ===")
    print(f"run_id     : {run_id}")
    print(f"status     : {status}")
    print(f"loaded     : {metrics['rows_loaded']}")
    print(f"quarantined: {metrics['rows_quarantined']}")
    print(f"reconciled : {metrics['reconciled_rows']}")
    print(f"duration   : {(finished - started).total_seconds():.1f}s")

    if status == "failed":
        sys.exit(1)   # non-zero exit -> GitHub Action shows a red X


if __name__ == "__main__":
    main()