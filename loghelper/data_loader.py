import json
from pathlib import Path

def load_mods_json(path: str | Path = None) -> dict:
    if path is None:
        path = Path(__file__).parent / "data" / "mods.json"
    with open(path, "r") as f:
        return json.load(f)

def load_issues_json(path: str | Path = None) -> dict:
    if path is None:
        path = Path(__file__).parent / "data" / "issues.json"
    with open(path, "r") as f:
        return json.load(f)