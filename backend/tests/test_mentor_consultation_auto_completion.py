from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import ANY, patch
from uuid import UUID

from fastapi import HTTPException
from app.routes import mentor_consultation as mentor_consultation_routes
from app.schemas.mentor_consultation import MentorConsultationMessageCreateRequest
from app.services import mentor_consultation_lifecycle as lifecycle
from app.services.mentor_consultation import serialize_mentor_order


class _Response:
    def __init__(self, data):
        self.data = data


class MentorConsultationAutoCompletionTests(unittest.TestCase):
    now = datetime(2026, 9, 3, 12, 0, tzinfo=timezone.utc)

    def _order(self, **overrides) -> dict:
        order = {
            "id": "order-auto-complete-1",
            "order_no": "MC-AUTO-001",
            "applicant_user_id": "applicant-1",
            "mentor_id": "mentor-1",
            "consultation_type": "instant",
            "slot_id": None,
            "order_status": "in_progress",
            "payment_status": "paid",
            "payment_mode": "real",
            "payment_reference": "PAY-AUTO-001",
            "price_cents": 3900,
            "consultation_window_minutes": 60,
            "started_at": (self.now - timedelta(minutes=60)).isoformat(),
            "ended_at": None,
            "applicant_completion_confirmed_at": None,
            "mentor_completion_confirmed_at": None,
        }
        order.update(overrides)
        return order

    def test_order_before_service_deadline_is_unchanged_without_rpc(self):
        order = self._order(started_at=(self.now - timedelta(minutes=59, seconds=59)).isoformat())
        with (
            patch.object(lifecycle, "call_supabase") as call_supabase,
            patch.object(lifecycle, "record_consultation_income_pending") as record_income,
        ):
            result = lifecycle.refresh_expired_mentor_consultation_order(
                object(),
                order,
                now=self.now,
            )

        self.assertIs(result, order)
        call_supabase.assert_not_called()
        record_income.assert_not_called()

    def test_exact_deadline_auto_completes_without_forging_confirmations(self):
        confirmed_at = (self.now - timedelta(minutes=10)).isoformat()
        order = self._order(applicant_completion_confirmed_at=confirmed_at)
        completed = {
            **order,
            "order_status": "completed",
            "ended_at": self.now.isoformat(),
        }

        with (
            patch.object(lifecycle, "call_supabase", return_value=_Response([completed])) as call_supabase,
            patch.object(lifecycle, "record_consultation_income_pending") as record_income,
            patch.object(lifecycle, "_insert_system_message") as insert_message,
            patch.object(lifecycle, "_insert_event") as insert_event,
            patch.object(lifecycle, "create_user_notification") as create_notification,
        ):
            result = lifecycle.refresh_expired_mentor_consultation_order(
                object(),
                order,
                now=self.now,
            )

        self.assertEqual(result["order_status"], "completed")
        self.assertEqual(result["ended_at"], self.now.isoformat())
        self.assertEqual(result["applicant_completion_confirmed_at"], confirmed_at)
        self.assertIsNone(result["mentor_completion_confirmed_at"])
        self.assertEqual(
            call_supabase.call_args.kwargs["operation_name"],
            "consultation service window auto completion",
        )
        # The database RPC owns all visible side effects in its transaction.
        insert_message.assert_not_called()
        insert_event.assert_not_called()
        create_notification.assert_not_called()
        record_income.assert_called_once_with(ANY, completed)

    def test_custom_window_uses_order_duration(self):
        order = self._order(
            consultation_window_minutes=90,
            started_at=(self.now - timedelta(minutes=60)).isoformat(),
        )
        with patch.object(lifecycle, "call_supabase") as call_supabase:
            result = lifecycle.refresh_expired_mentor_consultation_order(
                object(),
                order,
                now=self.now,
            )

        self.assertIs(result, order)
        call_supabase.assert_not_called()

    def test_open_report_marks_expired_order_as_dispute_blocked(self):
        order = self._order()

        def fake_call_supabase(_operation, *, operation_name: str):
            if operation_name == "consultation service window auto completion":
                return _Response([])
            if operation_name == "consultation lifecycle order refresh":
                return _Response([order])
            if operation_name == "consultation auto completion dispute lookup":
                return _Response([{"id": "report-1", "status": "reviewing"}])
            self.fail(f"unexpected operation: {operation_name}")

        with (
            patch.object(lifecycle, "call_supabase", side_effect=fake_call_supabase),
            patch.object(lifecycle, "record_consultation_income_pending") as record_income,
        ):
            result = lifecycle.refresh_expired_mentor_consultation_order(
                object(),
                order,
                now=self.now,
            )

        self.assertEqual(result["order_status"], "in_progress")
        self.assertTrue(result["auto_completion_blocked_by_dispute"])
        record_income.assert_not_called()

    def test_open_appeal_marks_expired_order_as_dispute_blocked(self):
        order = self._order()

        def fake_call_supabase(_operation, *, operation_name: str):
            if operation_name == "consultation service window auto completion":
                return _Response([])
            if operation_name == "consultation lifecycle order refresh":
                return _Response([order])
            if operation_name == "consultation auto completion dispute lookup":
                return _Response([{"id": "report-1", "status": "resolved"}])
            if operation_name == "consultation auto completion appeal lookup":
                return _Response([{"id": "appeal-1"}])
            self.fail(f"unexpected operation: {operation_name}")

        with patch.object(lifecycle, "call_supabase", side_effect=fake_call_supabase):
            result = lifecycle.refresh_expired_mentor_consultation_order(
                object(),
                order,
                now=self.now,
            )

        self.assertTrue(result["auto_completion_blocked_by_dispute"])

    def test_missing_rpc_keeps_order_reads_available_during_rollout(self):
        order = self._order()
        with (
            patch.object(
                lifecycle,
                "call_supabase",
                side_effect=RuntimeError(
                    "PGRST202 Could not find the function in the schema cache"
                ),
            ),
            patch.object(lifecycle, "record_consultation_income_pending") as record_income,
        ):
            result = lifecycle.refresh_expired_mentor_consultation_order(
                object(),
                order,
                now=self.now,
            )

        self.assertIs(result, order)
        record_income.assert_not_called()

    def test_serialized_order_exposes_server_deadline_contract(self):
        started_at = self.now - timedelta(minutes=7)
        payload = serialize_mentor_order(self._order(
            consultation_window_minutes=90,
            started_at=started_at.isoformat(),
            auto_completion_blocked_by_dispute=True,
        ))

        server_now = datetime.fromisoformat(payload["server_now"])
        service_ends_at = datetime.fromisoformat(payload["service_ends_at"])
        self.assertLess(abs((server_now - datetime.now(timezone.utc)).total_seconds()), 2)
        self.assertEqual(service_ends_at, started_at + timedelta(minutes=90))
        self.assertTrue(payload["auto_completion_blocked_by_dispute"])

    def test_background_sweep_uses_dispute_filtered_batch_rpc(self):
        completed = self._order(order_status="completed", ended_at=self.now.isoformat())
        operation_names: list[str] = []

        def fake_call_supabase(_operation, *, operation_name: str):
            operation_names.append(operation_name)
            if operation_name == "consultation lifecycle in-progress batch completion":
                return _Response([completed])
            return _Response([])

        with (
            patch.object(lifecycle, "get_supabase_admin", return_value=object()),
            patch.object(lifecycle, "call_supabase", side_effect=fake_call_supabase),
            patch.object(lifecycle, "record_consultation_income_pending") as record_income,
            patch.object(lifecycle, "sweep_mentor_consultation_report_slas", return_value=0),
        ):
            changed = lifecycle.settle_expired_mentor_consultation_orders()

        self.assertEqual(changed, 1)
        self.assertIn("consultation lifecycle in-progress batch completion", operation_names)
        self.assertNotIn("consultation lifecycle in-progress candidate list", operation_names)
        record_income.assert_called_once_with(ANY, completed)

    def test_missing_batch_rpc_does_not_block_other_lifecycle_sweeps(self):
        operation_names: list[str] = []

        def fake_call_supabase(_operation, *, operation_name: str):
            operation_names.append(operation_name)
            if operation_name == "consultation lifecycle in-progress batch completion":
                raise RuntimeError("PGRST202 function missing from schema cache")
            return _Response([])

        with (
            patch.object(lifecycle, "get_supabase_admin", return_value=object()),
            patch.object(lifecycle, "call_supabase", side_effect=fake_call_supabase),
            patch.object(lifecycle, "sweep_mentor_consultation_report_slas", return_value=0),
        ):
            changed = lifecycle.settle_expired_mentor_consultation_orders()

        self.assertEqual(changed, 0)
        self.assertIn("consultation lifecycle payment hold candidate list", operation_names)
        self.assertIn("consultation lifecycle terminal booking cleanup list", operation_names)


class MentorConsultationAutoCompletionSqlContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        migration = (
            Path(__file__).resolve().parents[2]
            / "database"
            / "mentor_consultation_auto_complete.sql"
        )
        cls.sql = migration.read_text(encoding="utf-8").lower()

    def test_atomic_rpc_checks_status_deadline_reports_and_appeals(self):
        self.assertIn("v_order.order_status <> 'in_progress'", self.sql)
        self.assertIn("v_service_ends_at > p_now", self.sql)
        self.assertIn("report.status in ('pending', 'reviewing')", self.sql)
        self.assertIn("appeal.status in ('pending', 'reviewing')", self.sql)
        self.assertIn("ended_at = v_service_ends_at", self.sql)
        self.assertNotIn("applicant_completion_confirmed_at =", self.sql)
        self.assertNotIn("mentor_completion_confirmed_at =", self.sql)

    def test_report_appeal_and_message_writes_share_order_lock_protocol(self):
        lock_key = "mentor-consultation-order:"
        self.assertGreaterEqual(self.sql.count(lock_key), 4)
        self.assertIn("lock_mentor_consultation_order_for_report_write", self.sql)
        self.assertIn("lock_mentor_consultation_order_for_appeal_write", self.sql)
        self.assertIn("guard_mentor_consultation_participant_message_write", self.sql)
        self.assertIn("consultation_message_window_closed", self.sql)
        self.assertIn("if new.sender_role = 'system'", self.sql)

    def test_database_message_guard_closes_after_either_confirmation(self):
        guard_start = self.sql.index(
            "create or replace function public.guard_mentor_consultation_participant_message_write"
        )
        guard_end = self.sql.index(
            "create or replace function public.auto_complete_expired_mentor_consultation_order",
            guard_start,
        )
        guard_sql = self.sql[guard_start:guard_end]

        self.assertIn("orders.applicant_completion_confirmed_at", guard_sql)
        self.assertIn("orders.mentor_completion_confirmed_at", guard_sql)
        self.assertIn("v_applicant_completion_confirmed_at is not null", guard_sql)
        self.assertIn("v_mentor_completion_confirmed_at is not null", guard_sql)
        self.assertIn("for update", guard_sql)

    def test_rpc_owns_idempotent_visible_side_effects(self):
        self.assertIn("insert into public.mentor_consultation_messages", self.sql)
        self.assertIn("'consultation_auto_completed'", self.sql)
        self.assertIn("insert into public.user_notification_outbox", self.sql)
        self.assertIn("uq_mentor_consultation_auto_completed_event", self.sql)
        self.assertIn("uq_mentor_consultation_system_message_business_key", self.sql)
        self.assertIn("on conflict (recipient_user_id, event_key) do nothing", self.sql)

    def test_batch_rpc_filters_disputes_before_limit_and_uses_service_deadline(self):
        batch_start = self.sql.index(
            "create or replace function public.auto_complete_expired_mentor_consultation_orders"
        )
        batch_sql = self.sql[batch_start:]
        self.assertIn("orders.service_ends_at <= p_now", batch_sql)
        self.assertLess(batch_sql.index("not exists"), batch_sql.index("limit greatest"))
        self.assertIn("order by orders.service_ends_at", batch_sql)

    def test_migration_backfills_legacy_started_at_with_audit_event(self):
        self.assertIn("consultation_started_at_backfilled", self.sql)
        self.assertIn("coalesce(orders.accepted_at, orders.created_at)", self.sql)
        self.assertIn("sync_mentor_consultation_service_ends_at", self.sql)
        self.assertIn("idx_mentor_consultation_orders_in_progress_service_end", self.sql)

    def test_completed_booking_slot_converges_after_slot_end(self):
        self.assertIn("v_order.consultation_type = 'booking'", self.sql)
        self.assertIn("slot.status = 'booked'", self.sql)
        self.assertIn("slot.ends_at <= p_now", self.sql)


class MentorConsultationMessageDeadlineTests(unittest.TestCase):
    def test_either_party_confirmation_blocks_participant_message(self):
        order_id = UUID("11111111-1111-4111-8111-111111111111")

        for participant_role, confirmed_field in (
            ("applicant", "mentor_completion_confirmed_at"),
            ("mentor", "applicant_completion_confirmed_at"),
        ):
            with self.subTest(participant_role=participant_role):
                order = {
                    "id": str(order_id),
                    "applicant_user_id": "applicant-1",
                    "mentor_id": "mentor-1",
                    "order_status": "in_progress",
                    "consultation_window_minutes": 60,
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "applicant_completion_confirmed_at": None,
                    "mentor_completion_confirmed_at": None,
                    confirmed_field: datetime.now(timezone.utc).isoformat(),
                }
                operation_names: list[str] = []

                def fake_call_supabase(_operation, *, operation_name: str):
                    operation_names.append(operation_name)
                    if operation_name == "consultation idempotent message lookup":
                        return _Response([])
                    self.fail(f"unexpected operation: {operation_name}")

                with (
                    patch.object(mentor_consultation_routes, "get_supabase_admin", return_value=object()),
                    patch.object(
                        mentor_consultation_routes,
                        "_get_order_participant",
                        return_value=(order, participant_role, {"id": "mentor-1"}),
                    ),
                    patch.object(
                        mentor_consultation_routes,
                        "_refresh_pending_accept_status",
                        return_value=order,
                    ),
                    patch.object(mentor_consultation_routes, "call_supabase", side_effect=fake_call_supabase),
                ):
                    with self.assertRaises(HTTPException) as raised:
                        mentor_consultation_routes.create_mentor_consultation_message(
                            order_id,
                            MentorConsultationMessageCreateRequest(
                                content="结束确认后的消息",
                                client_message_id=f"post-confirmation-{participant_role}",
                            ),
                            user_id=f"{participant_role}-1",
                        )

                self.assertEqual(raised.exception.status_code, 409)
                self.assertIn("结束确认", str(raised.exception.detail))
                self.assertNotIn("consultation message create", operation_names)

    def test_database_deadline_race_is_returned_as_conflict(self):
        order_id = UUID("11111111-1111-4111-8111-111111111111")
        order = {
            "id": str(order_id),
            "applicant_user_id": "applicant-1",
            "mentor_id": "mentor-1",
            "order_status": "in_progress",
            "consultation_window_minutes": 60,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "applicant_completion_confirmed_at": None,
        }

        def fake_call_supabase(_operation, *, operation_name: str):
            if operation_name == "consultation idempotent message lookup":
                return _Response([])
            if operation_name == "consultation message create":
                raise RuntimeError("P0001 consultation_message_window_closed")
            self.fail(f"unexpected operation: {operation_name}")

        with (
            patch.object(mentor_consultation_routes, "get_supabase_admin", return_value=object()),
            patch.object(
                mentor_consultation_routes,
                "_get_order_participant",
                return_value=(order, "applicant", {"id": "mentor-1"}),
            ),
            patch.object(
                mentor_consultation_routes,
                "_refresh_pending_accept_status",
                return_value=order,
            ),
            patch.object(mentor_consultation_routes, "call_supabase", side_effect=fake_call_supabase),
        ):
            with self.assertRaises(HTTPException) as raised:
                mentor_consultation_routes.create_mentor_consultation_message(
                    order_id,
                    MentorConsultationMessageCreateRequest(
                        content="服务截止边界消息",
                        client_message_id="deadline-race-1",
                    ),
                    user_id="applicant-1",
                )

        self.assertEqual(raised.exception.status_code, 409)
        self.assertIn("已停止发送", str(raised.exception.detail))


if __name__ == "__main__":
    unittest.main()
