import re

import pandas as pd

# Reconciliation: different sources spell the same country differently.
# Map every known alias (lowercased) to one canonical name.
COUNTRY_ALIASES = {
    "usa": "United States",
    "us": "United States",
    "u.s.a.": "United States",
    "united states": "United States",
    "united states of america": "United States",
    "uk": "United Kingdom",
    "u.k.": "United Kingdom",
    "united kingdom": "United Kingdom",
    "great britain": "United Kingdom",
    "russian federation": "Russia",
    "russia": "Russia",
    "republic of korea": "South Korea",
    "korea, rep.": "South Korea",
    "south korea": "South Korea",
}


def normalize_country(raw: str) -> str:
    """Collapse whitespace, then map aliases to a canonical country name."""
    if raw is None:
        return ""
    collapsed = re.sub(r"\s+", " ", str(raw)).strip()
    key = collapsed.lower()
    if key in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[key]
    return collapsed.title()  # fallback: 'japan' -> 'Japan'


def _dedup(rows, keys):
    seen = set()
    out = []
    for row in rows:
        sig = tuple(row[k] for k in keys)
        if sig in seen:
            continue
        seen.add(sig)
        out.append(row)
    return out


def clean_population(path):
    # Read everything as strings so WE control all type coercion.
    df = pd.read_csv(path, dtype=str, na_filter=False)
    rows = []
    for _, r in df.iterrows():
        pop_raw = str(r.get("population", "")).replace(",", "").strip()
        rows.append({
            "country": normalize_country(r.get("country", "")),
            # Empty -> None so Pydantic flags it (missing value -> quarantine)
            "population": pop_raw if pop_raw != "" else None,
            "year": str(r.get("year", "")).strip(),
        })
    return _dedup(rows, ["country", "population", "year"])


def clean_regions(path):
    df = pd.read_csv(path, dtype=str, na_filter=False)
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "country": normalize_country(r.get("country_name", "")),
            "region": str(r.get("region", "")).strip(),
            "income_group": str(r.get("income_group", "")).strip(),
        })
    return _dedup(rows, ["country", "region", "income_group"])