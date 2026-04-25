from __future__ import annotations

import argparse
import os
from pathlib import Path

from import_questions import (
    IMPORT_COLUMNS,
    BACKEND_DIR,
    PROJECT_ROOT,
    duplicate_key,
    load_env_file,
    load_questions,
    validate_question,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bulk import validated questions into Supabase.")
    parser.add_argument("--file", required=True, help="Path to the source JSON file.")
    parser.add_argument("--env-file", default=str(BACKEND_DIR / ".env"), help="Backend env file.")
    parser.add_argument("--batch-size", type=int, default=100, help="Rows per insert batch.")
    return parser.parse_args()


def fetch_existing_keys(supabase, exam_code: str, subject: str) -> set[tuple[str, str, str, str]]:
    keys: set[tuple[str, str, str, str]] = set()
    offset = 0
    page_size = 1000
    while True:
        response = (
            supabase.table("questions")
            .select("stem,subject,module,submodule")
            .eq("exam_code", exam_code)
            .eq("subject", subject)
            .range(offset, offset + page_size - 1)
            .execute()
        )
        rows = response.data or []
        for row in rows:
            keys.add(duplicate_key(row))
        if len(rows) < page_size:
            break
        offset += page_size
    return keys


def chunked(values: list[dict], size: int) -> list[list[dict]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def main() -> int:
    args = parse_args()
    json_path = Path(args.file).resolve()
    env_path = Path(args.env_file).resolve()

    load_env_file(env_path)
    from supabase import create_client

    supabase_url = os.environ["SUPABASE_URL"]
    supabase_key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    supabase = create_client(supabase_url, supabase_key)

    raw_questions = load_questions(json_path)
    valid_questions: list[dict] = []
    invalid: list[str] = []
    for index, question in enumerate(raw_questions, start=1):
        try:
            validated = validate_question(question, index)
            valid_questions.append(validated)
        except Exception as exc:
            invalid.append(f"Question #{index}: {exc}")

    if invalid:
        print("Invalid questions found. Import aborted.")
        for item in invalid[:20]:
            print(f"  - {item}")
        if len(invalid) > 20:
            print(f"  ... {len(invalid) - 20} more")
        return 1

    groups: dict[tuple[str, str], list[dict]] = {}
    for question in valid_questions:
        groups.setdefault((question["exam_code"], question["subject"]), []).append(question)

    existing_keys: set[tuple[str, str, str, str]] = set()
    for exam_code, subject in groups:
        existing_keys.update(fetch_existing_keys(supabase, exam_code, subject))

    seen: set[tuple[str, str, str, str]] = set()
    rows_to_insert: list[dict] = []
    skipped_duplicate = 0
    for question in valid_questions:
        key = duplicate_key(question)
        if key in seen or key in existing_keys:
            skipped_duplicate += 1
            continue
        seen.add(key)
        rows_to_insert.append({column: question.get(column) for column in IMPORT_COLUMNS if column != "id"})

    inserted = 0
    for batch in chunked(rows_to_insert, max(1, args.batch_size)):
        response = supabase.table("questions").insert(batch).execute()
        inserted += len(response.data or batch)
        print(f"Inserted batch: {inserted}/{len(rows_to_insert)}")

    print("Bulk import summary")
    print(f"  Source file: {json_path.relative_to(PROJECT_ROOT)}")
    print(f"  Total questions: {len(raw_questions)}")
    print(f"  Valid questions: {len(valid_questions)}")
    print(f"  Inserted: {inserted}")
    print(f"  Skipped duplicates: {skipped_duplicate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
