"""Canonical question classification catalog used by the admin write paths."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


_CATALOG_PATH = Path(__file__).resolve().parents[1] / "question_catalog.json"


@lru_cache(maxsize=1)
def get_question_catalog() -> dict[str, dict[str, Any]]:
    with _CATALOG_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def validate_question_classification(
    *,
    exam_code: str,
    subject: str,
    module: str,
    submodule: str,
) -> None:
    catalog = get_question_catalog()
    subject_config = catalog.get(subject)
    if not subject_config:
        raise ValueError(f"不支持的科目：{subject}")

    allowed_exam_codes = set(subject_config.get("allowed_exam_codes") or [subject_config["exam_code"]])
    if exam_code not in allowed_exam_codes:
        raise ValueError(f"{subject} 不支持考试代码 {exam_code}")

    modules = subject_config.get("modules") or {}
    allowed_submodules = modules.get(module)
    if allowed_submodules is None:
        raise ValueError(f"{subject} 不支持模块：{module}")
    if submodule not in allowed_submodules:
        raise ValueError(f"{subject} / {module} 不支持考点：{submodule}")
