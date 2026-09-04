from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = PROJECT_ROOT / "database" / "adaptive_comprehensive_practice_v1.sql"
BATCH_MIGRATION_PATH = (
    PROJECT_ROOT / "database" / "adaptive_comprehensive_submission_batch_v1.sql"
)


class AdaptiveComprehensiveMigrationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = MIGRATION_PATH.read_text(encoding="utf-8").lower()
        cls.batch_sql = BATCH_MIGRATION_PATH.read_text(encoding="utf-8").lower()

    @classmethod
    def function_sql(cls, name: str) -> str:
        markers = (
            f"create or replace function public.{name}(",
            f"create function public.{name}(",
        )
        starts = [cls.sql.find(marker) for marker in markers]
        start = min(position for position in starts if position >= 0)
        body_start = cls.sql.index("as $$", start)
        end = cls.sql.index("\n$$;", body_start) + len("\n$$;")
        return cls.sql[start:end]

    @classmethod
    def dynamic_function_sql(cls, name: str, dollar_tag: str) -> str:
        start = cls.sql.index(f"create function public.{name}(")
        body_start = cls.sql.index(dollar_tag, start)
        end = cls.sql.index(dollar_tag, body_start + len(dollar_tag))
        return cls.sql[start : end + len(dollar_tag)]

    @staticmethod
    def compact(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    def test_full_round_claim_is_one_privileged_transactional_function(self):
        claim = self.function_sql("claim_adaptive_comprehensive_practice_items")
        compact = self.compact(claim)

        self.assertIn("security definer", claim)
        self.assertIn("perform pg_advisory_xact_lock", claim)
        self.assertIn(":adaptive_comprehensive_embargo", claim)
        self.assertIn("session_row.mode <> 'comprehensive'", claim)
        self.assertIn(
            "jsonb_array_length(p_items) <> session_row.requested_question_count",
            claim,
        )
        self.assertIn("insert into public.practice_session_items", claim)
        self.assertIn(
            "insert into public.practice_session_item_question_snapshots",
            claim,
        )
        self.assertIn("to_jsonb(question_row)", claim)
        self.assertIn("order by item.position", claim)
        self.assertIn("adaptive_update_pending", claim)
        self.assertIn(
            "grant execute on function public.claim_adaptive_comprehensive_practice_items( "
            "uuid, uuid, bigint, jsonb, timestamptz ) to service_role",
            self.compact(self.sql),
        )
        self.assertNotIn("grant execute", compact)

    def test_concurrent_claim_replays_only_a_complete_snapshotted_round(self):
        claim = self.function_sql("claim_adaptive_comprehensive_practice_items")
        replay_start = claim.index("if existing_count > 0 then")
        replay_end = claim.index("if jsonb_array_length", replay_start)
        replay = claim[replay_start:replay_end]

        self.assertIn("existing_count <> session_row.requested_question_count", replay)
        self.assertIn("existing_snapshot_count <> existing_count", replay)
        self.assertIn("question_snapshot", replay)
        self.assertIn("return result_items", replay)

    def test_comprehensive_claim_database_enforces_the_d1_to_d4_ceiling(self):
        claim = self.function_sql("claim_adaptive_comprehensive_practice_items")
        question_lookup = claim.index("select * into question_row")
        difficulty_guard = claim.index(
            "question_row.difficulty not between 1 and 4",
            question_lookup,
        )
        insert_item = claim.index(
            "insert into public.practice_session_items",
            question_lookup,
        )

        self.assertIn(
            "question_row.difficulty is null",
            claim[question_lookup:difficulty_guard],
        )
        self.assertLess(difficulty_guard, insert_item)
        self.assertIn(
            "raise exception 'adaptive_comprehensive_difficulty_out_of_range'",
            claim[difficulty_guard:insert_item],
        )

    def test_submission_manifest_is_locked_with_scope_consistent_lock_order(self):
        begin = self.function_sql("begin_adaptive_comprehensive_submission")
        compact = self.compact(begin)

        self.assertIn("p_answers jsonb", begin)
        self.assertGreaterEqual(begin.count("perform pg_advisory_xact_lock"), 2)
        self.assertIn(":adaptive_comprehensive_embargo", begin)
        self.assertLess(
            begin.index("perform pg_advisory_xact_lock"),
            begin.index("for update", begin.index("select * into session_row")),
        )
        self.assertIn("comprehensive_submission", begin)
        self.assertIn("manifest_hash", begin)
        self.assertIn("canonical_answers", begin)
        self.assertIn("'answers', canonical_answers", begin)
        self.assertIn("'phase', 'locked'", begin)
        self.assertIn("jsonb_array_length(p_answers)", begin)
        self.assertIn("generate_series(1, session_row.requested_question_count)", begin)
        self.assertIn("entry_used_time not between 0 and 86400", begin)
        self.assertIn("entry_client_submission_id = any(seen_submission_ids)", begin)
        self.assertIn("item_row.position <> entry_position", begin)
        self.assertIn("adaptive_comprehensive_submission_conflict", begin)
        self.assertIn("idempotent', true", begin)
        self.assertIn("existing_manifest->'completion_state'", begin)
        self.assertIn(
            "grant execute on function public.begin_adaptive_comprehensive_submission( "
            "uuid, uuid, text, text, jsonb, timestamptz ) to service_role",
            self.compact(self.sql),
        )
        self.assertIn("session_row.mode <> 'comprehensive'", compact)

    def test_single_feedback_assertion_blocks_item_and_question_only_bypasses(self):
        assertion = self.function_sql("assert_single_answer_feedback_allowed")
        compact = self.compact(assertion)

        self.assertIn(":adaptive_comprehensive_embargo", assertion)
        self.assertIn("p_practice_session_item_id is not null", assertion)
        self.assertIn("session.user_id = p_user_id", assertion)
        self.assertIn("item_question_id <> p_question_id", assertion)
        self.assertIn("session.mode = 'comprehensive'", assertion)
        self.assertIn("session.status = 'active'", assertion)
        self.assertIn("item.question_id = p_question_id", assertion)
        self.assertGreaterEqual(
            assertion.count("adaptive_comprehensive_batch_required"),
            2,
        )
        self.assertIn(
            "grant execute on function public.assert_single_answer_feedback_allowed( "
            "uuid, uuid, uuid ) to service_role",
            self.compact(self.sql),
        )
        self.assertNotIn("grant execute", compact)

    def test_incremental_upgrade_wraps_the_legacy_answer_rpc_without_an_exposed_overload(self):
        compact = self.compact(self.sql)
        wrapper = self.dynamic_function_sql(
            "record_answer_submission",
            "$answer_wrapper$",
        )
        new_signature = (
            "public.record_answer_submission(uuid,uuid,text,text,boolean,integer,"
            "text,text,text,text,boolean,timestamptz,uuid,text,uuid,text,text)"
        )
        old_signature = (
            "public.record_answer_submission(uuid,uuid,text,text,boolean,integer,"
            "text,text,text,text,boolean,timestamptz,uuid)"
        )
        private_signature = (
            "public.record_answer_submission_pre_comprehensive_v1(uuid,uuid,text,text,"
            "boolean,integer,text,text,text,text,boolean,timestamptz,uuid)"
        )

        self.assertIn("do $answer_rpc_upgrade$", self.sql)
        self.assertIn(f"to_regprocedure( '{new_signature}' ) is null", compact)
        self.assertIn(f"to_regprocedure( '{old_signature}' ) is null", compact)
        self.assertIn(f"to_regprocedure( '{private_signature}' ) is null", compact)
        self.assertIn(
            "rename to record_answer_submission_pre_comprehensive_v1",
            compact,
        )
        self.assertIn(
            "from public, anon, authenticated, service_role",
            compact,
        )
        self.assertIn("execute $create_answer_wrapper$", self.sql)
        self.assertIn("p_submission_kind text default 'single'", wrapper)
        self.assertIn("p_comprehensive_session_id uuid default null", wrapper)
        self.assertIn("p_comprehensive_client_submission_id text default null", wrapper)
        self.assertIn("p_comprehensive_manifest_hash text default null", wrapper)
        self.assertIn("p_used_time not between 0 and 86400", wrapper)
        self.assertIn(":adaptive_comprehensive_embargo", wrapper)
        self.assertIn("p_practice_session_item_id is null", wrapper)
        self.assertIn("embargoed_session.mode = 'comprehensive'", wrapper)
        self.assertIn("embargoed_session.status = 'active'", wrapper)
        self.assertIn("embargoed_item.question_id = p_question_id", wrapper)
        self.assertIn("manifest->'answers'", wrapper)
        self.assertIn("p_comprehensive_session_id is distinct from session_row.id", wrapper)
        self.assertIn("answer_entry->>'selected_answer' <> p_selected_answer", wrapper)
        self.assertIn("(answer_entry->>'used_time')::integer <> p_used_time", wrapper)
        self.assertIn("answer_entry->>'client_submission_id' <> normalized_client_id", wrapper)
        self.assertIn(
            "return public.record_answer_submission_pre_comprehensive_v1(",
            wrapper,
        )
        self.assertIn(f"if to_regprocedure( '{old_signature}' ) is not null", compact)
        self.assertIn("execute 'drop function public.record_answer_submission(", self.sql)
        self.assertEqual(
            self.sql.count("create function public.record_answer_submission("),
            1,
            "the incremental migration must expose only the extended RPC shape",
        )
        self.assertNotIn(
            "grant execute on function public.record_answer_submission_pre_comprehensive_v1",
            compact,
        )
        self.assertIn(
            "revoke all on function public.record_answer_submission( uuid, uuid, text, text, "
            "boolean, integer, text, text, text, text, boolean, timestamptz, uuid, text, uuid, "
            "text, text ) from public, anon, authenticated;",
            compact,
        )
        self.assertIn(
            "grant execute on function public.record_answer_submission( uuid, uuid, text, text, "
            "boolean, integer, text, text, text, text, boolean, timestamptz, uuid, text, uuid, "
            "text, text ) to service_role;",
            compact,
        )

    def test_incremental_migration_replaces_every_comprehensive_sensitive_base_rpc(self):
        compact_sql = self.compact(self.sql)
        expected_signatures = (
            "public.get_adaptive_question_snapshot(uuid, uuid, uuid)",
            "public.record_practice_session_item_event(uuid, uuid, uuid, text, timestamptz)",
            "public.complete_practice_session(uuid, uuid, text, timestamptz)",
            "public.get_pending_adaptive_update_items(uuid, text, text, uuid, integer)",
        )

        for name in (
            "get_adaptive_question_snapshot",
            "record_practice_session_item_event",
            "complete_practice_session",
            "get_pending_adaptive_update_items",
        ):
            self.assertIn(f"create or replace function public.{name}(", self.sql)
            function = self.function_sql(name)
            self.assertIn("security definer", function)
            self.assertIn("set search_path = public, pg_temp", function)

        getter = self.function_sql("get_adaptive_question_snapshot")
        event = self.function_sql("record_practice_session_item_event")
        complete = self.function_sql("complete_practice_session")
        pending = self.function_sql("get_pending_adaptive_update_items")
        self.assertIn(":adaptive_comprehensive_embargo", getter)
        self.assertIn("adaptive_comprehensive_batch_required", getter)
        self.assertIn(":adaptive_comprehensive_embargo", event)
        self.assertIn("adaptive_comprehensive_submission_in_progress", event)
        self.assertIn(":adaptive_comprehensive_embargo", complete)
        self.assertIn("adaptive_comprehensive_finalize_required", complete)
        self.assertIn(
            "order by answer.created_at asc, session.created_at asc, item.position asc, item.id asc",
            pending,
        )

        for signature in expected_signatures:
            self.assertIn(
                f"revoke all on function {signature} from public, anon, authenticated;",
                compact_sql,
            )
            self.assertIn(
                f"grant execute on function {signature} to service_role;",
                compact_sql,
            )

        self.assertNotIn("adaptive_active_wrong_questions_snapshot", self.sql)
        self.assertNotIn("delete from public.wrong_questions", self.sql)
        self.assertNotIn("lock table public.user_answers", self.sql)
        self.assertIn("notify pgrst, 'reload schema'", self.sql)

    def test_migration_has_transactional_reviewed_predecessor_gate(self):
        compact_sql = self.compact(self.sql)
        gate = self.sql[
            self.sql.index("do $predecessor_gate$") :
            self.sql.index("$predecessor_gate$;")
        ]

        self.assertLess(self.sql.index("begin;"), self.sql.index("do $predecessor_gate$"))
        self.assertLess(
            self.sql.index("$predecessor_gate$;"),
            self.sql.index("create or replace function public.claim_adaptive_comprehensive_practice_items"),
        )
        self.assertIn("where status = 'active'", gate)
        self.assertIn("adaptive_comprehensive_active_session_present", gate)
        self.assertIn("adaptive_comprehensive_answer_rpc_transition_invalid", gate)
        self.assertIn("adaptive_comprehensive_partial_or_prior_migration_present", gate)
        self.assertIn("adaptive_comprehensive_predecessor_drift", gate)
        self.assertIn("actual_acl <> '{postgres=x/postgres,service_role=x/postgres}'", gate)
        self.assertIn("actual_owner <> 'postgres'", gate)
        self.assertIn("search_path=public, pg_temp", gate)

        expected_reviewed_hashes = (
            "a49e0d6863b722198224766e2295f1da",
            "9dcb9ac1196ce9af928bf439a1f2b005",
            "d2e2be3a78f1a5b9522c639be8729de7",
            "7255f4d5a37a55bd49ec09c78c66f6ad",
            "73bfd2b45fa01b4535aa703222d5a676",
            "42b4400fa3fdc080055d11849807976b",
            "b1557754912e57cddcdad7c7062d9df7",
            "c945ae789dd4ad8074902b857dd356b0",
            "3f09faf68c2a5ecd1c0fa6ce541c9334",
            "a4f121c8006d6b4b4046c85f242834c4",
            "d377f77e8a3cf4fc85c6b4e49b52fcc9",
            "6fd9e1cfe1d526a36a64b52e014c4dd1",
        )
        for expected_hash in expected_reviewed_hashes:
            self.assertIn(expected_hash, gate)

        for signature in (
            "public.claim_adaptive_comprehensive_practice_items(uuid,uuid,bigint,jsonb,timestamptz)",
            "public.assert_single_answer_feedback_allowed(uuid,uuid,uuid)",
            "public.begin_adaptive_comprehensive_submission(uuid,uuid,text,text,jsonb,timestamptz)",
            "public.record_adaptive_comprehensive_skip(uuid,uuid,uuid,text,text,timestamptz)",
            "public.finalize_adaptive_comprehensive_submission(uuid,uuid,text,text,timestamptz)",
            "public.get_adaptive_candidate_history_v1(uuid,text,text,uuid[],integer,boolean)",
            "public.persist_adaptive_comprehensive_answers_batch(uuid,uuid,text,text,timestamptz)",
        ):
            self.assertIn(signature, compact_sql)

    def test_manifest_authorized_skip_is_idempotent_and_never_updates_ability(self):
        skip = self.function_sql("record_adaptive_comprehensive_skip")

        self.assertIn(":adaptive_comprehensive_embargo", skip)
        self.assertIn("for update", skip)
        self.assertIn("manifest->'answers'", skip)
        self.assertIn("answer_entry->'selected_answer' is distinct from 'null'::jsonb", skip)
        self.assertIn("manifest_phase <> 'locked'", skip)
        self.assertIn("item_row.item_status = 'answered'", skip)
        self.assertIn("set item_status = 'skipped'", skip)
        self.assertIn("'idempotent', true", skip)
        self.assertNotIn("user_subject_state", skip)
        self.assertNotIn("adaptive_model_updates", skip)
        self.assertIn(
            "grant execute on function public.record_adaptive_comprehensive_skip( "
            "uuid, uuid, uuid, text, text, timestamptz ) to service_role",
            self.compact(self.sql),
        )

    def test_finalize_atomically_verifies_every_item_and_freezes_completion_state(self):
        finalize = self.function_sql("finalize_adaptive_comprehensive_submission")

        self.assertIn(":adaptive_comprehensive_embargo", finalize)
        self.assertIn("for update", finalize)
        self.assertIn("manifest_phase = 'completed'", finalize)
        self.assertIn("'idempotent', true", finalize)
        self.assertIn("jsonb_array_elements(manifest->'answers')", finalize)
        self.assertIn("answer.client_submission_id is distinct from", finalize)
        self.assertIn("answer.used_time is distinct from", finalize)
        self.assertIn("from public.adaptive_model_updates applied", finalize)
        self.assertIn("raise exception 'adaptive_update_pending'", finalize)
        self.assertIn("completion_state := jsonb_build_object", finalize)
        self.assertIn("'phase', 'completed'", finalize)
        self.assertIn("status = 'completed'", finalize)
        self.assertIn("completed_at = coalesce(completed_at, p_now)", finalize)
        self.assertIn(
            "grant execute on function public.finalize_adaptive_comprehensive_submission( "
            "uuid, uuid, text, text, timestamptz ) to service_role",
            self.compact(self.sql),
        )

    def test_incremental_batch_persistence_is_bounded_atomic_and_manifest_authorized(self):
        sql = self.batch_sql
        start = sql.index(
            "create or replace function public.persist_adaptive_comprehensive_answers_batch("
        )
        body_start = sql.index("as $$", start)
        end = sql.index("\n$$;", body_start) + len("\n$$;")
        function = sql[start:end]
        compact_sql = self.compact(sql)

        self.assertIn("begin;", sql)
        self.assertIn("commit;", sql)
        self.assertIn("security definer", function)
        self.assertIn("set search_path = public, pg_temp", function)
        self.assertGreaterEqual(function.count("perform pg_advisory_xact_lock"), 2)
        self.assertIn(":adaptive_comprehensive_embargo", function)
        self.assertIn("for update", function)
        self.assertIn("session_row.mode <> 'comprehensive'", function)
        self.assertIn("session_row.requested_question_count not between 1 and 30", function)
        self.assertIn("manifest->>'client_submission_id'", function)
        self.assertIn("manifest->>'manifest_hash'", function)
        self.assertIn("upper(coalesce(manifest->>'phase', '')) <> 'locked'", function)
        self.assertIn("order by (value->>'position')::integer", function)
        self.assertIn("public.record_answer_submission(", function)
        self.assertIn("public.record_adaptive_comprehensive_skip(", function)
        self.assertIn("question_row.answer not in ('a', 'b', 'c', 'd')", function)
        self.assertIn("question_row.exam_code not in ('common', session_row.stats_exam_code)", function)
        self.assertIn("processed_count <> session_row.requested_question_count", function)
        for response_field in (
            "'subject_state'",
            "'topic_states'",
            "'pending_conflict'",
            "'external_pending_count'",
            "'adaptive_updated'",
        ):
            self.assertIn(response_field, function)
        self.assertIn("from public.user_subject_state", function)
        self.assertIn("from public.user_topic_state", function)
        self.assertIn("from public.adaptive_conflicts", function)
        self.assertIn("from public.adaptive_model_updates applied", function)
        self.assertIn(
            "revoke all on function public.persist_adaptive_comprehensive_answers_batch( "
            "uuid, uuid, text, text, timestamptz ) from public, anon, authenticated",
            compact_sql,
        )
        self.assertIn(
            "grant execute on function public.persist_adaptive_comprehensive_answers_batch( "
            "uuid, uuid, text, text, timestamptz ) to service_role",
            compact_sql,
        )
        self.assertNotIn("grant execute", self.compact(function))


if __name__ == "__main__":
    unittest.main()
