"""Remove confirmed delete candidates from local JSON files and generate DB SQL.

Input: data/question_quality_audit_report.json
Output:
- database/delete_question_quality_candidates.sql
- data/question_quality_delete_summary.json
- data/question_quality_delete_summary.md

The script does not connect to Supabase. Execute the generated SQL manually in
Supabase SQL Editor when you are ready to sync the online database.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATABASE_DIR = ROOT / "database"
AUDIT_REPORT = DATA_DIR / "question_quality_audit_report.json"
SUMMARY_JSON = DATA_DIR / "question_quality_delete_summary.json"
SUMMARY_MD = DATA_DIR / "question_quality_delete_summary.md"
DELETE_SQL = DATABASE_DIR / "delete_question_quality_candidates.sql"


def sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    text = str(value)
    return "'" + text.replace("'", "''") + "'"


def load_payload(path: Path) -> tuple[Any, list[dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        questions = payload
    elif isinstance(payload, dict) and isinstance(payload.get("questions"), list):
        questions = payload["questions"]
    else:
        raise ValueError(f"Unsupported question JSON shape: {path}")
    if not all(isinstance(item, dict) for item in questions):
        raise ValueError(f"Question list contains non-object item: {path}")
    return payload, questions


def write_payload(path: Path, payload: Any, questions: list[dict[str, Any]]) -> None:
    if isinstance(payload, list):
        payload = questions
    else:
        payload["questions"] = questions
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def get_stem(question: dict[str, Any]) -> str:
    return str(question.get("stem") or question.get("question") or "").strip()


def remove_candidates() -> dict[str, Any]:
    report = json.loads(AUDIT_REPORT.read_text(encoding="utf-8"))
    delete_rows = [row for row in report.get("issues", []) if row.get("action") == "delete_candidate"]
    if not delete_rows:
        raise RuntimeError("No delete_candidate rows found. Run audit_question_quality.py first.")

    by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in delete_rows:
        by_file[row["file"]].append(row)

    removed: list[dict[str, Any]] = []
    kept_warnings: list[dict[str, Any]] = []

    for filename, rows in sorted(by_file.items()):
        path = DATA_DIR / filename
        payload, questions = load_payload(path)
        remove_indices = {int(row["index"]) for row in rows}
        new_questions: list[dict[str, Any]] = []

        for index, question in enumerate(questions, start=1):
            if index not in remove_indices:
                new_questions.append(question)
                continue

            stem = get_stem(question)
            matching = next((row for row in rows if int(row["index"]) == index), None)
            if matching and matching.get("stem") and not stem.startswith(str(matching["stem"]).rstrip("...")):
                kept_warnings.append(
                    {
                        "file": filename,
                        "index": index,
                        "reason": "stem_mismatch",
                        "report_stem": matching.get("stem"),
                        "current_stem": stem,
                    }
                )
                new_questions.append(question)
                continue

            removed.append(
                {
                    "file": filename,
                    "index": index,
                    "exam_code": question.get("exam_code"),
                    "subject": question.get("subject") or question.get("exam_module"),
                    "module": question.get("module"),
                    "submodule": question.get("submodule") or question.get("knowledge_point"),
                    "stem": stem,
                    "rules": [issue["rule"] for issue in (matching or {}).get("issues", [])],
                }
            )

        write_payload(path, payload, new_questions)

    return {
        "removed_count": len(removed),
        "warnings": kept_warnings,
        "removed": removed,
        "removed_by_file": dict(Counter(item["file"] for item in removed)),
        "removed_by_subject": dict(Counter(item.get("subject") or "" for item in removed)),
    }


def build_delete_sql(summary: dict[str, Any]) -> str:
    rows = summary["removed"]
    values = []
    for item in rows:
        values.append(
            "("
            + ", ".join(
                [
                    sql_literal(item.get("exam_code")),
                    sql_literal(item.get("subject")),
                    sql_literal(item.get("module")),
                    sql_literal(item.get("submodule")),
                    sql_literal(item.get("stem")),
                ]
            )
            + ")"
        )

    values_sql = ",\n    ".join(values)
    return f"""-- Delete low-quality question candidates found by scripts/audit_question_quality.py
-- Review data/question_quality_delete_summary.md before executing.
-- This deletes matching rows from public.questions; related answers/wrong/favorites
-- will cascade according to the existing foreign keys.

begin;

with delete_candidates(exam_code, subject, module, submodule, stem) as (
  values
    {values_sql}
),
deleted_questions as (
  delete from public.questions q
  using delete_candidates c
  where q.exam_code = c.exam_code
    and q.subject = c.subject
    and q.module = c.module
    and q.submodule = c.submodule
    and q.stem = c.stem
  returning q.id, q.exam_code, q.subject, q.module, q.submodule, q.stem
)
select count(*) as deleted_question_count from deleted_questions;

commit;
"""


def build_summary_md(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# 题库删除候选处理摘要")
    lines.append("")
    lines.append("> 已从本地 JSON 删除建议删除候选；线上数据库请手动执行 `database/delete_question_quality_candidates.sql` 同步。")
    lines.append("")
    lines.append(f"- 本地删除题目数：{summary['removed_count']}")
    lines.append(f"- 安全警告数：{len(summary['warnings'])}")
    lines.append("")
    lines.append("## 按文件统计")
    lines.append("")
    for file, count in summary["removed_by_file"].items():
        lines.append(f"- {file}：{count}")
    lines.append("")
    lines.append("## 按科目统计")
    lines.append("")
    for subject, count in summary["removed_by_subject"].items():
        lines.append(f"- {subject or '未标注'}：{count}")
    lines.append("")
    lines.append("## 删除明细")
    lines.append("")
    for item in summary["removed"][:260]:
        meta = " / ".join(str(value) for value in [item.get("exam_code"), item.get("subject"), item.get("module"), item.get("submodule")] if value)
        lines.append(f"- `{item['file']}#{item['index']}` {meta}：{item['stem']}")
    if len(summary["removed"]) > 260:
        lines.append(f"- 其余 {len(summary['removed']) - 260} 条见 JSON 摘要。")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    summary = remove_candidates()
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    SUMMARY_MD.write_text(build_summary_md(summary), encoding="utf-8")
    DELETE_SQL.write_text(build_delete_sql(summary), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("removed_count", "warnings", "removed_by_file", "removed_by_subject")}, ensure_ascii=False, indent=2))
    print(f"Wrote {SUMMARY_JSON}")
    print(f"Wrote {SUMMARY_MD}")
    print(f"Wrote {DELETE_SQL}")


if __name__ == "__main__":
    main()
