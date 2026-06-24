# src/tfg/scenario/incidents.py
from pathlib import Path
import json

def load_events(path: str | Path):
  with Path(path).open(encoding="utf-8") as f:
    return json.load(f)
