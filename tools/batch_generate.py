import json
from pathlib import Path
from script_generator import (
    generate_short_script,
    generate_long_outline,
    generate_newsletter,
)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data" / "comparisons"
    output_dir = root / "generated"

    json_files = sorted(data_dir.glob("*.json"))

    if not json_files:
        print("No comparison JSON files found.")
        return 1

    for path in json_files:
        comparison = load_json(path)
        comparison_id = comparison["comparison_id"]

        write_text(
            output_dir / "short_scripts" / f"{comparison_id}.md",
            generate_short_script(comparison),
        )

        write_text(
            output_dir / "long_outlines" / f"{comparison_id}.md",
            generate_long_outline(comparison),
        )

        write_text(
            output_dir / "newsletters" / f"{comparison_id}.md",
            generate_newsletter(comparison),
        )

        print(f"Generated content for {comparison_id}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
