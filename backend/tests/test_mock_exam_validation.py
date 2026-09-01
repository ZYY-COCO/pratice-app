from copy import deepcopy
import unittest

from app.routes import mock_exams


def build_valid_mock_exam(exam_code: str = "Z001") -> tuple[list[dict], dict[str, dict]]:
    third_subject = "数学基础" if exam_code == "Z002" else "逻辑推理"
    sections = (
        ("culture", 20, "中华文化", "中国历史", "COMMON"),
        ("english", 20, "英语运用", "语言知识", "COMMON"),
        ("third", 15, third_subject, third_subject, exam_code),
    )
    difficulties = [1] * 19 + [3] * 28 + [4] * 8
    item_rows: list[dict] = []
    question_by_id: dict[str, dict] = {}
    global_index = 0

    for section_key, count, subject, module, question_exam_code in sections:
        for section_index in range(count):
            question_id = f"{section_key}-{section_index + 1}"
            question_by_id[question_id] = {
                "id": question_id,
                "exam_code": question_exam_code,
                "subject": subject,
                "module": module,
                "submodule": f"考点 {section_index + 1}",
                "question_type": "single_choice",
                "stem": f"{section_key} 唯一题干 {section_index + 1}",
                "difficulty": difficulties[global_index],
                "source_type": "manual",
                "status": "active" if global_index % 2 == 0 else "archived",
                "review_status": "approved" if global_index % 2 == 0 else "pending",
            }
            item_rows.append({"question_id": question_id, "section_key": section_key})
            global_index += 1

    return item_rows, question_by_id


class MockExamValidationTests(unittest.TestCase):
    def test_mixed_published_and_unpublished_questions_are_valid(self):
        item_rows, question_by_id = build_valid_mock_exam()

        result = mock_exams.validate_mock_exam_selection(
            "Z001",
            item_rows,
            question_by_id,
            require_complete=True,
        )

        self.assertEqual({row["status"] for row in question_by_id.values()}, {"active", "archived"})
        self.assertTrue(result.valid, result.errors)
        self.assertEqual(result.question_count, 55)
        self.assertEqual(result.total_score, 105)
        self.assertEqual(
            {item.key: item.selected_count for item in result.difficulty},
            {"basic": 19, "medium": 28, "hard": 8},
        )

    def test_duplicate_question_is_rejected(self):
        item_rows, question_by_id = build_valid_mock_exam()
        duplicated = deepcopy(item_rows)
        duplicated[-1]["question_id"] = duplicated[-2]["question_id"]

        result = mock_exams.validate_mock_exam_selection(
            "Z001",
            duplicated,
            question_by_id,
            require_complete=True,
        )

        self.assertFalse(result.valid)
        self.assertTrue(any("重复选择" in error for error in result.errors))

    def test_reading_question_is_rejected(self):
        item_rows, question_by_id = build_valid_mock_exam()
        question_by_id["english-1"]["stem"] = "阅读理解材料：请选择正确答案"

        result = mock_exams.validate_mock_exam_selection(
            "Z001",
            item_rows,
            question_by_id,
            require_complete=True,
        )

        self.assertFalse(result.valid)
        self.assertTrue(any("阅读类题目" in error for error in result.errors))

    def test_temporary_ai_question_is_rejected(self):
        item_rows, question_by_id = build_valid_mock_exam()
        question_by_id["culture-1"]["source_type"] = mock_exams.AI_QUESTION_SOURCE_TYPE

        result = mock_exams.validate_mock_exam_selection(
            "Z001",
            item_rows,
            question_by_id,
            require_complete=True,
        )

        self.assertFalse(result.valid)
        self.assertTrue(any("临时 AI 训练题" in error for error in result.errors))

    def test_wrong_subject_and_incomplete_paper_are_rejected(self):
        item_rows, question_by_id = build_valid_mock_exam()
        question_by_id["third-1"]["subject"] = "数学基础"
        incomplete = item_rows[:-1]

        result = mock_exams.validate_mock_exam_selection(
            "Z001",
            incomplete,
            question_by_id,
            require_complete=True,
        )

        self.assertFalse(result.valid)
        self.assertTrue(any("不属于" in error for error in result.errors))
        self.assertTrue(any("整卷需要 55 道" in error for error in result.errors))

    def test_wrong_difficulty_ratio_is_rejected(self):
        item_rows, question_by_id = build_valid_mock_exam()
        question_by_id["culture-1"]["difficulty"] = 4

        result = mock_exams.validate_mock_exam_selection(
            "Z001",
            item_rows,
            question_by_id,
            require_complete=True,
        )

        self.assertFalse(result.valid)
        self.assertTrue(any("基础难度需要 19 题" in error for error in result.errors))
        self.assertTrue(any("较难难度需要 8 题" in error for error in result.errors))

    def test_first_publish_keeps_v1_and_later_publish_increments(self):
        self.assertEqual(mock_exams._next_publish_version({"status": "draft", "version": 1}), 1)
        self.assertEqual(mock_exams._next_publish_version({"status": "published", "version": 1}), 2)
        self.assertEqual(mock_exams._next_publish_version({"status": "archived", "version": 2}), 3)
        self.assertEqual(mock_exams._next_publish_version({"status": "draft", "version": 3}), 3)

    def test_question_option_classification_accepts_module_and_submodule(self):
        module, submodule = mock_exams._normalize_question_option_classification(
            "Z001",
            "culture",
            "中国哲学常识",
            "儒家",
        )

        self.assertEqual(module, "中国哲学常识")
        self.assertEqual(submodule, "儒家")

    def test_question_option_classification_infers_single_english_module(self):
        module, submodule = mock_exams._normalize_question_option_classification(
            "Z001",
            "english",
            None,
            "语法",
        )

        self.assertEqual(module, "语言知识")
        self.assertEqual(submodule, "语法")

    def test_question_option_classification_rejects_mismatched_submodule(self):
        with self.assertRaisesRegex(ValueError, "不支持考点"):
            mock_exams._normalize_question_option_classification(
                "Z001",
                "culture",
                "中国哲学常识",
                "书法",
            )


if __name__ == "__main__":
    unittest.main()
