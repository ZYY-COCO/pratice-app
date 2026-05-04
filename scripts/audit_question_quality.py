"""Audit local question bank JSON files for low-quality or meta questions.

This script is intentionally read-only for the database. It scans data/*.json,
flags questions that look like metadata/classification prompts, prompt leakage,
raw math notation, or structural quality issues, and writes a JSON + Markdown
report under data/.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REPORT_JSON = DATA_DIR / "question_quality_audit_report.json"
REPORT_MD = DATA_DIR / "question_quality_audit_report.md"


ACTION_DELETE = "delete_candidate"
ACTION_REWRITE = "rewrite_candidate"
ACTION_REVIEW = "manual_review"


DELETE_STEM_RULES: list[tuple[str, str, re.Pattern[str]]] = [
    (
        "meta_classification_stem",
        "题干是知识点归类/考点分类题，不像真实选择题",
        re.compile(
            r"题干若|题目若|若考查|若考察|最准确的知识点归类|知识点归类|最准确的归类|"
            r"归类是|属于哪个知识点|对应的知识点|考查的知识点|考察的知识点|本题属于|"
            r"本题考查的是|本题考察的是"
        ),
    ),
    (
        "outline_leak_stem",
        "题干泄露考纲/命题提示，不适合作为用户题目",
        re.compile(r"(依据|根据|按照).{0,16}(考纲|考试大纲)|中华文化考纲|港澳台.{0,12}考纲"),
    ),
]

REWRITE_TEXT_RULES: list[tuple[str, str, re.Pattern[str]]] = [
    (
        "raw_math_notation",
        "存在 LaTeX/源码式数学符号，需要改成常规卷面表达或由前端渲染",
        re.compile(r"\\frac|\\lim|\\to|_\{|\\int|\\sqrt|\\sin|\\cos|\$"),
    ),
    (
        "source_hint_text",
        "出现生成/接入/模式提示，需要删去或改写成正式题目表述",
        re.compile(r"后续接入|mock\s*模式|AI\s*生成|大模型|DeepSeek|依据.{0,16}考纲|考试大纲"),
    ),
    (
        "stem_prefix_tigan",
        "题干以“题干”开头，疑似生成提示残留",
        re.compile(r"^\s*题干"),
    ),
]

TAXONOMY_TERMS = [
    "中国文学常识",
    "中国历史学常识",
    "中国哲学常识",
    "中国艺术常识",
    "中国古代科技常识",
    "古代礼俗与称谓",
    "文学总集",
    "戏剧",
    "儒家",
    "道家",
    "语言知识",
    "词汇",
    "语法",
    "语用",
    "逻辑推理",
    "判断关系",
    "一元函数微分学",
    "一元函数积分学",
    "多元函数微分学",
    "数学基础",
]


@dataclass
class QuestionRecord:
    file: str
    index: int
    question: dict[str, Any]
    stem_key: str
    issues: list[dict[str, str]] = field(default_factory=list)

    @property
    def action(self) -> str | None:
        actions = [issue["action"] for issue in self.issues]
        if ACTION_DELETE in actions:
            return ACTION_DELETE
        if ACTION_REWRITE in actions:
            return ACTION_REWRITE
        if ACTION_REVIEW in actions:
            return ACTION_REVIEW
        return None


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def normalize_stem(text: str) -> str:
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[，。！？；：、,.!?;:()\[\]（）【】\"“”'‘’]", "", text)
    return text.lower()


def preview(text: str, limit: int = 90) -> str:
    text = re.sub(r"\s+", " ", as_text(text)).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "..."


def get_stem(question: dict[str, Any]) -> str:
    for key in ("question", "stem", "title", "content"):
        value = question.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def get_options(question: dict[str, Any]) -> dict[str, str]:
    raw = question.get("options")
    if isinstance(raw, dict):
        return {str(k): as_text(v) for k, v in raw.items()}
    if isinstance(raw, list):
        return {chr(65 + i): as_text(v) for i, v in enumerate(raw)}
    options: dict[str, str] = {}
    for key in ("A", "B", "C", "D"):
        value = question.get(key) or question.get(key.lower()) or question.get(f"option_{key.lower()}")
        if value is not None:
            options[key] = as_text(value)
    return options


def load_questions(path: Path) -> list[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except Exception:
        return []

    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("questions", "records", "data", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        if "question" in payload:
            return [payload]
    return []


def add_issue(record: QuestionRecord, action: str, rule: str, message: str) -> None:
    if any(issue["rule"] == rule for issue in record.issues):
        return
    record.issues.append({"action": action, "rule": rule, "message": message})


def taxonomy_option_score(option_text: str) -> int:
    return sum(1 for term in TAXONOMY_TERMS if term in option_text)


def audit_record(record: QuestionRecord) -> None:
    question = record.question
    stem = get_stem(question)
    options = get_options(question)
    option_values = list(options.values())
    all_text = "\n".join([stem, *option_values, as_text(question.get("analysis")), as_text(question.get("explanation"))])

    for rule, message, pattern in DELETE_STEM_RULES:
        if pattern.search(stem):
            add_issue(record, ACTION_DELETE, rule, message)

    taxonomy_path_options = 0
    for value in option_values:
        score = taxonomy_option_score(value)
        if "/" in value and score >= 1:
            taxonomy_path_options += 1
    if taxonomy_path_options >= 2:
        add_issue(
            record,
            ACTION_DELETE,
            "taxonomy_options",
            "多个选项是知识点路径/考点分类，疑似把归类题当成选择题",
        )

    for rule, message, pattern in REWRITE_TEXT_RULES:
        if pattern.search(all_text):
            add_issue(record, ACTION_REWRITE, rule, message)

    answer = as_text(question.get("answer") or question.get("correct_answer")).strip().upper()
    if answer and answer not in {"A", "B", "C", "D"}:
        add_issue(record, ACTION_REVIEW, "answer_not_abcd", "答案不是 A-D，需要人工核对")

    cleaned_options = [normalize_stem(value) for value in option_values if normalize_stem(value)]
    if len(cleaned_options) != len(set(cleaned_options)):
        add_issue(record, ACTION_REVIEW, "duplicate_options", "选项内容重复，需要人工核对")

    analysis = as_text(question.get("analysis") or question.get("explanation"))
    if analysis and len(analysis.strip()) < 16:
        add_issue(record, ACTION_REVIEW, "short_analysis", "解析过短，建议补充推理过程")


def summarize_record(record: QuestionRecord) -> dict[str, Any]:
    question = record.question
    options = get_options(question)
    return {
        "file": record.file,
        "index": record.index,
        "id": question.get("id"),
        "action": record.action,
        "issues": record.issues,
        "exam_code": question.get("exam_code") or question.get("exam"),
        "subject": question.get("subject") or question.get("exam_module"),
        "module": question.get("module"),
        "submodule": question.get("submodule") or question.get("knowledge_point"),
        "difficulty": question.get("difficulty"),
        "answer": question.get("answer") or question.get("correct_answer"),
        "stem": preview(get_stem(question), 140),
        "options": {key: preview(value, 80) for key, value in options.items()},
    }


def build_markdown(report: dict[str, Any]) -> str:
    issue_rows = report["issues"]
    lines: list[str] = []
    lines.append("# 题库质量排查报告")
    lines.append("")
    lines.append("> 本报告只扫描本地 `data/*.json`，没有删除数据库题目，也没有改写题库文件。")
    lines.append("")
    lines.append("## 总览")
    lines.append("")
    lines.append(f"- 扫描文件数：{report['scanned_files']}")
    lines.append(f"- 扫描题目数：{report['scanned_questions']}")
    lines.append(f"- 命中问题题目数：{len(issue_rows)}")
    lines.append("")
    lines.append("## 按处理建议统计")
    lines.append("")
    for action, count in report["counts_by_action"].items():
        lines.append(f"- {action}：{count}")
    lines.append("")
    lines.append("## 按规则统计")
    lines.append("")
    for rule, count in report["counts_by_rule"].items():
        lines.append(f"- {rule}：{count}")

    sections = [
        (ACTION_DELETE, "建议删除候选"),
        (ACTION_REWRITE, "建议改写候选"),
        (ACTION_REVIEW, "人工复核候选"),
    ]

    for action, title in sections:
        rows = [row for row in issue_rows if row["action"] == action]
        lines.append("")
        lines.append(f"## {title}")
        lines.append("")
        if not rows:
            lines.append("暂无。")
            continue
        lines.append(f"共 {len(rows)} 条。下面展示前 120 条，完整结果见 JSON 报告。")
        lines.append("")
        for row in rows[:120]:
            rules = "、".join(issue["rule"] for issue in row["issues"])
            location = f"{row['file']} #{row['index']}"
            meta = " / ".join(str(value) for value in [row.get("exam_code"), row.get("subject"), row.get("module"), row.get("submodule")] if value)
            lines.append(f"### {location}")
            if meta:
                lines.append(f"- 分类：{meta}")
            lines.append(f"- 规则：{rules}")
            lines.append(f"- 题干：{row['stem']}")
            if row["options"]:
                options = "；".join(f"{key}. {value}" for key, value in row["options"].items())
                lines.append(f"- 选项：{options}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    records: list[QuestionRecord] = []
    scanned_files = 0

    for path in sorted(DATA_DIR.glob("*.json")):
        if path.name.startswith("question_quality_audit_report"):
            continue
        questions = load_questions(path)
        if not questions:
            continue
        scanned_files += 1
        for index, question in enumerate(questions, start=1):
            stem = get_stem(question)
            records.append(QuestionRecord(path.name, index, question, normalize_stem(stem)))

    stem_locations: dict[str, list[QuestionRecord]] = defaultdict(list)
    for record in records:
        if record.stem_key:
            stem_locations[record.stem_key].append(record)

    for record in records:
        audit_record(record)

    for duplicates in stem_locations.values():
        if len(duplicates) <= 1:
            continue
        for record in duplicates:
            add_issue(record, ACTION_REVIEW, "duplicate_stem", "题干在本地 JSON 中重复，需要确认是否为重复题")

    issue_rows = [summarize_record(record) for record in records if record.issues]
    issue_rows.sort(key=lambda row: ({"delete_candidate": 0, "rewrite_candidate": 1, "manual_review": 2}.get(row["action"], 9), row["file"], row["index"]))

    counts_by_action = Counter(row["action"] for row in issue_rows)
    counts_by_rule = Counter(issue["rule"] for row in issue_rows for issue in row["issues"])

    report = {
        "scanned_files": scanned_files,
        "scanned_questions": len(records),
        "issue_questions": len(issue_rows),
        "counts_by_action": dict(counts_by_action),
        "counts_by_rule": dict(counts_by_rule),
        "issues": issue_rows,
    }

    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")

    print(json.dumps({key: report[key] for key in ("scanned_files", "scanned_questions", "issue_questions", "counts_by_action", "counts_by_rule")}, ensure_ascii=False, indent=2))
    print(f"Wrote {REPORT_JSON}")
    print(f"Wrote {REPORT_MD}")


if __name__ == "__main__":
    main()
