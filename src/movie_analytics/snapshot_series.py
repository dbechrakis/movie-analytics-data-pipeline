"""Tabulate the dated snapshot summaries so that the README table is generated and never typed by hand."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_DIR = ROOT / "snapshots"
README = ROOT / "README.md"
START = "<!-- snapshot-series:start -->"
END = "<!-- snapshot-series:end -->"
HEADER = (
    "| Snapshot date | Profile | Films ingested | After staging filters | Median ROI | Mean ROI | dbt tests passed |\n"
    "|---|---|---:|---:|---:|---:|---:|"
)


def load_snapshots(directory: Path = SNAPSHOT_DIR) -> list[dict]:
    snapshots = []
    for path in sorted(directory.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        data["snapshot_date"] = path.name.split("_", 1)[0]
        snapshots.append(data)
    return sorted(snapshots, key=lambda s: (s["sampling"], s["snapshot_date"]))


def series_table(snapshots: list[dict]) -> str:
    rows = []
    for s in snapshots:
        tests = s.get("dbt_tests") or {}
        passed = f"{tests['passed']} of {tests['total']}" if tests else "not recorded"
        rows.append(
            f"| {s['snapshot_date']} | `{s['sampling']}` | {s['movies_ingested']} | {s['movies_after_staging_filters']} "
            f"| {s['roi_median']:.2f} | {s['roi_mean']:.2f} | {passed} |"
        )
    return "\n".join([HEADER, *rows])


def replace_block(readme_text: str, table: str) -> str:
    start = readme_text.index(START) + len(START)
    end = readme_text.index(END)
    return readme_text[:start] + "\n" + table + "\n" + readme_text[end:]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-readme", action="store_true")
    args = parser.parse_args()
    table = series_table(load_snapshots())
    if args.write_readme:
        README.write_text(replace_block(README.read_text(encoding="utf-8"), table), encoding="utf-8", newline="\n")
    print(table)


if __name__ == "__main__":
    main()
