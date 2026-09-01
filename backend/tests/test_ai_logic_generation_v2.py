from __future__ import annotations

import unittest

from app.routes.ai import (
    _build_deepseek_messages,
    _canonicalize_logic_target,
    _safe_question_candidate,
)
from app.schemas.ai import AiTrainingTarget
from tests.test_logic_question_quality import build_logic_metadata, build_logic_question


class AiLogicGenerationV2Tests(unittest.TestCase):
    def setUp(self):
        self.target = AiTrainingTarget(
            subject="逻辑推理",
            module="推理规则",
            submodule="演绎推理",
            difficulty="标准提升",
            question_count=5,
            basis="条件推理专项训练",
        )

    def test_target_legacy_alias_is_canonicalized(self):
        target = _canonicalize_logic_target(self.target)
        self.assertEqual(target.module, "推理")
        self.assertEqual(target.submodule, "演绎推理")

    def test_prompt_contains_v2_contract_and_retry_feedback(self):
        target = _canonicalize_logic_target(self.target)
        messages = _build_deepseek_messages(
            target,
            [],
            request_count=5,
            quality_feedback=["上一题答案不唯一"],
        )
        content = "\n".join(message["content"] for message in messages)
        self.assertIn("logic_v2", content)
        self.assertIn("formal_spec", content)
        self.assertIn("上一题答案不唯一", content)

    def test_only_v2_verified_candidate_is_accepted(self):
        target = _canonicalize_logic_target(self.target)
        raw = {**build_logic_question(), "logic_v2": build_logic_metadata()}
        row, reasons = _safe_question_candidate(raw, target, "Z001")
        self.assertIsNotNone(row, reasons)
        self.assertEqual(reasons, [])
        self.assertEqual(row["module"], "推理")

        raw.pop("logic_v2")
        row, reasons = _safe_question_candidate(raw, target, "Z001")
        self.assertIsNone(row)
        self.assertTrue(any("logic_v2" in reason for reason in reasons))


if __name__ == "__main__":
    unittest.main()
