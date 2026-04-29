from __future__ import annotations

import json
from pathlib import Path

from generate_common_culture_integrated_batch_005 import CARDS


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "common_culture_advanced_batch_006.json"


def option_map(values: list[str], correct_position: int) -> tuple[dict[str, str], str]:
    letters = ["A", "B", "C", "D"]
    rotated = values[correct_position % 4 :] + values[: correct_position % 4]
    correct_value = values[0]
    mapped = dict(zip(letters, rotated))
    answer = next(letter for letter, value in mapped.items() if value == correct_value)
    return mapped, answer


def q(
    module: str,
    submodule: str,
    stem: str,
    options: list[str],
    explanation: str,
    difficulty: int,
    position: int,
) -> dict:
    mapped, answer = option_map(options, position)
    return {
        "exam_code": "COMMON",
        "subject": "中华文化",
        "module": module,
        "submodule": submodule,
        "question_type": "single_choice",
        "stem": stem,
        "option_a": mapped["A"],
        "option_b": mapped["B"],
        "option_c": mapped["C"],
        "option_d": mapped["D"],
        "answer": answer,
        "explanation": explanation,
        "difficulty": difficulty,
        "source_type": "source_extracted",
        "source_year": 2026,
        "passage_id": None,
    }


def card_at(index: int):
    return CARDS[index % len(CARDS)]


def concept_label(item) -> str:
    module, submodule, concept, *_ = item
    return f"{concept} / {module} / {submodule}"


def build_questions() -> list[dict]:
    questions: list[dict] = []

    for index, item in enumerate(CARDS):
        module, submodule, concept, clue, distractors, wrong_clues, _difficulty = item
        distractor_items = [card_at(index + 17), card_at(index + 41), card_at(index + 73)]
        options = [
            f"{concept} / {module} / {submodule}",
            *[concept_label(other) for other in distractor_items],
        ]
        questions.append(
            q(
                module,
                submodule,
                f"题干若考查“{clue}”，最准确的知识点归类是：",
                options,
                f"该描述对应“{concept}”，应归入“{module} / {submodule}”。",
                3 if index % 4 == 0 else 4,
                index,
            )
        )

    second_round_caps = {
        "中国哲学常识": 20,
        "中国历史学常识": 21,
        "中国文学常识": 20,
        "中国艺术常识": 15,
        "中国古代科技常识": 16,
    }
    second_round_counts = {module: 0 for module in second_round_caps}

    for index, item in enumerate(CARDS):
        module, submodule, concept, clue, _distractors, wrong_clues, _difficulty = item
        if second_round_counts[module] >= second_round_caps[module]:
            continue
        second_round_counts[module] += 1
        options = [
            f"{concept}：{clue}",
            f"{concept}：{wrong_clues[0]}",
            f"{concept}：{wrong_clues[1]}",
            f"{concept}：{wrong_clues[2]}",
        ]
        questions.append(
            q(
                module,
                submodule,
                f"下列关于“{concept}”与易混知识点的辨析，正确的是：",
                options,
                f"“{concept}”的准确理解是：{clue}。",
                4,
                index + 1,
            )
        )

    if len(questions) != 200:
        raise RuntimeError(f"Expected 200 questions, got {len(questions)}")
    stems = [item["stem"] for item in questions]
    repeated = sorted({stem for stem in stems if stems.count(stem) > 1})
    if repeated:
        raise RuntimeError("Duplicate stems inside generated batch:\n" + "\n".join(repeated))
    return questions


def main() -> int:
    questions = build_questions()
    OUTPUT_PATH.write_text(
        json.dumps({"questions": questions}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {len(questions)} questions to {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")
    module_counts: dict[str, int] = {}
    difficulty_counts: dict[int, int] = {}
    for item in questions:
        module_counts[item["module"]] = module_counts.get(item["module"], 0) + 1
        difficulty_counts[item["difficulty"]] = difficulty_counts.get(item["difficulty"], 0) + 1
    for module, count in module_counts.items():
        print(f"  {module}: {count}")
    print("Difficulty:", dict(sorted(difficulty_counts.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
