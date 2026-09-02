from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import ANY, MagicMock, patch
from uuid import uuid4

from app.routes import mentor_consultation


class _Response:
    def __init__(self, data):
        self.data = data


class MentorConsultationCompletionNotificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.order_id = str(uuid4())
        self.applicant_user_id = str(uuid4())
        self.mentor_id = str(uuid4())
        self.mentor_user_id = str(uuid4())
        self.mentor = {
            "id": self.mentor_id,
            "owner_user_id": self.mentor_user_id,
        }

    def _order(
        self,
        *,
        order_status: str = "in_progress",
        applicant_confirmed_at: str | None = None,
        mentor_confirmed_at: str | None = None,
        ended_at: str | None = None,
    ) -> dict:
        return {
            "id": self.order_id,
            "order_no": "MC-COMPLETION-001",
            "applicant_user_id": self.applicant_user_id,
            "mentor_id": self.mentor_id,
            "consultation_type": "instant",
            "order_status": order_status,
            "payment_status": "paid",
            "questionnaire": {
                "name": "测试用户",
                "school": "示例大学",
                "major": "示例专业",
                "grade": "大四",
                "question": "测试咨询问题",
            },
            "price_cents": 3900,
            "consultation_window_minutes": 60,
            "payment_mode": "real",
            "payment_reference": "PAY-COMPLETION-001",
            "started_at": "2026-09-02T08:00:00+00:00",
            "ended_at": ended_at,
            "applicant_completion_confirmed_at": applicant_confirmed_at,
            "mentor_completion_confirmed_at": mentor_confirmed_at,
            "refund_amount_cents": 0,
            "created_at": "2026-09-02T07:50:00+00:00",
            "updated_at": "2026-09-02T08:30:00+00:00",
        }

    def _invoke(
        self,
        *,
        initial_order: dict,
        participant_role: str,
        current_rows: list[dict],
        operation_responses: dict[str, list[_Response]],
        notification_side_effect=None,
    ):
        queues = {name: list(values) for name, values in operation_responses.items()}
        operation_names: list[str] = []

        def fake_call_supabase(_operation, *, operation_name: str):
            operation_names.append(operation_name)
            queue = queues.get(operation_name)
            if not queue:
                self.fail(f"unexpected Supabase operation: {operation_name}")
            return queue.pop(0)

        create_notification = MagicMock(side_effect=notification_side_effect)
        insert_event = MagicMock()
        insert_system_message = MagicMock()
        record_income = MagicMock()

        with (
            patch.object(mentor_consultation, "get_supabase_admin", return_value=object()),
            patch.object(
                mentor_consultation,
                "_get_order_participant",
                return_value=(initial_order, participant_role, self.mentor),
            ),
            patch.object(
                mentor_consultation,
                "_get_order_or_404",
                side_effect=list(current_rows),
            ),
            patch.object(mentor_consultation, "call_supabase", side_effect=fake_call_supabase),
            patch.object(mentor_consultation, "_insert_order_event", insert_event),
            patch.object(mentor_consultation, "_insert_system_message", insert_system_message),
            patch.object(mentor_consultation, "record_consultation_income_pending", record_income),
            patch.object(mentor_consultation, "create_user_notification", create_notification),
        ):
            result = mentor_consultation.complete_mentor_consultation_order(
                self.order_id,
                user_id=(
                    self.mentor_user_id
                    if participant_role == "mentor"
                    else self.applicant_user_id
                ),
            )

        for operation_name, queue in queues.items():
            self.assertEqual(queue, [], f"unused response for {operation_name}")
        return SimpleNamespace(
            result=result,
            create_notification=create_notification,
            insert_event=insert_event,
            insert_system_message=insert_system_message,
            record_income=record_income,
            operation_names=operation_names,
        )

    def test_applicant_first_confirmation_notifies_only_mentor(self):
        confirmed_at = "2026-09-02T08:31:00+00:00"
        current = self._order(applicant_confirmed_at=confirmed_at)

        run = self._invoke(
            initial_order=self._order(),
            participant_role="applicant",
            current_rows=[current],
            operation_responses={
                "consultation completion confirmation": [_Response([current])],
            },
        )

        self.assertEqual(run.result.order_status, "in_progress")
        self.assertEqual(run.result.applicant_completion_confirmed_at, confirmed_at)
        self.assertIsNone(run.result.mentor_completion_confirmed_at)
        run.create_notification.assert_called_once()
        kwargs = run.create_notification.call_args.kwargs
        self.assertEqual(kwargs["recipient_user_id"], self.mentor_user_id)
        self.assertEqual(kwargs["category"], "consultation")
        self.assertEqual(kwargs["notification_type"], "mentor_order_status")
        self.assertEqual(kwargs["related_type"], "mentor_consultation_order")
        self.assertEqual(
            kwargs["related_id"],
            f"{self.order_id}:completion_pending:applicant",
        )
        self.assertEqual(kwargs["delivery_payload"]["audience"], "mentor")
        self.assertEqual(kwargs["delivery_payload"]["event"], "completion_pending")
        self.assertEqual(kwargs["delivery_payload"]["order_id"], self.order_id)
        self.assertIn("role=mentor", kwargs["route_path"])
        self.assertIn("from=mentor-center", kwargs["route_path"])

    def test_mentor_first_confirmation_notifies_only_applicant(self):
        confirmed_at = "2026-09-02T08:32:00+00:00"
        current = self._order(mentor_confirmed_at=confirmed_at)

        run = self._invoke(
            initial_order=self._order(),
            participant_role="mentor",
            current_rows=[current],
            operation_responses={
                "consultation completion confirmation": [_Response([current])],
            },
        )

        self.assertEqual(run.result.order_status, "in_progress")
        self.assertIsNone(run.result.applicant_completion_confirmed_at)
        self.assertEqual(run.result.mentor_completion_confirmed_at, confirmed_at)
        run.create_notification.assert_called_once()
        kwargs = run.create_notification.call_args.kwargs
        self.assertEqual(kwargs["recipient_user_id"], self.applicant_user_id)
        self.assertEqual(kwargs["notification_type"], "mentor_order_status")
        self.assertEqual(
            kwargs["related_id"],
            f"{self.order_id}:completion_pending:mentor",
        )
        self.assertEqual(kwargs["delivery_payload"]["audience"], "applicant")
        self.assertEqual(kwargs["delivery_payload"]["event"], "completion_pending")
        self.assertIn("role=applicant", kwargs["route_path"])
        self.assertIn("from=my-consultations", kwargs["route_path"])

    def test_second_confirmation_completes_order_and_notifies_both_parties(self):
        applicant_confirmed_at = "2026-09-02T08:34:00+00:00"
        mentor_confirmed_at = "2026-09-02T08:33:00+00:00"
        both_confirmed = self._order(
            applicant_confirmed_at=applicant_confirmed_at,
            mentor_confirmed_at=mentor_confirmed_at,
        )
        completed = self._order(
            order_status="completed",
            applicant_confirmed_at=applicant_confirmed_at,
            mentor_confirmed_at=mentor_confirmed_at,
            ended_at="2026-09-02T08:34:00+00:00",
        )

        run = self._invoke(
            initial_order=self._order(mentor_confirmed_at=mentor_confirmed_at),
            participant_role="applicant",
            current_rows=[both_confirmed],
            operation_responses={
                "consultation completion confirmation": [_Response([both_confirmed])],
                "consultation order complete after mutual confirmation": [_Response([completed])],
            },
        )

        self.assertEqual(run.result.order_status, "completed")
        self.assertEqual(run.result.ended_at, completed["ended_at"])
        self.assertEqual(run.create_notification.call_count, 2)
        calls_by_audience = {
            item.kwargs["delivery_payload"]["audience"]: item.kwargs
            for item in run.create_notification.call_args_list
        }
        self.assertEqual(set(calls_by_audience), {"applicant", "mentor"})
        for audience, kwargs in calls_by_audience.items():
            self.assertEqual(kwargs["category"], "consultation")
            self.assertEqual(kwargs["notification_type"], "mentor_order_status")
            self.assertEqual(kwargs["related_id"], f"{self.order_id}:completed")
            self.assertEqual(kwargs["delivery_payload"]["event"], "completed")
            self.assertEqual(kwargs["delivery_payload"]["order_status"], "completed")
            self.assertNotIn("confirming_role", kwargs["delivery_payload"])
            self.assertNotIn("completion_pending", kwargs["related_id"])
            self.assertIn(f"role={audience}", kwargs["route_path"])
        self.assertEqual(
            calls_by_audience["applicant"]["recipient_user_id"],
            self.applicant_user_id,
        )
        self.assertEqual(
            calls_by_audience["mentor"]["recipient_user_id"],
            self.mentor_user_id,
        )
        run.record_income.assert_called_once_with(ANY, completed)

    def test_repeated_confirmation_by_same_party_does_not_notify_again(self):
        applicant_confirmed_at = "2026-09-02T08:35:00+00:00"
        current = self._order(applicant_confirmed_at=applicant_confirmed_at)

        run = self._invoke(
            initial_order=current,
            participant_role="applicant",
            current_rows=[current],
            operation_responses={},
        )

        self.assertEqual(run.result.order_status, "in_progress")
        self.assertEqual(run.operation_names, [])
        run.create_notification.assert_not_called()
        run.insert_event.assert_not_called()

    def test_concurrent_completion_loser_returns_completed_without_duplicate_notification(self):
        applicant_confirmed_at = "2026-09-02T08:37:00+00:00"
        mentor_confirmed_at = "2026-09-02T08:36:00+00:00"
        both_confirmed = self._order(
            applicant_confirmed_at=applicant_confirmed_at,
            mentor_confirmed_at=mentor_confirmed_at,
        )
        completed = self._order(
            order_status="completed",
            applicant_confirmed_at=applicant_confirmed_at,
            mentor_confirmed_at=mentor_confirmed_at,
            ended_at="2026-09-02T08:37:00+00:00",
        )

        run = self._invoke(
            initial_order=self._order(mentor_confirmed_at=mentor_confirmed_at),
            participant_role="applicant",
            current_rows=[both_confirmed, completed],
            operation_responses={
                "consultation completion confirmation": [_Response([both_confirmed])],
                "consultation order complete after mutual confirmation": [_Response([])],
            },
        )

        self.assertEqual(run.result.order_status, "completed")
        run.create_notification.assert_not_called()
        run.record_income.assert_not_called()
        completed_events = [
            item
            for item in run.insert_event.call_args_list
            if item.kwargs.get("event_type") == "consultation_completed"
        ]
        self.assertEqual(completed_events, [])

    def test_completed_retry_retries_idempotent_notification_enqueue(self):
        completed = self._order(
            order_status="completed",
            applicant_confirmed_at="2026-09-02T08:37:00+00:00",
            mentor_confirmed_at="2026-09-02T08:38:00+00:00",
            ended_at="2026-09-02T08:38:00+00:00",
        )

        run = self._invoke(
            initial_order=completed,
            participant_role="applicant",
            current_rows=[],
            operation_responses={},
        )

        self.assertEqual(run.result.order_status, "completed")
        self.assertEqual(run.create_notification.call_count, 2)
        self.assertEqual(
            {
                item.kwargs["delivery_payload"]["audience"]
                for item in run.create_notification.call_args_list
            },
            {"applicant", "mentor"},
        )
        for item in run.create_notification.call_args_list:
            self.assertNotIn("confirming_role", item.kwargs["delivery_payload"])
        run.record_income.assert_not_called()

    def test_completed_notification_payload_is_stable_across_role_retries(self):
        completed = self._order(
            order_status="completed",
            applicant_confirmed_at="2026-09-02T08:37:00+00:00",
            mentor_confirmed_at="2026-09-02T08:38:00+00:00",
            ended_at="2026-09-02T08:38:00+00:00",
        )

        with patch.object(mentor_consultation, "create_user_notification") as create_notification:
            mentor_consultation._notify_consultation_completion_status(
                object(),
                order=completed,
                mentor=self.mentor,
                recipient_role="applicant",
                event="completed",
                confirming_role="applicant",
            )
            mentor_consultation._notify_consultation_completion_status(
                object(),
                order=completed,
                mentor=self.mentor,
                recipient_role="applicant",
                event="completed",
                confirming_role="mentor",
            )

        self.assertEqual(create_notification.call_count, 2)
        first_kwargs = create_notification.call_args_list[0].kwargs
        second_kwargs = create_notification.call_args_list[1].kwargs
        self.assertEqual(first_kwargs, second_kwargs)
        self.assertNotIn("confirming_role", first_kwargs["delivery_payload"])

    def test_admin_completed_order_without_mutual_confirmation_does_not_claim_mutual_completion(self):
        completed = self._order(
            order_status="completed",
            ended_at="2026-09-02T08:38:00+00:00",
        )

        run = self._invoke(
            initial_order=completed,
            participant_role="applicant",
            current_rows=[],
            operation_responses={},
        )

        self.assertEqual(run.result.order_status, "completed")
        run.create_notification.assert_not_called()

    def test_admin_completion_race_after_one_confirmation_does_not_send_pending_notice(self):
        confirmed_at = "2026-09-02T08:40:00+00:00"
        update_result = self._order(applicant_confirmed_at=confirmed_at)
        admin_completed = self._order(
            order_status="completed",
            applicant_confirmed_at=confirmed_at,
            ended_at="2026-09-02T08:40:01+00:00",
        )

        run = self._invoke(
            initial_order=self._order(),
            participant_role="applicant",
            current_rows=[admin_completed],
            operation_responses={
                "consultation completion confirmation": [_Response([update_result])],
            },
        )

        self.assertEqual(run.result.order_status, "completed")
        run.create_notification.assert_not_called()
        self.assertNotIn(
            "consultation order complete after mutual confirmation",
            run.operation_names,
        )

    def test_notification_failure_does_not_change_successful_completion_response(self):
        applicant_confirmed_at = "2026-09-02T08:39:00+00:00"
        mentor_confirmed_at = "2026-09-02T08:38:00+00:00"
        both_confirmed = self._order(
            applicant_confirmed_at=applicant_confirmed_at,
            mentor_confirmed_at=mentor_confirmed_at,
        )
        completed = self._order(
            order_status="completed",
            applicant_confirmed_at=applicant_confirmed_at,
            mentor_confirmed_at=mentor_confirmed_at,
            ended_at="2026-09-02T08:39:00+00:00",
        )

        run = self._invoke(
            initial_order=self._order(mentor_confirmed_at=mentor_confirmed_at),
            participant_role="applicant",
            current_rows=[both_confirmed],
            operation_responses={
                "consultation completion confirmation": [_Response([both_confirmed])],
                "consultation order complete after mutual confirmation": [_Response([completed])],
            },
            notification_side_effect=RuntimeError("notification outbox unavailable"),
        )

        self.assertEqual(run.result.order_status, "completed")
        self.assertEqual(run.create_notification.call_count, 2)
        run.record_income.assert_called_once()


if __name__ == "__main__":
    unittest.main()
