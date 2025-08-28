import json
from pathlib import Path

def sort():
    print("Sorting issues...")
    path = Path(__file__).parent / "issues.json"
    added_periods = 0
    with open(path, "r") as f:
        strings = json.load(f)
        for key, string in strings.items():
            if not string[len(string) - 1] in [".", "!", "?", "*", ":", ")", "}"]:
                strings[key] = string + "."
                added_periods += 1
        with open(path, "w") as w:
            json.dump(dict(sorted(strings.items())), w, indent=4)
    print(f"  Added {added_periods} period{'s' if not added_periods == 1 else ''}.")
    print("  Finished sorting issues.")

if __name__ == "__main__":
    sort()
