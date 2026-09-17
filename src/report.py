from src import db


def main():
    conn = db.get_conn()
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
    finally:
        conn.close()


if __name__ == "__main__":
    main()