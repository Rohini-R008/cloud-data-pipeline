from pathlib import Path
import yaml

# Project root is one level up from this file (src/config.py -> project root)
ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data"
LANDING_DIR = DATA_DIR / "landing"
SEEDS_DIR = ROOT / "seeds"
LOGS_DIR = ROOT / "logs"
CONFIG_FILE = ROOT / "config" / "sources.yaml"


def load_sources():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("sources", [])