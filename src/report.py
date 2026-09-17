from src import db


def main():
    conn = db.connect_with_retries()
    try:
        with conn.cursor() as cur:
            print("=== Table counts ===")
            for t in ["population", "regions", "quarantine", "country_reconciled"]:
                try:
                    cur.execute(f"SELECT count(*) FROM {t};")
                    print(f"{t:20s}: {cur.fetchone()[0]} rows")
                except Exception:
                    conn.rollback()
                    print(f"{t:20s}: (not created yet)")

            print("\n=== Quarantine sample (up to 10) ===")
            cur.execute(
                "SELECT source, error_reason, raw_data "
                "FROM quarantine ORDER BY id LIMIT 10;"
            )
            for source, reason, raw in cur.fetchall():
                print(f"[{source}] {reason}  ::  {raw}")

            print("\n=== Recent pipeline runs (up to 5) ===")
            try:
                cur.execute(
                    "SELECT run_id, status, rows_loaded, rows_quarantined, "
                    "round(duration_seconds::numeric, 1) AS secs, started_at "
                    "FROM pipeline_runs ORDER BY started_at DESC LIMIT 5;"
                )
                for run_id, status, loaded, quar, secs, started in cur.fetchall():
                    print(f"{started}  {status:8s}  loaded={loaded} "
                          f"quar={quar}  {secs}s  ({run_id})")
            except Exception:
                conn.rollback()
                print("(no pipeline_runs yet — run: python -m src.pipeline)")
    finally:
        conn.close()


if __name__ == "__main__":
    main()