def classify_accuracy(accuracy: float) -> tuple[str, str]:
    """Return a Chinese ability level and practice recommendation."""

    if accuracy >= 80:
        return "稳定", "保持节奏，可适当挑战更高难度题目。"
    if accuracy >= 60:
        return "一般", "建议继续巩固本知识点，优先复盘错题解析。"
    if accuracy >= 40:
        return "薄弱", "建议安排专项训练，并把典型错题加入复习计划。"
    return "重点补强", "建议从基础概念重新梳理，再进行 5-10 题小组练习。"


def build_ability_item(row: dict) -> dict:
    level, recommendation = classify_accuracy(float(row.get("accuracy") or 0))
    return {
        **row,
        "accuracy": float(row.get("accuracy") or 0),
        "level": level,
        "recommendation": recommendation,
    }
