import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import requests

from src.config import LANDING_DIR, SEEDS_DIR, LOGS_DIR, load_sources


def utc_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_url(url: str, dest: Path) -> None:
    # Download to a .part file, then atomically rename — so an interrupted
    # run never leaves a half-written file in the landing zone.
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    tmp.replace(dest)


def fetch_local(location: str, dest: Path) -> None:
    src = SEEDS_DIR / location
    if not src.exists():
        raise FileNotFoundError(f"Seed file not found: {src}")
    tmp = dest.with_suffix(dest.suffix + ".part")
    shutil.copyfile(src, tmp)
    tmp.replace(dest)


def ingest() -> Path:
    sources = load_sources()
    if not sources:
        raise SystemExit("No sources configured in config/sources.yaml")

    run_id = utc_run_id()
    run_dir = LANDING_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    manifest = {
        "run_id": run_id,
        "ingested_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": [],
    }

    for s in sources:
        name = s["name"]
        stype = s["type"]
        location = s["location"]
        filename = s["filename"]
        dest = run_dir / filename

        print(f"[ingest] {name}: {stype} -> {dest}")
        if stype == "url":
            fetch_url(location, dest)
        elif stype == "local":
            fetch_local(location, dest)
        else:
            raise ValueError(f"Unknown source type: {stype}")

        manifest["sources"].append({
            "name": name,
            "type": stype,
            "location": location,
            "filename": filename,
            "bytes": dest.stat().st_size,
            "sha256": sha256_of(dest),
        })

    manifest_path = run_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Cross-platform "latest run" pointer (avoids symlinks that break on Windows)
    (LANDING_DIR / "_latest.txt").write_text(run_id, encoding="utf-8")

    print(f"[ingest] done. run_id={run_id}")
    print(f"[ingest] manifest: {manifest_path}")
    return run_dir


if __name__ == "__main__":
    ingest()