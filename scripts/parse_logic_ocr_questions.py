from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = PROJECT_ROOT / "data" / "logic_sources" / "logic_7_lessons_part_001_ocr_combined.txt"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "z001_logic_reasoning_logic7_part001_batch_001.json"


NOISE_LINES = {
    "管理类、经济类联考",
    "逻辑要点7讲",
    "扫码免费听",
    "本节讲解",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parse OCR text from logic PDF into importable question JSON.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Combined OCR text file.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output JSON path.")
    return parser.parse_args()


def clean_text(value: str) -> str:
    lines = []
    for raw_line in value.splitlines():
        line = raw_line.strip()
        if not line or line in NOISE_LINES or line.startswith("==="):
            continue
        lines.append(line)
    text = "\n".join(lines)
    text = re.sub(r"[ \t]+", " ", text)
    text = text.replace("ⅡI", "Ⅲ").replace("IⅡ", "Ⅱ").replace("购要条件", "必要条件")
    return text.strip()


def split_blocks(text: str) -> list[str]:
    pattern = re.compile(r"(?=例\d+\.\d+)")
    parts = pattern.split(text)
    return [part.strip() for part in parts if part.strip().startswith("例")]


def find_answer(block: str) -> str | None:
    match = re.search(r"【答案】\s*([A-E])", block)
    return match.group(1) if match else None


def extract_options(question_area: str) -> tuple[str, dict[str, str]]:
    markers = list(re.finditer(r"(?<![A-Za-z0-9])([A-E])[\.\．]\s*", question_area))
    if len(markers) < 4:
        return "", {}

    stem = question_area[: markers[0].start()].strip()
    options: dict[str, str] = {}

    for index, marker in enumerate(markers):
        key = marker.group(1)
        start = marker.end()
        end = markers[index + 1].start() if index + 1 < len(markers) else len(question_area)
        value = question_area[start:end].strip()
        value = re.sub(r"\s*\n\s*", "", value)
        if value:
            options[key] = value

    return stem, options


def classify_question(stem: str, explanation: str) -> tuple[str, str]:
    haystack = f"{stem}\n{explanation}"

    if any(keyword in haystack for keyword in ["支持", "加强", "论述提供支持"]):
        return "论证", "加强"
    if any(keyword in haystack for keyword in ["质疑", "削弱", "反驳", "不支持"]):
        return "论证", "削弱"
    if any(keyword in haystack for keyword in ["解释上述", "解释以上", "解释这一"]):
        return "论证", "解释"
    if "谬误" in haystack:
        return "论证", "谬误识别"
    if any(keyword in haystack for keyword in ["联言", "选言", "模态", "性质命题", "当且仅当", "必要条件", "充分条件"]):
        return "判断", "判断种类"
    if any(keyword in haystack for keyword in ["结构相似", "推理结构", "类比"]):
        return "推理", "类比推理"
    if any(keyword in haystack for keyword in ["根据以上信息", "可以得出", "安排", "分配", "对应", "一一对应", "真假"]):
        return "推理", "综合推理"
    return "推理", "演绎推理"


def build_question(block: str, index: int) -> dict | None:
    block = clean_text(block)
    answer = find_answer(block)
    if not answer:
        return None

    before_answer = block.split("【答案】", 1)[0]
    if "【详细解析】" in before_answer:
        question_area, explanation_area = before_answer.split("【详细解析】", 1)
    else:
        question_area, explanation_area = before_answer, ""

    stem, options = extract_options(question_area)
    if not stem or not all(key in options for key in ["A", "B", "C", "D"]):
        return None
    if answer == "E" and "E" not in options:
        return None

    title_match = re.match(r"(例\d+\.\d+)", stem)
    source_label = title_match.group(1) if title_match else f"逻辑资料题{index}"
    stem = re.sub(r"^例\d+\.\d+\s*", "", stem).strip()
    explanation = explanation_area.strip() or f"本题答案为 {answer}。"

    module, submodule = classify_question(stem, explanation)
    question = {
        "exam_code": "Z001",
        "subject": "逻辑推理",
        "module": module,
        "submodule": submodule,
        "question_type": "single_choice",
        "stem": stem,
        "option_a": options["A"],
        "option_b": options["B"],
        "option_c": options["C"],
        "option_d": options["D"],
        "answer": answer,
        "explanation": f"{source_label}。{explanation}",
        "difficulty": 3 if "真题" in stem else 2,
        "source_type": "source_extracted",
        "source_year": 2025,
        "passage_id": None,
    }
    if options.get("E"):
        question["option_e"] = options["E"]
    return question


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()

    text = input_path.read_text(encoding="utf-8")
    blocks = split_blocks(text)
    questions = []
    skipped = 0

    for index, block in enumerate(blocks, start=1):
        question = build_question(block, index)
        if question:
            questions.append(question)
        else:
            skipped += 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps({"questions": questions}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Parsed questions: {len(questions)}")
    print(f"Skipped blocks: {skipped}")
    print(f"Output: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
