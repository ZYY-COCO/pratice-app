from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ANSWER_KEYS = {"A", "B", "C", "D"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize question JSON files to A-D options only.")
    parser.add_argument(
        "--path",
        default=str(DATA_DIR),
        help="JSON file or directory to normalize. Directories are scanned non-recursively.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing files.")
    return parser.parse_args()


def load_questions(payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("questions"), list):
        return [item for item in payload["questions"] if isinstance(item, dict)]
    return []


def update_explanation(text: object) -> object:
    if not isinstance(text, str):
        return text

    replacements = {
        "E项": "D项",
        "E 项": "D 项",
        "选E": "选D",
        "选 E": "选 D",
        "答案E": "答案D",
        "答案 E": "答案 D",
        "答案为E": "答案为D",
        "答案为 E": "答案为 D",
        "正确答案E": "正确答案D",
        "正确答案 E": "正确答案 D",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"([，。；：、\s])E([，。；：、\s])", r"\1D\2", text)
    return text


def normalize_question(question: dict) -> bool:
    changed = False
    option_e = question.get("option_e")
    answer = str(question.get("answer", "")).strip().upper()

    if answer == "E":
        if isinstance(option_e, str) and option_e.strip():
            question["option_d"] = option_e.strip()
        question["answer"] = "D"
        question["explanation"] = update_explanation(question.get("explanation"))
        changed = True
    elif answer and answer not in ANSWER_KEYS:
        question["answer"] = answer

    if "option_e" in question:
        question.pop("option_e", None)
        changed = True

    return changed


def normalize_file(path: Path, dry_run: bool) -> tuple[int, int, int]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    questions = load_questions(payload)
    changed_count = 0
    remapped_answer_count = 0

    for question in questions:
        if str(question.get("answer", "")).strip().upper() == "E":
            remapped_answer_count += 1
        if normalize_question(question):
            changed_count += 1

    if changed_count and not dry_run:
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return len(questions), changed_count, remapped_answer_count


def iter_json_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(path.glob("*.json"))


def main() -> int:
    args = parse_args()
    target = Path(args.path).resolve()
    files = iter_json_files(target)
    total_changed = 0
    total_remapped = 0

    for path in files:
        try:
            total, changed, remapped = normalize_file(path, args.dry_run)
        except Exception as exc:
            print(f"[SKIP] {path}: {exc}")
            continue
        if changed or remapped:
            relative = path.relative_to(PROJECT_ROOT)
            print(f"{relative}: questions={total}, changed={changed}, answer_e_to_d={remapped}")
        total_changed += changed
        total_remapped += remapped

    print("Normalize summary")
    print(f"  Files scanned: {len(files)}")
    print(f"  Questions changed: {total_changed}")
    print(f"  Answers E->D: {total_remapped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
