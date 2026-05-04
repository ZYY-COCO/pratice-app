from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REPORT_JSON = DATA_DIR / "question_difficulty_normalization_report.json"
REPORT_MD = DATA_DIR / "question_difficulty_normalization_report.md"

DIFFICULTY_MAP = {
    "\u57fa\u7840": 1,
    "\u7b80\u5355": 1,
    "\u8f83\u6613": 2,
    "\u4e2d\u7ea7": 3,
    "\u4e2d\u7b49": 3,
    "\u8f83\u96be": 4,
    "\u56f0\u96be": 5,
    "\u9ad8\u7ea7": 5,
    "\u6311\u6218": 5,
}

SKIP_SUFFIXES = (
    "_report.json",
    "_summary.json",
)


def should_scan(path: Path) -> bool:
    if path.name.startswith("question_quality_"):
        return False
    if path.name.startswith("question_difficulty_"):
        return False
    return not path.name.endswith(SKIP_SUFFIXES)


def load_payload(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def iter_question_dicts(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("questions", "items", "data", "records"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        if "difficulty" in payload:
            return [payload]
    return []


def normalize_file(path: Path) -> dict[str, Any] | None:
    payload = load_payload(path)
    questions = iter_question_dicts(payload)
    changes: list[dict[str, Any]] = []

    for index, question in enumerate(questions, start=1):
        raw = question.get("difficulty")
        if isinstance(raw, str):
            key = raw.strip()
            if key in DIFFICULTY_MAP:
                next_value = DIFFICULTY_MAP[key]
                question["difficulty"] = next_value
                changes.append({"index": index, "from": raw, "to": next_value})

    if not changes:
        return None

    with path.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    return {
        "file": str(path.relative_to(ROOT)).replace("\\", "/"),
        "changes": changes,
        "count": len(changes),
    }


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Question difficulty normalization",
        "",
        f"- Scanned files: {report['scanned_files']}",
        f"- Updated files: {len(report['files'])}",
        f"- Updated questions: {report['updated_questions']}",
        "",
        "## Mapping",
        "",
    ]

    for label, value in sorted(DIFFICULTY_MAP.items(), key=lambda item: (item[1], item[0])):
        lines.append(f"- {label} -> {value}")

    lines.extend(["", "## Updated Files", ""])
    if not report["files"]:
        lines.append("- No files changed.")
    else:
        for item in report["files"]:
            lines.append(f"- `{item['file']}`: {item['count']} question(s)")

    lines.extend(["", "## Counts By Source Label", ""])
    for label, count in report["counts_by_source_label"].items():
        lines.append(f"- {label}: {count}")

    return "\n".join(lines) + "\n"


def main() -> int:
    scanned = 0
    files: list[dict[str, Any]] = []
    counts_by_source_label: Counter[str] = Counter()
    counts_by_target: defaultdict[str, int] = defaultdict(int)

    for path in sorted(DATA_DIR.glob("*.json")):
        if not should_scan(path):
            continue
        scanned += 1
        result = normalize_file(path)
        if not result:
            continue
        files.append(result)
        for change in result["changes"]:
            counts_by_source_label[str(change["from"])] += 1
            counts_by_target[str(change["to"])] += 1

    report = {
        "scanned_files": scanned,
        "updated_questions": sum(item["count"] for item in files),
        "counts_by_source_label": dict(sorted(counts_by_source_label.items())),
        "counts_by_target": dict(sorted(counts_by_target.items())),
        "files": files,
    }

    with REPORT_JSON.open("w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    REPORT_MD.write_text(build_markdown(report), encoding="utf-8", newline="\n")

    print(f"Scanned files: {scanned}")
    print(f"Updated files: {len(files)}")
    print(f"Updated questions: {report['updated_questions']}")
    for item in files:
        print(f"  - {item['file']}: {item['count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
