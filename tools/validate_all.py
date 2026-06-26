import json
from pathlib import Path
from comparison_validator import validate_comparison


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data" / "comparisons"

    if not data_dir.exists():
        print(f"Missing directory: {data_dir}")
        return 1

    json_files = sorted(data_dir.glob("*.json"))

    if not json_files:
        print("No comparison JSON files found.")
        return 1

    failed = False

    for path in json_files:
        comparison = load_json(path)
        result = validate_comparison(comparison)

        print(f"\n{path.name}: {result['status']}")

        for error in result["errors"]:
            print(f"  ERROR: {error}")

        for warning in result["warnings"]:
            print(f"  WARNING: {warning}")

        if result["status"] != "valid":
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
