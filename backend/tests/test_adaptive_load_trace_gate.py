from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from datetime import datetime, timedelta
from pathlib import Path
from types import ModuleType


def _load_gate() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "scripts" / "validate_adaptive_load_trace.py"
    spec = importlib.util.spec_from_file_location("adaptive_load_trace_gate", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = _load_gate()
REQUIRED_VUS = {50, 100, 200}
PASSING_RECORDS = gate._synthetic_self_test_records(required_vus=REQUIRED_VUS)


def _evaluate(records: list[dict], **overrides):
    options = {
        "required_vus": REQUIRED_VUS,
        "minimum_samples": 30,
        "minimum_transitions_per_vu": 1500,
        "minimum_natural_special_transitions_per_vu": 300,
        "minimum_stable_seconds": 300.0,
    }
    options.update(overrides)
    return gate.evaluate(records, **options)


def _replace(records: list[dict], index: int, **changes) -> list[dict]:
    changed_records = list(records)
    changed = dict(changed_records[index])
    changed.update(changes)
    changed_records[index] = changed
    return changed_records


def _first_index(*, metric: str, vus: int | None = None) -> int:
    return next(
        index
        for index, record in enumerate(PASSING_RECORDS)
        if record["metric"] == metric and (vus is None or record["vus"] == vus)
    )


def _manifest_hash(items: list[dict]) -> str:
    return gate._manifest_hash(
        tuple(
            sorted(
                (item["position"], item["item_id"], item["question_id"])
                for item in items
            )
        )
    )


def _valid_manifest_conflict(*, vus: int = 50) -> dict:
    sheet = dict(PASSING_RECORDS[_first_index(metric="comprehensive_sheet_ready", vus=vus)])
    sheet.update(
        event_id=f"manifest-conflict-event-{vus}",
        request_id=f"manifest-conflict-request-{vus}",
        sample_kind="audit_only",
        expected_outcome="expected_conflict",
        status_code=409,
        error_code="ADAPTIVE_COMPREHENSIVE_SUBMISSION_CONFLICT",
        conflict_scenario="comprehensive_manifest_conflict",
        attempt_group_id=f"manifest-conflict-group-{vus}",
        concurrency=2,
        expected_error_code="ADAPTIVE_COMPREHENSIVE_SUBMISSION_CONFLICT",
        attempted_manifest_hash="a" * 64,
    )
    sheet.pop("manifest_items")
    sheet.pop("manifest_question_count")
    return sheet


class AdaptiveLoadTraceGateTests(unittest.TestCase):
    def test_synthetic_trace_passes_all_per_vu_gates(self):
        result = _evaluate(PASSING_RECORDS)

        self.assertTrue(result["passed"])
        self.assertEqual(set(result["stage_latency"]), {"50", "100", "200"})
        self.assertTrue(
            all(
                stage["inter_question_transition_count"] >= 1500
                for stage in result["stage_derived"].values()
            )
        )

    def test_minimum_samples_are_enforced_for_each_vu_and_metric(self):
        retained = False
        changed = []
        for record in PASSING_RECORDS:
            matches = (
                record["vus"] == 200
                and record["metric"] == "special_answer_feedback"
            )
            if matches and retained:
                continue
            if matches:
                retained = True
            changed.append(record)

        result = _evaluate(changed)

        self.assertFalse(result["passed"])
        self.assertTrue(
            any(
                "VU stage 200 special_answer_feedback: samples 1 < required 100" in failure
                for failure in result["failures"]
            )
        )

    def test_latency_threshold_uses_unrounded_value_per_vu(self):
        changed = list(PASSING_RECORDS)
        for index, record in enumerate(changed):
            if record["vus"] == 50 and record["metric"] == "special_answer_feedback":
                changed[index] = dict(record, duration_ms=800.0004)

        result = _evaluate(changed)

        self.assertFalse(result["passed"])
        self.assertEqual(
            result["stage_latency"]["50"]["special_answer_feedback"]["p95_ms"],
            800.0,
        )
        self.assertTrue(
            any(
                "VU stage 50 special_answer_feedback p95 800.000400ms > 800.000ms"
                in failure
                for failure in result["failures"]
            )
        )

    def test_duplicate_event_and_request_metric_cannot_inflate_samples(self):
        duplicate_event = list(PASSING_RECORDS) + [dict(PASSING_RECORDS[0])]
        event_result = _evaluate(duplicate_event)
        self.assertFalse(event_result["passed"])
        self.assertEqual(event_result["derived"]["duplicate_event_ids"], 1)

        duplicate_request = dict(PASSING_RECORDS[0], event_id="new-event-id")
        request_result = _evaluate(list(PASSING_RECORDS) + [duplicate_request])
        self.assertFalse(request_result["passed"])
        self.assertEqual(
            request_result["derived"]["duplicate_request_metric_records"], 1
        )

    def test_duplicate_transition_and_metric_hit_disagreement_are_rejected(self):
        first = _first_index(metric="special_prefetch_transition", vus=50)
        second = next(
            index
            for index in range(first + 1, len(PASSING_RECORDS))
            if PASSING_RECORDS[index]["metric"] == "special_prefetch_transition"
            and PASSING_RECORDS[index]["vus"] == 50
        )
        duplicate = _replace(
            PASSING_RECORDS,
            second,
            transition_id=PASSING_RECORDS[first]["transition_id"],
        )
        result = _evaluate(duplicate)
        self.assertFalse(result["passed"])
        self.assertEqual(result["derived"]["duplicate_transition_ids"], 1)

        inconsistent = _replace(PASSING_RECORDS, first, prefetch_hit=False)
        with self.assertRaisesRegex(gate.TraceError, "requires prefetch_hit=true"):
            _evaluate(inconsistent)

    def test_forced_online_probes_do_not_reduce_natural_prefetch_hit_rate(self):
        changed = list(PASSING_RECORDS)
        for index, record in enumerate(changed):
            if record["vus"] == 50 and record["metric"] == "special_online_transition":
                changed[index] = dict(record, sample_kind="forced_probe")

        result = _evaluate(
            changed,
            minimum_natural_special_transitions_per_vu=270,
        )

        self.assertTrue(result["passed"])
        self.assertEqual(
            result["stage_derived"]["50"]["natural_special_transition_count"], 270
        )
        self.assertEqual(
            result["stage_derived"]["50"]["special_prefetch_hit_rate"], 1.0
        )

    def test_tail_transition_sample_floor_is_enforced_per_vu(self):
        index = _first_index(metric="comprehensive_local_transition", vus=200)
        changed = list(PASSING_RECORDS)
        changed.pop(index)

        result = _evaluate(changed)

        self.assertFalse(result["passed"])
        self.assertTrue(
            any(
                "VU stage 200: inter-question transitions 1499 < required 1500"
                in failure
                for failure in result["failures"]
            )
        )

    def test_session_owner_scope_and_item_owner_are_immutable(self):
        first = _first_index(metric="special_answer_feedback", vus=50)
        second = first + 1
        cross_scope = _replace(
            PASSING_RECORDS,
            second,
            session_id=PASSING_RECORDS[first]["session_id"],
            anonymous_user_key=PASSING_RECORDS[first]["anonymous_user_key"] + "-other",
            expected_exam_code="Z002",
            actual_exam_code="Z002",
            expected_subject="数学基础",
            actual_subject="数学基础",
        )
        scope_result = _evaluate(cross_scope)
        self.assertFalse(scope_result["passed"])
        self.assertGreater(scope_result["derived"]["session_ownership_conflicts"], 0)

        reused_item = _replace(
            PASSING_RECORDS,
            second,
            item_id=PASSING_RECORDS[first]["item_id"],
        )
        item_result = _evaluate(reused_item)
        self.assertFalse(item_result["passed"])
        self.assertGreater(item_result["derived"]["item_ownership_conflicts"], 0)

    def test_manifest_must_be_complete_unique_immutable_and_match_event(self):
        sheet = _first_index(metric="comprehensive_sheet_ready", vus=50)
        sheet_record = dict(PASSING_RECORDS[sheet])
        duplicate_manifest = [dict(item) for item in sheet_record["manifest_items"]]
        duplicate_manifest[1]["question_id"] = duplicate_manifest[0]["question_id"]
        duplicate_records = _replace(
            PASSING_RECORDS,
            sheet,
            manifest_items=duplicate_manifest,
            authoritative_manifest_hash=_manifest_hash(duplicate_manifest),
        )
        duplicate_result = _evaluate(duplicate_records)
        self.assertFalse(duplicate_result["passed"])
        self.assertGreater(
            duplicate_result["derived"]["manifest_duplicate_questions"], 0
        )

        incomplete_records = _replace(
            PASSING_RECORDS,
            sheet,
            manifest_question_count=len(sheet_record["manifest_items"]) + 1,
        )
        incomplete_result = _evaluate(incomplete_records)
        self.assertFalse(incomplete_result["passed"])
        self.assertGreater(incomplete_result["derived"]["manifest_incomplete"], 0)

        local = _first_index(metric="comprehensive_local_transition", vus=50)
        mismatched_records = _replace(
            PASSING_RECORDS,
            local,
            item_id="not-in-manifest-item",
            question_id="not-in-manifest-question",
        )
        mismatch_result = _evaluate(mismatched_records)
        self.assertFalse(mismatch_result["passed"])
        self.assertGreater(
            mismatch_result["derived"]["manifest_event_mapping_mismatches"], 0
        )

    def test_manifest_is_required_on_every_successful_comprehensive_event(self):
        sheet = _first_index(metric="comprehensive_sheet_ready", vus=50)
        changed = list(PASSING_RECORDS)
        record = dict(changed[sheet])
        record.pop("manifest_items")
        record.pop("manifest_question_count")
        changed[sheet] = record

        with self.assertRaisesRegex(
            gate.TraceError, "manifest_question_count must be an integer"
        ):
            _evaluate(changed)

    def test_stable_window_and_independent_account_floor_are_enforced(self):
        changed_window = list(PASSING_RECORDS)
        exemplar = next(record for record in changed_window if record["vus"] == 50)
        start = datetime.fromisoformat(exemplar["stage_started_at"].replace("Z", "+00:00"))
        short_end = start + timedelta(seconds=60)
        occurred = start + timedelta(seconds=30)
        for index, record in enumerate(changed_window):
            if record["vus"] == 50:
                changed_window[index] = dict(
                    record,
                    stage_ended_at=gate._iso_z(short_end),
                    occurred_at=gate._iso_z(occurred),
                )
        window_result = _evaluate(changed_window)
        self.assertFalse(window_result["passed"])
        self.assertTrue(
            any(
                "steady window 60.000s < required 300.000s" in failure
                for failure in window_result["failures"]
            )
        )

        one_account = list(PASSING_RECORDS)
        for index, record in enumerate(one_account):
            if record["vus"] == 50:
                one_account[index] = dict(record, anonymous_user_key="only-user-at-50")
        account_result = _evaluate(one_account)
        self.assertFalse(account_result["passed"])
        self.assertTrue(
            any(
                "independent performance users 1 < required 50" in failure
                for failure in account_result["failures"]
            )
        )

    def test_single_run_and_candidate_identity_are_enforced(self):
        mixed_run = _replace(PASSING_RECORDS, 0, run_id="different-run")
        run_result = _evaluate(mixed_run)
        self.assertFalse(run_result["passed"])
        self.assertTrue(
            any("exactly one run_id" in failure for failure in run_result["failures"])
        )

        mixed_build = _replace(PASSING_RECORDS, 0, build_sha="different-build")
        build_result = _evaluate(mixed_build)
        self.assertFalse(build_result["passed"])
        self.assertTrue(
            any("mixes build_sha" in failure for failure in build_result["failures"])
        )

    def test_expected_conflict_is_a_successful_audit_outcome(self):
        expected_conflict = _valid_manifest_conflict(vus=50)

        result = _evaluate([*PASSING_RECORDS, expected_conflict])

        self.assertTrue(result["passed"])
        self.assertEqual(
            result["derived"]["conflict_scenario_counts"],
            {"comprehensive_manifest_conflict": 1},
        )

    def test_ok_status_and_expected_outcome_must_agree(self):
        index = _first_index(metric="special_answer_feedback", vus=50)
        dishonest_success = _replace(
            PASSING_RECORDS,
            index,
            status_code=500,
            error_code="SERVER_ERROR",
            ok=True,
        )
        with self.assertRaisesRegex(
            gate.TraceError, "successful events must have empty error_code"
        ):
            _evaluate(dishonest_success)

        failed = _replace(
            PASSING_RECORDS,
            index,
            status_code=500,
            error_code="SERVER_ERROR",
            ok=False,
        )
        failed_result = _evaluate(failed)
        self.assertFalse(failed_result["passed"])
        self.assertEqual(failed_result["derived"]["unexpected_errors"], 1)

    def test_audit_only_is_reserved_exclusively_for_expected_conflicts(self):
        laundering = _replace(PASSING_RECORDS, 0, sample_kind="audit_only")
        with self.assertRaisesRegex(gate.TraceError, "if and only if"):
            _evaluate(laundering)

        wrong_kind = _valid_manifest_conflict(vus=50)
        wrong_kind["sample_kind"] = "natural"
        with self.assertRaisesRegex(gate.TraceError, "if and only if"):
            _evaluate([*PASSING_RECORDS, wrong_kind])

    def test_network_and_local_success_status_semantics_are_metric_specific(self):
        network = _first_index(metric="special_answer_feedback", vus=50)
        with self.assertRaisesRegex(gate.TraceError, "metric/expected_outcome/status_code"):
            _evaluate(_replace(PASSING_RECORDS, network, status_code=0))

        local = _first_index(metric="comprehensive_local_transition", vus=50)
        with self.assertRaisesRegex(gate.TraceError, "metric/expected_outcome/status_code"):
            _evaluate(_replace(PASSING_RECORDS, local, status_code=200))

    def test_foreground_budget_flag_matches_duration_and_is_reported(self):
        index = _first_index(metric="special_prefetch_transition", vus=50)
        mismatch = _replace(
            PASSING_RECORDS,
            index,
            foreground_budget_exceeded=True,
        )
        with self.assertRaisesRegex(gate.TraceError, "duration_ms > 1200"):
            _evaluate(mismatch)

        exceeded = _replace(
            PASSING_RECORDS,
            index,
            duration_ms=1200.001,
            foreground_budget_exceeded=True,
        )
        result = _evaluate(exceeded)
        self.assertTrue(result["passed"])
        self.assertEqual(
            result["stage_derived"]["50"]["foreground_budget_exceeded_count"],
            1,
        )
        self.assertGreater(
            result["stage_derived"]["50"]["foreground_budget_exceeded_rate"],
            0,
        )

    def test_observed_vu_stages_must_exactly_match_required_set(self):
        extra = dict(
            PASSING_RECORDS[0],
            event_id="extra-vu-event",
            request_id="extra-vu-request",
            session_id="extra-vu-session",
            item_id="extra-vu-item",
            question_id="extra-vu-question",
            anonymous_user_key="extra-vu-user",
            vus=999,
            duration_ms=999999.0,
        )
        result = _evaluate([*PASSING_RECORDS, extra])
        self.assertFalse(result["passed"])
        self.assertTrue(
            any(
                "must exactly match required VU stages" in failure
                for failure in result["failures"]
            )
        )

    def test_observed_performance_span_rejects_collapsed_timeline_with_five_second_tolerance(self):
        collapsed = [
            (
                dict(record, occurred_at=record["stage_started_at"])
                if record["vus"] == 50
                else record
            )
            for record in PASSING_RECORDS
        ]
        collapsed_result = _evaluate(collapsed)
        self.assertFalse(collapsed_result["passed"])
        self.assertTrue(
            any(
                "VU stage 50: observed performance span 0.000s" in failure
                for failure in collapsed_result["failures"]
            )
        )

        exemplar = next(record for record in PASSING_RECORDS if record["vus"] == 50)
        start = datetime.fromisoformat(exemplar["stage_started_at"].replace("Z", "+00:00"))
        tolerated_end = gate._iso_z(start + timedelta(seconds=295))
        first_seen = False
        tolerated = []
        for record in PASSING_RECORDS:
            if record["vus"] != 50:
                tolerated.append(record)
                continue
            occurred_at = record["stage_started_at"] if not first_seen else tolerated_end
            first_seen = True
            tolerated.append(dict(record, occurred_at=occurred_at))
        tolerated_result = _evaluate(tolerated)
        self.assertTrue(tolerated_result["passed"])
        self.assertEqual(
            tolerated_result["stage_derived"]["50"]["observed_performance_span_seconds"],
            295.0,
        )

    def test_statistical_sample_floors_override_lower_cli_floor(self):
        result = _evaluate(PASSING_RECORDS, minimum_samples=1)
        self.assertTrue(result["passed"])
        self.assertEqual(
            result["stage_latency"]["50"]["special_answer_feedback"]["required_count"],
            100,
        )
        self.assertEqual(
            result["stage_latency"]["50"]["special_online_transition"]["required_count"],
            300,
        )

        removed_online = list(PASSING_RECORDS)
        removed_online.pop(_first_index(metric="special_online_transition", vus=50))
        online_result = _evaluate(removed_online, minimum_samples=1)
        self.assertFalse(online_result["passed"])
        self.assertTrue(
            any(
                "VU stage 50 special_online_transition: samples 299 < required 300"
                in failure
                for failure in online_result["failures"]
            )
        )

    def test_audit_accounts_do_not_inflate_independent_performance_users(self):
        one_user = [
            (
                dict(record, anonymous_user_key="only-performance-user")
                if record["vus"] == 50
                else record
            )
            for record in PASSING_RECORDS
        ]
        seed = dict(
            PASSING_RECORDS[_first_index(metric="special_online_transition", vus=50)]
        )
        for serial in range(49):
            conflict = dict(
                seed,
                event_id=f"audit-user-event-{serial}",
                request_id=f"audit-user-request-{serial}",
                transition_id=f"audit-user-transition-{serial}",
                session_id=f"audit-user-session-{serial}",
                anonymous_user_key=f"audit-only-user-{serial}",
                sample_kind="audit_only",
                expected_outcome="expected_conflict",
                status_code=409,
                error_code="ADAPTIVE_UPDATE_PENDING",
                conflict_scenario="special_update_pending",
                attempt_group_id=f"audit-user-group-{serial}",
                concurrency=2,
                expected_error_code="ADAPTIVE_UPDATE_PENDING",
            )
            for field in ("item_id", "question_id", "position"):
                conflict.pop(field)
            one_user.append(conflict)

        result = _evaluate(one_user)
        self.assertFalse(result["passed"])
        self.assertEqual(result["stage_derived"]["50"]["independent_users"], 1)
        self.assertEqual(
            result["derived"]["conflict_scenario_counts"]["special_update_pending"],
            49,
        )

    def test_manifest_is_emitted_once_and_local_mappings_are_checked_at_end(self):
        local_records = [
            record
            for record in PASSING_RECORDS
            if record["metric"] == "comprehensive_local_transition"
        ]
        self.assertTrue(local_records)
        self.assertTrue(all("manifest_items" not in record for record in local_records))

        sheets = [
            record
            for record in PASSING_RECORDS
            if record["metric"] == "comprehensive_sheet_ready"
        ]
        reordered = [
            record
            for record in PASSING_RECORDS
            if record["metric"] != "comprehensive_sheet_ready"
        ] + sheets
        self.assertTrue(_evaluate(reordered)["passed"])

        local_index = _first_index(metric="comprehensive_local_transition", vus=50)
        local = PASSING_RECORDS[local_index]
        sheet = next(
            record
            for record in sheets
            if record["session_id"] == local["session_id"]
        )
        repeated = _replace(
            PASSING_RECORDS,
            local_index,
            manifest_question_count=sheet["manifest_question_count"],
            manifest_items=[dict(item) for item in sheet["manifest_items"]],
            authoritative_manifest_hash=sheet["authoritative_manifest_hash"],
        )
        self.assertTrue(_evaluate(repeated)["passed"])

        changed_items = [dict(item) for item in sheet["manifest_items"]]
        changed_items[0]["question_id"] = "changed-repeated-manifest-question"
        conflicting_repeat = _replace(
            PASSING_RECORDS,
            local_index,
            manifest_question_count=len(changed_items),
            manifest_items=changed_items,
            authoritative_manifest_hash=_manifest_hash(changed_items),
        )
        conflicting_result = _evaluate(conflicting_repeat)
        self.assertFalse(conflicting_result["passed"])
        self.assertGreater(conflicting_result["derived"]["manifest_conflicts"], 0)

    def test_manifest_conflict_uses_attempted_and_authoritative_hashes(self):
        conflict = _valid_manifest_conflict(vus=50)
        self.assertTrue(_evaluate([*PASSING_RECORDS, conflict])["passed"])

        same_hash = dict(
            conflict,
            event_id="same-hash-conflict-event",
            request_id="same-hash-conflict-request",
            attempted_manifest_hash=conflict["authoritative_manifest_hash"],
        )
        with self.assertRaisesRegex(gate.TraceError, "must differ"):
            _evaluate([*PASSING_RECORDS, same_hash])

        wrong_code = dict(
            conflict,
            event_id="wrong-code-conflict-event",
            request_id="wrong-code-conflict-request",
            error_code="UNRELATED_CONFLICT",
        )
        with self.assertRaisesRegex(gate.TraceError, "metric/expected_outcome/status_code"):
            _evaluate([*PASSING_RECORDS, wrong_code])

        wrong_authority = dict(
            conflict,
            event_id="wrong-authority-conflict-event",
            request_id="wrong-authority-conflict-request",
            authoritative_manifest_hash="b" * 64,
        )
        wrong_authority_result = _evaluate([*PASSING_RECORDS, wrong_authority])
        self.assertFalse(wrong_authority_result["passed"])
        self.assertEqual(
            wrong_authority_result["derived"]["manifest_conflict_hash_mismatches"],
            1,
        )

    def test_jsonl_loader_is_lazy_and_reports_late_parse_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.jsonl"
            path.write_text(
                json.dumps(PASSING_RECORDS[0], ensure_ascii=False) + "\n{broken-json\n",
                encoding="utf-8",
            )
            records = iter(gate._load_records(path))
            self.assertEqual(next(records)["event_id"], PASSING_RECORDS[0]["event_id"])
            with self.assertRaisesRegex(gate.TraceError, "invalid JSON on line 2"):
                next(records)

    def test_fractional_integer_fields_are_rejected(self):
        cases = [
            ("special_answer_feedback", "vus", 50.9),
            ("special_answer_feedback", "position", 1.9),
            ("comprehensive_local_transition", "comprehensive_next_calls", 0.9),
        ]
        for metric, field, value in cases:
            with self.subTest(field=field):
                index = _first_index(metric=metric, vus=50)
                changed = _replace(PASSING_RECORDS, index, **{field: value})
                with self.assertRaisesRegex(
                    gate.TraceError, f"{field} must be an integer"
                ):
                    _evaluate(changed)

    def test_required_vus_cannot_be_empty_and_cli_returns_usage_error(self):
        with self.assertRaisesRegex(gate.TraceError, "at least one VU stage"):
            _evaluate(PASSING_RECORDS, required_vus=set())

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            exit_code = gate.main(["--self-test", "--require-vus", ""])
        self.assertEqual(exit_code, 2)
        self.assertIn("at least one positive integer", stderr.getvalue())

    def test_fixed_schema_fields_and_numeric_types_are_required(self):
        missing_run = list(PASSING_RECORDS)
        record = dict(missing_run[0])
        record.pop("run_id")
        missing_run[0] = record
        with self.assertRaisesRegex(gate.TraceError, "run_id must be a string"):
            _evaluate(missing_run)

        duration_as_text = _replace(PASSING_RECORDS, 0, duration_ms="320")
        with self.assertRaisesRegex(gate.TraceError, "duration_ms must be a number"):
            _evaluate(duration_as_text)

    def test_self_test_exercises_positive_and_negative_paths(self):
        result = gate._run_self_test(
            required_vus=REQUIRED_VUS,
            minimum_samples=30,
            minimum_transitions_per_vu=1500,
            minimum_natural_special_transitions_per_vu=300,
            minimum_stable_seconds=300.0,
        )

        self.assertTrue(result["passed"])
        self.assertTrue(result["cases"]["valid_trace_passes"])
        self.assertTrue(all(result["cases"].values()))


if __name__ == "__main__":
    unittest.main()
