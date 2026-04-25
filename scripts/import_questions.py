from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from uuid import UUID


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"


KNOWLEDGE_TREE = {
    "中华文化": {
        "中国哲学常识": ["儒家", "道家", "墨家", "法家", "名家", "纵横家", "后代学派流变", "古代宗教流变"],
        "中国历史学常识": [
            "古代职官与科举",
            "古代礼俗与称谓",
            "古代衣食住行",
            "古代军事战争",
            "古代经济发展",
            "古代图书文物",
            "近现代史学常识",
        ],
        "中国文学常识": ["文体流变", "代表作家及作品", "创作群体及文学流派", "文学总集", "民族史诗"],
        "中国艺术常识": ["书法", "绘画", "雕塑", "建筑", "音乐", "戏剧", "民俗", "陶瓷"],
        "中国古代科技常识": ["天文历法与算学", "地理舆图", "农业水利", "医学", "科技发明"],
    },
    "英语运用": {
        "语言知识": ["词汇", "语法", "语用"],
        "阅读理解": ["阅读主旨题", "阅读细节题", "阅读推断题", "阅读词义题", "阅读结构题"],
    },
    "逻辑推理": {
        "概念": ["概念种类", "概念关系", "定义", "划分"],
        "判断": ["判断种类", "判断关系"],
        "推理": ["演绎推理", "归纳推理", "类比推理", "综合推理"],
        "论证": ["加强", "削弱", "解释", "谬误识别"],
    },
    "数学基础": {
        "一元函数微分学": [
            "极限",
            "连续",
            "导数",
            "微分",
            "高阶导数",
            "洛必达法则",
            "单调性",
            "极值与最值",
            "凹凸性",
            "拐点",
            "渐近线",
        ],
        "一元函数积分学": [
            "原函数",
            "定积分",
            "变限定积分",
            "牛顿-莱布尼兹公式",
            "换元积分",
            "分部积分",
            "几何应用",
            "物理应用",
        ],
        "多元函数微分学": ["偏导数", "全微分", "二阶偏导", "链导法则", "隐函数求导", "二元函数极值"],
    },
}

ALLOWED_EXAM_CODES = {"Z001", "Z002"}
ALLOWED_ANSWERS = {"A", "B", "C", "D", "E"}
ALLOWED_SOURCE_TYPES = {"real_exam", "ai_generated", "manual", "source_extracted"}
REQUIRED_FIELDS = [
    "exam_code",
    "subject",
    "module",
    "submodule",
    "question_type",
    "stem",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "answer",
    "explanation",
    "difficulty",
]
IMPORT_COLUMNS = [
    "id",
    "exam_code",
    "subject",
    "module",
    "submodule",
    "question_type",
    "stem",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "option_e",
    "answer",
    "explanation",
    "difficulty",
    "source_type",
    "source_year",
    "passage_id",
]


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        raise FileNotFoundError(f"Env file not found: {env_path}")

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import generated questions JSON into Supabase questions table.")
    parser.add_argument(
        "--file",
        default=str(PROJECT_ROOT / "data" / "generated_questions_sample.json"),
        help="Path to the source JSON file.",
    )
    parser.add_argument(
        "--env-file",
        default=str(BACKEND_DIR / ".env"),
        help="Path to the backend env file with Supabase credentials.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate only, do not write to Supabase.",
    )
    return parser.parse_args()


def load_questions(json_path: Path) -> list[dict]:
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        questions = payload
    elif isinstance(payload, dict) and isinstance(payload.get("questions"), list):
        questions = payload["questions"]
    else:
        raise ValueError("JSON must be a list or an object with a 'questions' array")

    if not questions:
        raise ValueError("No questions found in JSON file")

    return questions


def is_blank(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return False


def validate_uuid(value: object, field_name: str) -> None:
    if value in (None, ""):
        return
    try:
        UUID(str(value))
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid UUID or null") from exc


def validate_question(question: dict, index: int) -> dict:
    if not isinstance(question, dict):
        raise ValueError(f"Question #{index} must be a JSON object")

    for field in REQUIRED_FIELDS:
        if is_blank(question.get(field)):
            raise ValueError(f"Question #{index} missing required field: {field}")

    exam_code = str(question["exam_code"]).strip()
    if exam_code not in ALLOWED_EXAM_CODES:
        raise ValueError(f"Question #{index} has invalid exam_code: {exam_code}")

    answer = str(question["answer"]).strip().upper()
    if answer not in ALLOWED_ANSWERS:
        raise ValueError(f"Question #{index} has invalid answer: {answer}")

    subject = str(question["subject"]).strip()
    module = str(question["module"]).strip()
    submodule = str(question["submodule"]).strip()

    if subject not in KNOWLEDGE_TREE:
        raise ValueError(f"Question #{index} has unknown subject: {subject}")
    if module not in KNOWLEDGE_TREE[subject]:
        raise ValueError(f"Question #{index} has unknown module for {subject}: {module}")
    if submodule not in KNOWLEDGE_TREE[subject][module]:
        raise ValueError(f"Question #{index} has unknown submodule for {subject}/{module}: {submodule}")

    difficulty = question["difficulty"]
    if not isinstance(difficulty, int) or difficulty < 1 or difficulty > 5:
        raise ValueError(f"Question #{index} has invalid difficulty: {difficulty}")

    source_year = question.get("source_year")
    if source_year is not None and not isinstance(source_year, int):
        raise ValueError(f"Question #{index} source_year must be an integer or null")

    source_type = question.get("source_type")
    if not is_blank(source_type) and source_type not in ALLOWED_SOURCE_TYPES:
        raise ValueError(
            f"Question #{index} has invalid source_type: {source_type}. "
            f"Allowed: {', '.join(sorted(ALLOWED_SOURCE_TYPES))}"
        )

    validate_uuid(question.get("id"), "id")
    validate_uuid(question.get("passage_id"), "passage_id")

    normalized = {}
    for column in IMPORT_COLUMNS:
        if column in question:
            normalized[column] = question[column]

    normalized["exam_code"] = exam_code
    normalized["answer"] = answer
    normalized["subject"] = subject
    normalized["module"] = module
    normalized["submodule"] = submodule
    normalized["question_type"] = str(question["question_type"]).strip()
    normalized["stem"] = str(question["stem"]).strip()
    normalized["option_a"] = str(question["option_a"]).strip()
    normalized["option_b"] = str(question["option_b"]).strip()
    normalized["option_c"] = str(question["option_c"]).strip()
    normalized["option_d"] = str(question["option_d"]).strip()
    if not is_blank(question.get("option_e")):
        normalized["option_e"] = str(question["option_e"]).strip()
    normalized["explanation"] = str(question["explanation"]).strip()

    return normalized


def duplicate_key(question: dict) -> tuple[str, str, str, str]:
    return (
        question["stem"],
        question["subject"],
        question["module"],
        question["submodule"],
    )


def find_duplicate_in_supabase(supabase, question: dict) -> str | None:
    response = (
        supabase.table("questions")
        .select("id")
        .eq("stem", question["stem"])
        .eq("subject", question["subject"])
        .eq("module", question["module"])
        .eq("submodule", question["submodule"])
        .limit(1)
        .execute()
    )
    if response.data:
        return response.data[0]["id"]
    return None


def print_validation_summary(total_count: int, valid_count: int, failures: list[str]) -> None:
    print("Validation summary")
    print(f"  Total questions: {total_count}")
    print(f"  Valid questions: {valid_count}")
    print(f"  Invalid questions: {len(failures)}")
    if failures:
        print("Invalid question details:")
        for reason in failures:
            print(f"  - {reason}")


def main() -> int:
    args = parse_args()
    json_path = Path(args.file).resolve()
    env_path = Path(args.env_file).resolve()

    try:
        load_env_file(env_path)
        sys.path.insert(0, str(BACKEND_DIR))
        from app.db import get_supabase_admin

        questions = load_questions(json_path)
    except Exception as exc:
        print(f"[ERROR] Initialization failed: {exc}")
        return 1

    valid_questions: list[dict] = []
    failures: list[str] = []

    for index, question in enumerate(questions, start=1):
        try:
            valid_questions.append(validate_question(question, index))
        except Exception as exc:
            failures.append(str(exc))

    print_validation_summary(len(questions), len(valid_questions), failures)

    if args.dry_run:
        seen_keys: set[tuple[str, str, str, str]] = set()
        duplicate_in_file = 0
        for question in valid_questions:
            key = duplicate_key(question)
            if key in seen_keys:
                duplicate_in_file += 1
            seen_keys.add(key)

        print("[DRY RUN] No data was written to Supabase.")
        print(f"[DRY RUN] Duplicate questions inside file: {duplicate_in_file}")
        return 0 if not failures else 1

    supabase = get_supabase_admin()
    success_count = 0
    skipped_duplicate_count = 0
    seen_keys: set[tuple[str, str, str, str]] = set()

    for index, question in enumerate(valid_questions, start=1):
        try:
            key = duplicate_key(question)
            if key in seen_keys:
                skipped_duplicate_count += 1
                continue
            seen_keys.add(key)

            duplicate_id = find_duplicate_in_supabase(supabase, question)
            if duplicate_id:
                skipped_duplicate_count += 1
                continue

            supabase.table("questions").insert(question).execute()
            success_count += 1
        except Exception as exc:
            stem_preview = question["stem"][:30]
            failures.append(f"Question #{index} insert failed ({stem_preview}...): {exc}")

    print("Import finished.")
    print(f"  Success inserted: {success_count}")
    print(f"  Skipped duplicates: {skipped_duplicate_count}")
    print(f"  Failed: {len(failures)}")
    if failures:
        print("Failure details:")
        for reason in failures:
            print(f"  - {reason}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
