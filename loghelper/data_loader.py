import json
from pathlib import Path

def load_mods_json(path: str | Path | None = None) -> list[dict]:
    if path is None:
        path = Path(__file__).parent / "data" / "mods.json"
    with open(path, "r") as f:
        mods = json.load(f)
        mods = sorted(mods, key=lambda d: len(d.get("name", "")), reverse=True)
        return mods

def load_issues_json(path: str | Path | None = None) -> dict:
    if path is None:
        path = Path(__file__).parent / "data" / "issues.json"
    with open(path, "r") as f:
        return json.load(f)