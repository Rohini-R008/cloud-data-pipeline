from pydantic import ValidationError

from src import db
from src.clean import clean_population, clean_regions
from src.config import LANDING_DIR
from src.schemas import PopulationRecord, RegionRecord


def latest_run_dir():
    latest = LANDING_DIR / "_latest.txt"
    if not latest.exists():
        raise SystemExit("No landing runs found. Run first: python -m src.ingest")
    run_id = latest.read_text(encoding="utf-8").strip()
    return run_id, LANDING_DIR / run_id


def validate(rows, model):
    valid, bad = [], []
    for row in rows:
        try:
            rec = model(**row)
            valid.append(rec.model_dump())
        except ValidationError as e:
            reasons = "; ".join(
                f"{err['loc'][0] if err['loc'] else '?'}: {err['msg']}"
                for err in e.errors()
            )
            bad.append({"raw": row, "error": reasons})
    return valid, bad


def main():
    run_id, run_dir = latest_run_dir()
    print(f"[load] using landing run: {run_id}")

    pop_rows = clean_population(run_dir / "population.csv")
    reg_rows = clean_regions(run_dir / "regions.csv")

    pop_valid, pop_bad = validate(pop_rows, PopulationRecord)
    reg_valid, reg_bad = validate(reg_rows, RegionRecord)

    conn = db.get_conn()
    try:
        db.init_db(conn)
        db.truncate_all(conn)
        db.insert_population(conn, pop_valid, run_id)
        db.insert_regions(conn, reg_valid, run_id)
        db.insert_quarantine(conn, pop_bad, "population", run_id)
        db.insert_quarantine(conn, reg_bad, "regions", run_id)
        reconciled = db.build_reconciled(conn)
    finally:
        conn.close()

    print("\n=== Load summary ===")
    print(f"run_id       : {run_id}")
    print(f"population   : {len(pop_valid):>3} loaded, {len(pop_bad):>3} quarantined")
    print(f"regions      : {len(reg_valid):>3} loaded, {len(reg_bad):>3} quarantined")
    print(f"reconciled   : {reconciled:>3} rows (population joined to regions)")


if __name__ == "__main__":
    main()