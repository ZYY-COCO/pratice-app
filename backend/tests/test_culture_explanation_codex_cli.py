from __future__ import annotations

import asyncio
import json
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from app.services.culture_explanation_codex_cli import (
    CodexCLIExecutionError,
    CodexCLIOutputError,
    CodexCLITimeoutError,
    CodexCLIUnavailableError,
    build_culture_explanation_codex_output_schema,
    build_culture_explanation_codex_prompt,
    preflight_culture_explanation_codex_cli,
    regenerate_culture_explanation_batch_with_codex_cli,
)


QUESTION_ID = "fixed-culture-question"
SECOND_ID = "second-culture-question"
OLD_EXPLANATION = "OLD_EXPLANATION_MUST_NOT_REACH_CODEX"


def build_question(question_id: str = QUESTION_ID) -> dict[str, object]:
    return {
        "id": question_id,
        "exam_code": "COMMON",
        "subject": "中华文化",
        "module": "中国历史学常识",
        "submodule": "先秦史",
        "question_type": "single_choice",
        "stem": "秦国主持变法并推行法家政策的人物是？",
        "option_a": "商鞅",
        "option_b": "孔子",
        "option_c": "墨子",
        "option_d": "庄子",
        "answer": "A",
        "difficulty": 2,
        "explanation": OLD_EXPLANATION,
    }


def minimal_response(question_id: str = QUESTION_ID) -> str:
    return json.dumps(
        {
            "updates": [
                {
                    "id": question_id,
                    "culture_v3": {
                        "version": "3.0",
                    },
                }
            ]
        },
        ensure_ascii=False,
    )


class CultureExplanationCodexSchemaTests(unittest.TestCase):
    def test_schema_is_strict_at_every_object_level_and_locks_batch_ids(self):
        rows = [build_question(), build_question(SECOND_ID)]

        schema = build_culture_explanation_codex_output_schema(rows)

        self.assertFalse(schema["additionalProperties"])
        updates = schema["properties"]["updates"]
        self.assertEqual(updates["minItems"], 2)
        self.assertEqual(updates["maxItems"], 2)
        update = updates["items"]
        self.assertEqual(update["required"], ["id", "culture_v3"])
        self.assertFalse(update["additionalProperties"])
        self.assertEqual(update["properties"]["id"]["enum"], [QUESTION_ID, SECOND_ID])

        culture_v3 = update["properties"]["culture_v3"]
        self.assertFalse(culture_v3["additionalProperties"])
        self.assertEqual(culture_v3["properties"]["version"]["const"], "3.0")
        self.assertEqual(culture_v3["properties"]["scope_level"]["const"], "core")
        self.assertFalse(
            culture_v3["properties"]["fact_anchor"]["additionalProperties"]
        )
        self.assertFalse(
            culture_v3["properties"]["reasoning_steps"]["additionalProperties"]
        )
        option_analysis = culture_v3["properties"]["option_analysis"]
        self.assertEqual(option_analysis["required"], ["A", "B", "C", "D"])
        self.assertFalse(option_analysis["additionalProperties"])
        for label in "ABCD":
            self.assertFalse(option_analysis["properties"][label]["additionalProperties"])

    def test_schema_rejects_blank_duplicate_and_oversized_batches(self):
        with self.assertRaisesRegex(ValueError, "must have an id"):
            build_culture_explanation_codex_output_schema([build_question("")])
        with self.assertRaisesRegex(ValueError, "unique"):
            build_culture_explanation_codex_output_schema(
                [build_question(), build_question()]
            )
        with self.assertRaisesRegex(ValueError, "at most 6"):
            build_culture_explanation_codex_output_schema(
                [build_question(f"id-{index}") for index in range(7)]
            )

    def test_prompt_reuses_narrow_contract_without_old_explanation(self):
        prompt = build_culture_explanation_codex_prompt(
            [build_question()],
            feedback_by_id={QUESTION_ID: ["bridge 缺少具体中间事实"]},
        )

        self.assertNotIn(OLD_EXPLANATION, prompt)
        self.assertNotIn('"explanation"', prompt)
        self.assertIn("不得改题、改选项、改答案、改分类或改难度", prompt)
        self.assertIn("bridge 缺少具体中间事实", prompt)
        self.assertIn("不要读取目录、文件或外部上下文", prompt)


class CultureExplanationCodexExecutionTests(unittest.TestCase):
    def _run(self, **kwargs):
        return asyncio.run(
            regenerate_culture_explanation_batch_with_codex_cli(
                [build_question()],
                timeout_seconds=17,
                **kwargs,
            )
        )

    @mock.patch(
        "app.services.culture_explanation_codex_cli._resolve_codex_cli",
        return_value="codex-test",
    )
    @mock.patch(
        "app.services.culture_explanation_codex_cli.parse_culture_explanation_regeneration_response"
    )
    @mock.patch("app.services.culture_explanation_codex_cli.subprocess.run")
    def test_invocation_is_isolated_structured_and_passed_to_existing_parser(
        self,
        run_mock,
        parse_mock,
        _resolve_mock,
    ):
        observed: dict[str, object] = {}
        parser_result = {"accepted": [], "rejected": [], "raw": {}}
        parse_mock.return_value = parser_result

        def fake_run(command, **kwargs):
            observed["command"] = list(command)
            observed["kwargs"] = kwargs
            schema_path = Path(command[command.index("--output-schema") + 1])
            output_path = Path(command[command.index("--output-last-message") + 1])
            observed["temporary_path"] = schema_path.parent
            observed["schema"] = json.loads(schema_path.read_text(encoding="utf-8"))
            output_path.write_text(minimal_response(), encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        run_mock.side_effect = fake_run

        result = self._run(model="gpt-test")

        command = observed["command"]
        self.assertEqual(command[:2], ["codex-test", "exec"])
        self.assertIn("--ephemeral", command)
        self.assertIn("--ignore-rules", command)
        self.assertNotIn("--ignore-user-config", command)
        self.assertEqual(command.count("--disable"), 3)
        self.assertIn("plugins", command)
        self.assertIn("remote_plugin", command)
        self.assertIn("apps", command)
        self.assertEqual(command[command.index("--enable") + 1], "skip_host_skill_discovery")
        self.assertEqual(command[command.index("-s") + 1], "read-only")
        self.assertIn("--skip-git-repo-check", command)
        self.assertEqual(command[command.index("--model") + 1], "gpt-test")
        self.assertEqual(command[-1], "-")

        kwargs = observed["kwargs"]
        self.assertFalse(kwargs["shell"])
        self.assertEqual(kwargs["timeout"], 17)
        self.assertEqual(Path(kwargs["cwd"]), observed["temporary_path"])
        self.assertIn("只把符合输出 Schema 的 JSON 对象", kwargs["input"])
        self.assertNotIn(OLD_EXPLANATION, kwargs["input"])
        self.assertFalse(Path(observed["temporary_path"]).exists())

        parse_mock.assert_called_once()
        parser_content, questions_by_id = parse_mock.call_args.args
        self.assertEqual(json.loads(parser_content), json.loads(minimal_response()))
        self.assertEqual(list(questions_by_id), [QUESTION_ID])
        self.assertIs(result, parser_result)
        self.assertEqual(result["model"], "codex-cli/gpt-test")

    @mock.patch("app.services.culture_explanation_codex_cli.shutil.which", return_value=None)
    @mock.patch("app.services.culture_explanation_codex_cli.subprocess.run")
    def test_missing_cli_is_reported_before_process_start(self, run_mock, _which_mock):
        with self.assertRaisesRegex(CodexCLIUnavailableError, "was not found"):
            self._run()
        run_mock.assert_not_called()

    @mock.patch(
        "app.services.culture_explanation_codex_cli._resolve_codex_cli",
        return_value="codex-test",
    )
    @mock.patch("app.services.culture_explanation_codex_cli.subprocess.run")
    def test_nonzero_exit_is_bounded_and_temp_files_are_cleaned(
        self,
        run_mock,
        _resolve_mock,
    ):
        temporary_paths: list[Path] = []

        def fake_run(command, **_kwargs):
            schema_path = Path(command[command.index("--output-schema") + 1])
            temporary_paths.append(schema_path.parent)
            return subprocess.CompletedProcess(
                command,
                23,
                stdout="",
                stderr="  provider failed\nwith detail  ",
            )

        run_mock.side_effect = fake_run

        with self.assertRaises(CodexCLIExecutionError) as caught:
            self._run()

        self.assertEqual(caught.exception.returncode, 23)
        self.assertIn("provider failed with detail", str(caught.exception))
        self.assertTrue(temporary_paths)
        self.assertFalse(temporary_paths[0].exists())

    @mock.patch(
        "app.services.culture_explanation_codex_cli._resolve_codex_cli",
        return_value="codex-test",
    )
    @mock.patch("app.services.culture_explanation_codex_cli.subprocess.run")
    def test_timeout_is_mapped_and_temp_files_are_cleaned(
        self,
        run_mock,
        _resolve_mock,
    ):
        temporary_paths: list[Path] = []

        def fake_run(command, **kwargs):
            schema_path = Path(command[command.index("--output-schema") + 1])
            temporary_paths.append(schema_path.parent)
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])

        run_mock.side_effect = fake_run

        with self.assertRaisesRegex(CodexCLITimeoutError, "17 seconds"):
            self._run()
        self.assertFalse(temporary_paths[0].exists())

    def _assert_output_failure(self, output_text: str | None, expected: str) -> None:
        def fake_run(command, **_kwargs):
            output_path = Path(command[command.index("--output-last-message") + 1])
            if output_text is not None:
                output_path.write_text(output_text, encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        with mock.patch(
            "app.services.culture_explanation_codex_cli._resolve_codex_cli",
            return_value="codex-test",
        ), mock.patch(
            "app.services.culture_explanation_codex_cli.subprocess.run",
            side_effect=fake_run,
        ):
            with self.assertRaisesRegex(CodexCLIOutputError, expected):
                self._run()

    def test_missing_empty_and_invalid_json_outputs_are_rejected(self):
        cases = [
            (None, "without a last-message"),
            ("  \n", "empty last-message"),
            ("not-json", "not valid JSON"),
            ("[]", "root must be an object"),
        ]
        for output_text, expected in cases:
            with self.subTest(expected=expected):
                self._assert_output_failure(output_text, expected)

    @mock.patch(
        "app.services.culture_explanation_codex_cli._resolve_codex_cli",
        return_value="codex-test",
    )
    @mock.patch(
        "app.services.culture_explanation_codex_cli.parse_culture_explanation_regeneration_response",
        side_effect=ValueError("root 只能包含 updates"),
    )
    @mock.patch("app.services.culture_explanation_codex_cli.subprocess.run")
    def test_existing_parser_contract_error_is_mapped_to_output_error(
        self,
        run_mock,
        _parse_mock,
        _resolve_mock,
    ):
        def fake_run(command, **_kwargs):
            output_path = Path(command[command.index("--output-last-message") + 1])
            output_path.write_text(minimal_response(), encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        run_mock.side_effect = fake_run

        with self.assertRaisesRegex(CodexCLIOutputError, "violates the regeneration contract"):
            self._run()


class CultureExplanationCodexPreflightTests(unittest.TestCase):
    @mock.patch(
        "app.services.culture_explanation_codex_cli._resolve_codex_cli",
        return_value="codex-test",
    )
    @mock.patch("app.services.culture_explanation_codex_cli.subprocess.run")
    def test_preflight_reads_version_without_starting_exec(
        self,
        run_mock,
        _resolve_mock,
    ):
        run_mock.return_value = subprocess.CompletedProcess(
            ["codex-test", "--version"],
            0,
            stdout="codex-cli 0.test\n",
            stderr="",
        )

        result = preflight_culture_explanation_codex_cli(timeout_seconds=9)

        self.assertEqual(result, {"path": "codex-test", "version": "codex-cli 0.test"})
        command = run_mock.call_args.args[0]
        self.assertEqual(command[0], "codex-test")
        self.assertEqual(command[-1], "--version")
        self.assertNotIn("--ignore-user-config", command)
        self.assertEqual(command.count("--disable"), 3)
        self.assertIn("plugins", command)
        self.assertIn("remote_plugin", command)
        self.assertIn("apps", command)
        self.assertEqual(command[command.index("--enable") + 1], "skip_host_skill_discovery")
        self.assertNotIn("exec", command)
        self.assertEqual(run_mock.call_args.kwargs["timeout"], 9)
        self.assertFalse(run_mock.call_args.kwargs["shell"])

    @mock.patch("app.services.culture_explanation_codex_cli.shutil.which", return_value=None)
    @mock.patch("app.services.culture_explanation_codex_cli.subprocess.run")
    def test_preflight_missing_cli_fails_before_process_start(
        self,
        run_mock,
        _which_mock,
    ):
        with self.assertRaisesRegex(CodexCLIUnavailableError, "was not found"):
            preflight_culture_explanation_codex_cli()
        run_mock.assert_not_called()

    @mock.patch(
        "app.services.culture_explanation_codex_cli._resolve_codex_cli",
        return_value="codex-test",
    )
    @mock.patch("app.services.culture_explanation_codex_cli.subprocess.run")
    def test_preflight_nonzero_exit_is_reported(
        self,
        run_mock,
        _resolve_mock,
    ):
        run_mock.return_value = subprocess.CompletedProcess(
            ["codex-test", "--version"],
            7,
            stdout="",
            stderr="version failed",
        )

        with self.assertRaises(CodexCLIExecutionError) as caught:
            preflight_culture_explanation_codex_cli()

        self.assertEqual(caught.exception.returncode, 7)
        self.assertIn("version failed", str(caught.exception))

    @mock.patch(
        "app.services.culture_explanation_codex_cli._resolve_codex_cli",
        return_value="codex-test",
    )
    @mock.patch("app.services.culture_explanation_codex_cli.subprocess.run")
    def test_preflight_timeout_is_reported(
        self,
        run_mock,
        _resolve_mock,
    ):
        run_mock.side_effect = subprocess.TimeoutExpired(
            ["codex-test", "--version"],
            4,
        )

        with self.assertRaisesRegex(CodexCLITimeoutError, "4 seconds"):
            preflight_culture_explanation_codex_cli(timeout_seconds=4)


if __name__ == "__main__":
    unittest.main()
