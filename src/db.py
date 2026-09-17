import json

import psycopg2
from psycopg2.extras import execute_values

from src.config import DATABASE_URL

DDL = """
CREATE TABLE IF NOT EXISTS population (
    id          SERIAL PRIMARY KEY,
    country     TEXT   NOT NULL,
    population  BIGINT NOT NULL,
    year        INT    NOT NULL,
    run_id      TEXT   NOT NULL,
    loaded_at   TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS regions (
    id            SERIAL PRIMARY KEY,
    country       TEXT NOT NULL,
    region        TEXT NOT NULL,
    income_group  TEXT NOT NULL,
    run_id        TEXT NOT NULL,
    loaded_at     TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS quarantine (
    id             SERIAL PRIMARY KEY,
    source         TEXT  NOT NULL,
    run_id         TEXT  NOT NULL,
    raw_data       JSONB NOT NULL,
    error_reason   TEXT  NOT NULL,
    quarantined_at TIMESTAMPTZ DEFAULT now()
);
"""


def get_conn():
    if not DATABASE_URL:
        raise SystemExit(
            "DATABASE_URL is not set. Create a .env file from .env.example "
            "and paste your Neon connection string into it."
        )
    return psycopg2.connect(DATABASE_URL)


def init_db(conn):
    with conn.cursor() as cur:
        cur.execute(DDL)
    conn.commit()


def truncate_all(conn):
    # Idempotent loads: each run starts from a clean slate (no side effects).
    with conn.cursor() as cur:
        cur.execute("TRUNCATE population, regions, quarantine RESTART IDENTITY;")
    conn.commit()


def insert_population(conn, rows, run_id):
    if not rows:
        return
    values = [(r["country"], r["population"], r["year"], run_id) for r in rows]
    with conn.cursor() as cur:
        execute_values(
            cur,
            "INSERT INTO population (country, population, year, run_id) VALUES %s",
            values,
        )
    conn.commit()


def insert_regions(conn, rows, run_id):
    if not rows:
        return
    values = [(r["country"], r["region"], r["income_group"], run_id) for r in rows]
    with conn.cursor() as cur:
        execute_values(
            cur,
            "INSERT INTO regions (country, region, income_group, run_id) VALUES %s",
            values,
        )
    conn.commit()


def insert_quarantine(conn, items, source, run_id):
    if not items:
        return
    values = [
        (source, run_id, json.dumps(it["raw"]), it["error"]) for it in items
    ]
    with conn.cursor() as cur:
        execute_values(
            cur,
            "INSERT INTO quarantine (source, run_id, raw_data, error_reason) "
            "VALUES %s",
            values,
        )
    conn.commit()


def build_reconciled(conn):
    # The reconciliation payoff: join the two cleaned sources on canonical country.
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS country_reconciled;")
        cur.execute("""
            CREATE TABLE country_reconciled AS
            SELECT p.country, p.population, p.year, r.region, r.income_group
            FROM population p
            JOIN regions r ON p.country = r.country;
        """)
        cur.execute("SELECT count(*) FROM country_reconciled;")
        n = cur.fetchone()[0]
    conn.commit()
    return n