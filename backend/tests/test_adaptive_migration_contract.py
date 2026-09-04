from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = PROJECT_ROOT / "database" / "adaptive_question_delivery_v1.sql"


class AdaptiveMigrationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = MIGRATION_PATH.read_text(encoding="utf-8").lower()

    @classmethod
    def function_sql(cls, name: str) -> str:
        """Return one function definition without depending on file-wide order."""

        markers = (
            f"create or replace function public.{name}(",
            f"create function public.{name}(",
        )
        starts = [cls.sql.find(marker) for marker in markers]
        start = min(position for position in starts if position >= 0)
        body_start = cls.sql.index("as $$", start)
        end = cls.sql.index("\n$$;", body_start) + len("\n$$;")
        return cls.sql[start:end]

    @staticmethod
    def compact(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    def test_wrong_question_rebuild_is_gated_by_the_active_wrong_book_snapshot(self):
        snapshot = "create temporary table adaptive_active_wrong_questions_snapshot"
        delete = "delete from public.wrong_questions"
        insert = "insert into public.wrong_questions"

        self.assertIn(snapshot, self.sql)
        self.assertLess(self.sql.index(snapshot), self.sql.index(delete))

        rebuild = self.sql[self.sql.index(insert) : self.sql.index("drop index if exists", self.sql.index(insert))]
        self.assertIn("join adaptive_active_wrong_questions_snapshot snapshot", rebuild)
        self.assertIn("snapshot.stats_exam_code is null", rebuild)
        self.assertIn("snapshot.stats_exam_code = answers.stats_exam_code", rebuild)

    def test_removed_mastered_question_has_no_history_only_reinsertion_path(self):
        insert = self.sql.index("insert into public.wrong_questions")
        rebuild = self.sql[insert : self.sql.index("drop index if exists", insert)]

        # An inner join to the pre-migration active set means a question absent
        # from that set stays absent even when old incorrect answers still exist.
        self.assertIn("join adaptive_active_wrong_questions_snapshot snapshot", rebuild)
        self.assertNotIn("left join adaptive_active_wrong_questions_snapshot", rebuild)

    def test_next_item_claim_is_privileged_and_atomic(self):
        claim = self.function_sql("claim_next_adaptive_practice_item")
        compact_claim = self.compact(claim)

        self.assertIn("security definer", claim)
        self.assertIn("set search_path = public, pg_temp", claim)
        self.assertIn("perform pg_advisory_xact_lock(", claim)
        self.assertIn(
            "p_user_id::text || ':' || session_snapshot.stats_exam_code || ':' || session_snapshot.subject",
            claim,
        )
        self.assertIn(
            "from public.practice_sessions where id = p_session_id and user_id = p_user_id for update",
            compact_claim,
        )
        self.assertIn(
            "from public.user_subject_state where user_id = p_user_id and stats_exam_code = session_row.stats_exam_code "
            "and subject = session_row.subject for update",
            compact_claim,
        )
        self.assertIn("insert into public.practice_session_items", claim)
        self.assertIn("returning * into item_row", claim)

        compact_sql = self.compact(self.sql)
        signature = (
            "public.claim_next_adaptive_practice_item( "
            "uuid, uuid, uuid, integer, bigint, jsonb, timestamptz )"
        )
        self.assertIn(
            f"revoke all on function {signature} from public, anon, authenticated;",
            compact_sql,
        )
        self.assertIn(
            f"grant execute on function {signature} to service_role;",
            compact_sql,
        )

    def test_claim_pending_barrier_is_scope_wide_and_audit_authoritative(self):
        claim = self.function_sql("claim_next_adaptive_practice_item")
        pending_start = claim.index("from public.practice_sessions pending_session")
        pending_end = claim.index("raise exception 'adaptive_update_pending'", pending_start)
        pending = claim[pending_start:pending_end]

        self.assertIn("pending_session.user_id = p_user_id", pending)
        self.assertIn(
            "pending_session.stats_exam_code = session_row.stats_exam_code",
            pending,
        )
        self.assertIn("pending_session.subject = session_row.subject", pending)
        self.assertIn("pending_item.answer_id is not null", pending)
        self.assertIn("not exists (", pending)
        self.assertIn("from public.adaptive_model_updates applied_update", pending)
        self.assertIn("applied_update.answer_id = pending_item.answer_id", pending)
        self.assertNotIn("pending_session.id = p_session_id", pending)
        self.assertNotIn("adaptive_model_updated_at", pending)

    def test_pending_update_reader_uses_audit_rows_not_the_fast_marker(self):
        pending = self.function_sql("get_pending_adaptive_update_items")

        self.assertIn("item.answer_id is not null", pending)
        self.assertIn("public.adaptive_model_updates", pending)
        self.assertNotIn("adaptive_model_updated_at", pending)
        self.assertTrue(
            (
                "not exists (" in pending
                and "model_update.answer_id = item.answer_id" in pending
            )
            or (
                "left join public.adaptive_model_updates model_update" in pending
                and "model_update.answer_id is null" in pending
            ),
            "pending updates must anti-join the answer-id audit fact",
        )

    def test_claim_time_question_snapshots_are_private_and_owner_resolved(self):
        compact_sql = self.compact(self.sql)
        snapshot_table = "public.practice_session_item_question_snapshots"

        self.assertIn(f"create table if not exists {snapshot_table}", self.sql)
        self.assertIn(
            f"alter table {snapshot_table} enable row level security",
            compact_sql,
        )
        self.assertIn(
            f"revoke all on table {snapshot_table} from public, anon, authenticated",
            compact_sql,
        )
        self.assertNotIn(
            f"grant select on table {snapshot_table} to authenticated",
            compact_sql,
        )

        getter = self.function_sql("get_adaptive_question_snapshot")
        self.assertIn("security definer", getter)
        self.assertIn(":adaptive_comprehensive_embargo", getter)
        self.assertIn("session.user_id = p_user_id", getter)
        self.assertIn("snapshot.question_id = p_question_id", getter)
        self.assertIn("session_mode = 'comprehensive'", getter)
        self.assertIn("session_status = 'active'", getter)
        self.assertIn("adaptive_comprehensive_batch_required", getter)
        self.assertIn(
            "grant execute on function public.get_adaptive_question_snapshot(uuid, uuid, uuid) to service_role",
            compact_sql,
        )

    def test_answer_rpc_requires_exact_comprehensive_manifest_capability(self):
        record_answer = self.function_sql("record_answer_submission")
        compact_sql = self.compact(self.sql)

        self.assertIn("p_submission_kind text default 'single'", record_answer)
        self.assertIn("p_comprehensive_session_id uuid default null", record_answer)
        self.assertIn("p_comprehensive_client_submission_id text default null", record_answer)
        self.assertIn("p_comprehensive_manifest_hash text default null", record_answer)
        self.assertIn(":adaptive_comprehensive_embargo", record_answer)
        self.assertIn("p_practice_session_item_id is null", record_answer)
        self.assertIn("embargoed_session.mode = 'comprehensive'", record_answer)
        self.assertIn("embargoed_session.status = 'active'", record_answer)
        self.assertIn("embargoed_item.question_id = p_question_id", record_answer)
        self.assertIn("p_used_time not between 0 and 86400", record_answer)
        self.assertIn("adaptive_comprehensive_batch_required", record_answer)
        self.assertIn("comprehensive_manifest->'answers'", record_answer)
        self.assertIn("p_comprehensive_session_id is distinct from practice_session_row.id", record_answer)
        self.assertIn("comprehensive_answer_entry->>'selected_answer' <> p_selected_answer", record_answer)
        self.assertIn("(comprehensive_answer_entry->>'used_time')::integer <> p_used_time", record_answer)
        self.assertIn("comprehensive_answer_entry->>'client_submission_id' <> normalized_client_id", record_answer)
        signature = (
            "public.record_answer_submission( uuid, uuid, text, text, boolean, integer, "
            "text, text, text, text, boolean, timestamptz, uuid, text, uuid, text, text )"
        )
        self.assertIn(f"revoke all on function {signature} from public, anon, authenticated;", compact_sql)
        self.assertIn(f"grant execute on function {signature} to service_role;", compact_sql)

    def test_comprehensive_event_and_completion_paths_share_lock_order_and_guards(self):
        event = self.function_sql("record_practice_session_item_event")
        complete = self.function_sql("complete_practice_session")

        for function in (event, complete):
            self.assertIn(":adaptive_comprehensive_embargo", function)
            self.assertLess(
                function.index(":adaptive_comprehensive_embargo"),
                function.index("for update"),
            )
        self.assertIn("p_event_type = 'skipped'", event)
        self.assertIn("adaptive_comprehensive_batch_required", event)
        self.assertIn("p_event_type = 'abandoned'", event)
        self.assertIn("adaptive_comprehensive_submission_in_progress", event)
        self.assertIn("adaptive_comprehensive_finalize_required", complete)
        self.assertIn("adaptive_comprehensive_submission_in_progress", complete)
        self.assertIn("session_row.status = 'completed'", complete)
        self.assertIn("comprehensive_manifest->>'phase'", complete)

    def test_scope_wide_pending_updates_have_a_total_stable_order(self):
        pending = self.function_sql("get_pending_adaptive_update_items")
        self.assertIn(
            "order by answer.created_at asc, session.created_at asc, item.position asc, item.id asc",
            pending,
        )

    def test_answer_grade_recovery_and_model_update_use_claim_snapshot(self):
        record_answer = self.function_sql("record_answer_submission")
        pending = self.function_sql("get_pending_adaptive_update_items")
        apply_update = self.function_sql("apply_adaptive_model_update")

        self.assertIn(
            "if p_practice_session_item_id is null then",
            record_answer,
        )
        self.assertIn(
            "from public.practice_session_item_question_snapshots snapshot",
            record_answer,
        )
        self.assertIn(
            "resolved_is_correct := p_selected_answer = question_row.answer",
            record_answer,
        )
        self.assertIn(
            "join public.practice_session_item_question_snapshots snapshot",
            pending,
        )
        self.assertNotIn("join public.questions question", pending)
        self.assertIn(
            "from public.practice_session_item_question_snapshots snapshot",
            apply_update,
        )
        self.assertIn(
            "join public.practice_session_item_question_snapshots low_snapshot",
            apply_update,
        )
        self.assertIn(
            "join public.practice_session_item_question_snapshots high_snapshot",
            apply_update,
        )

    def test_claim_and_apply_both_validate_the_d2_then_d3_verification_slot(self):
        claim = self.function_sql("claim_next_adaptive_practice_item")
        apply_update = self.function_sql("apply_adaptive_model_update")

        for function_sql in (claim, apply_update):
            self.assertIn("verification_conflict_id", function_sql)
            self.assertIn("verification_expected_count", function_sql)
            self.assertIn("verification_expected_difficulty", function_sql)
            self.assertIn("mod(", function_sql)
            self.assertRegex(
                function_sql,
                r"mod\([^)]*verification_count[^)]*,\s*2\)\s*=\s*0\s+then\s+2\s+else\s+3",
            )
            self.assertIn("question_row.difficulty", function_sql)
            self.assertIn("question_row.module", function_sql)
            self.assertIn("question_row.submodule", function_sql)
            self.assertIn("question_row.question_type", function_sql)
            self.assertIn("low_question_id", function_sql)
            self.assertIn("high_question_id", function_sql)

    def test_verification_count_advances_only_after_reliable_evidence_checks(self):
        apply_update = self.function_sql("apply_adaptive_model_update")
        evidence_gate = apply_update.index("if not answer_row.is_first_attempt")
        increment = apply_update.index(
            "verification_count = least(20, verification_count + 1)",
            evidence_gate,
        )

        self.assertLess(evidence_gate, increment)
        self.assertIn("evidence_weight < 0.7", apply_update[evidence_gate:increment])
        self.assertIn("question_valid", apply_update[evidence_gate:increment])
        self.assertIn(
            "adaptive_conflict_verification_evidence_invalid",
            apply_update[evidence_gate:increment],
        )

    def test_subject_conflict_counter_is_recounted_and_saved_in_the_same_rpc(self):
        apply_update = self.function_sql("apply_adaptive_model_update")
        compact_apply = self.compact(apply_update)

        self.assertIn(
            "select count(*)::integer into pending_subject_conflicts from public.adaptive_conflicts",
            compact_apply,
        )
        self.assertIn("status = 'pending'", compact_apply)
        self.assertIn(
            "next_subject_conflicts := pending_subject_conflicts",
            compact_apply,
        )
        self.assertIn(
            "pending_conflict_count = next_subject_conflicts",
            compact_apply,
        )
        self.assertLess(
            compact_apply.index(
                "select count(*)::integer into pending_subject_conflicts"
            ),
            compact_apply.index("update public.user_subject_state"),
        )

    def test_verification_lease_releases_only_stale_unanswered_reservations(self):
        claim = self.function_sql("claim_next_adaptive_practice_item")
        lease_start = claim.index("update public.practice_session_items expired_item")
        lease_end = claim.index("-- a concurrent retry may have won", lease_start)
        lease = claim[lease_start:lease_end]

        self.assertIn("expired_item.target_zone = 'verify'", lease)
        self.assertIn("expired_item.item_status in ('selected', 'presented')", lease)
        self.assertIn("expired_item.answer_id is null", lease)
        self.assertIn("interval '15 minutes'", lease)
        self.assertIn("'verification_slot_expired', true", lease)
        self.assertNotIn("delete from", lease)
        self.assertNotIn("item_status = 'skipped'", lease)
        self.assertNotIn("answer_id = null", lease)

        reservation_check = claim[
            claim.index("from public.practice_sessions claimed_session") :
            claim.index("raise exception 'adaptive_conflict_verification_slot_claimed'")
        ]
        self.assertIn("verification_slot_expired", reservation_check)

    def test_answer_binding_freezes_lease_expiry_at_the_answer_timestamp(self):
        record_answer = self.function_sql("record_answer_submission")
        compact_record = self.compact(record_answer)

        self.assertIn(
            "existing_answer.created_at - interval '15 minutes'",
            record_answer,
        )
        self.assertIn("p_now - interval '15 minutes'", record_answer)
        self.assertGreaterEqual(
            record_answer.count("'verification_slot_expired', true"),
            2,
        )
        self.assertGreaterEqual(
            record_answer.count("returning * into practice_item_row"),
            2,
        )
        self.assertIn(
            "practice_session_row.status <> 'active' and not ( "
            "practice_item_row.strategy_metadata @> "
            "'{\"verification_slot_expired\": true}'::jsonb )",
            compact_record,
        )

    def test_expired_verification_answer_remains_ordinary_model_evidence(self):
        apply_update = self.function_sql("apply_adaptive_model_update")
        expired_branch = (
            "if conflict_action in ('open', 'verify', 'resolve', 'defer') "
            "and item_row.strategy_metadata @> "
            "'{\"verification_slot_expired\": true}'::jsonb then"
        )

        self.assertIn(self.compact(expired_branch), self.compact(apply_update))
        branch_start = self.compact(apply_update).index(self.compact(expired_branch))
        ordinary_tail = self.compact(apply_update)[branch_start:]
        self.assertIn("effective_conflict_action := 'none'", ordinary_tail)
        self.assertIn("update public.user_subject_state", ordinary_tail)
        self.assertIn("insert into public.adaptive_model_updates", ordinary_tail)

    def test_audit_trigger_keeps_marker_repairable_in_both_directions(self):
        sync_marker = self.function_sql("sync_adaptive_model_update_marker")
        compact_sql = self.compact(self.sql)

        self.assertIn("if tg_op in ('delete', 'update')", sync_marker)
        self.assertIn("if tg_op in ('insert', 'update')", sync_marker)
        self.assertIn("not exists (", sync_marker)
        self.assertIn("from public.adaptive_model_updates remaining_update", sync_marker)
        self.assertIn("remaining_update.answer_id = item.answer_id", sync_marker)
        self.assertIn(
            "create trigger sync_adaptive_model_update_marker after insert or update or delete "
            "on public.adaptive_model_updates",
            compact_sql,
        )

        marker_reconciliation = self.sql[
            self.sql.index("update public.practice_session_items item\nset adaptive_model_updated_at = null") :
            self.sql.index("create or replace function public.sync_adaptive_model_update_marker")
        ]
        self.assertIn("not exists (", marker_reconciliation)
        self.assertIn("model_update.answer_id = item.answer_id", marker_reconciliation)

if __name__ == "__main__":
    unittest.main()
