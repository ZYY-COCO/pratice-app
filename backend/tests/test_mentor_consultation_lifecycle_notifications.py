from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.services import mentor_consultation_lifecycle as lifecycle


class _Response:
    def __init__(self, data):
        self.data = data


class MentorConsultationLifecycleNotificationTests(unittest.TestCase):
    now = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)

    def _order(
        self,
        *,
        status: str,
        consultation_type: str = "instant",
        payment_reference: str = "MOCK-PAY-001",
    ) -> dict:
        return {
            "id": f"order-{status}",
            "order_no": "M202609010001",
            "applicant_user_id": "applicant-1",
            "mentor_id": "mentor-1",
            "consultation_type": consultation_type,
            "slot_id": "slot-1" if consultation_type == "booking" else None,
            "order_status": status,
            "payment_status": "paid",
            "payment_reference": payment_reference,
            "price_cents": 3900,
            "refund_amount_cents": 0,
            "expires_at": (self.now - timedelta(minutes=1)).isoformat(),
            "accepted_at": (self.now - timedelta(minutes=20)).isoformat(),
            "started_at": None,
        }

    def test_pending_accept_timeout_notifies_applicant_with_refund_result(self):
        order = self._order(status="pending_accept")
        settled = {
            **order,
            "order_status": "timeout",
            "payment_status": "refunded",
            "refund_amount_cents": 3900,
        }

        with (
            patch.object(lifecycle, "call_supabase", return_value=_Response([settled])),
            patch.object(lifecycle, "_insert_system_message"),
            patch.object(lifecycle, "_insert_event"),
            patch.object(lifecycle, "create_user_notification") as create_notification,
        ):
            result = lifecycle.refresh_expired_mentor_consultation_order(object(), order, now=self.now)

        self.assertEqual(result["order_status"], "timeout")
        create_notification.assert_called_once()
        kwargs = create_notification.call_args.kwargs
        self.assertEqual(kwargs["recipient_user_id"], "applicant-1")
        self.assertEqual(kwargs["category"], "consultation")
        self.assertEqual(kwargs["notification_type"], "mentor_order_status")
        self.assertEqual(kwargs["title"], "本次咨询已自动取消")
        self.assertIn("测试退款已完成", kwargs["content"])
        self.assertEqual(kwargs["related_type"], "mentor_consultation_order")
        self.assertEqual(kwargs["related_id"], "order-pending_accept:timeout")
        self.assertEqual(
            kwargs["route_path"],
            "/pages-sub-consultation/consultation/my-consultations",
        )
        self.assertEqual(kwargs["delivery_payload"]["event"], "timeout")
        self.assertEqual(kwargs["delivery_payload"]["timeout_reason"], "order_timed_out")
        self.assertEqual(kwargs["delivery_payload"]["payment_status"], "refunded")

    def test_accepted_start_timeout_notifies_that_refund_is_processing(self):
        order = self._order(status="accepted", payment_reference="WX-PAY-001")
        settled = {
            **order,
            "order_status": "timeout",
            "payment_status": "refunding",
            "refund_amount_cents": 3900,
        }

        with (
            patch.object(lifecycle, "call_supabase", return_value=_Response([settled])),
            patch.object(lifecycle, "_insert_system_message"),
            patch.object(lifecycle, "_insert_event"),
            patch.object(lifecycle, "create_user_notification") as create_notification,
        ):
            result = lifecycle.refresh_expired_mentor_consultation_order(object(), order, now=self.now)

        self.assertEqual(result["payment_status"], "refunding")
        kwargs = create_notification.call_args.kwargs
        self.assertEqual(kwargs["title"], "本次咨询未按时开始")
        self.assertIn("平台已提交退款处理", kwargs["content"])
        self.assertEqual(
            kwargs["delivery_payload"]["timeout_reason"],
            "accepted_start_timed_out",
        )

    def test_booking_no_show_timeout_notifies_applicant(self):
        order = self._order(status="booked", consultation_type="booking")
        settled = {
            **order,
            "order_status": "timeout",
            "payment_status": "refunded",
            "refund_amount_cents": 3900,
        }

        def fake_call_supabase(_operation, *, operation_name: str):
            if operation_name == "consultation booking slot lifecycle lookup":
                return _Response([{"id": "slot-1", "ends_at": (self.now - timedelta(minutes=1)).isoformat()}])
            if operation_name == "consultation booking no-show settlement":
                return _Response([settled])
            if operation_name == "consultation booking no-show slot expiry":
                return _Response([{"id": "slot-1", "status": "expired"}])
            self.fail(f"unexpected operation: {operation_name}")

        with (
            patch.object(lifecycle, "call_supabase", side_effect=fake_call_supabase),
            patch.object(lifecycle, "_insert_system_message"),
            patch.object(lifecycle, "_insert_event"),
            patch.object(lifecycle, "create_user_notification") as create_notification,
        ):
            result = lifecycle.refresh_expired_mentor_consultation_order(object(), order, now=self.now)

        self.assertEqual(result["order_status"], "timeout")
        kwargs = create_notification.call_args.kwargs
        self.assertEqual(kwargs["title"], "预约咨询未按时开始")
        self.assertIn("预约时段已结束", kwargs["content"])
        self.assertEqual(kwargs["delivery_payload"]["consultation_type"], "booking")
        self.assertEqual(
            kwargs["delivery_payload"]["timeout_reason"],
            "booking_no_show_timed_out",
        )

    def test_notification_failure_does_not_rollback_successful_timeout(self):
        order = self._order(status="pending_accept")
        settled = {
            **order,
            "order_status": "timeout",
            "payment_status": "refunded",
            "refund_amount_cents": 3900,
        }

        with (
            patch.object(lifecycle, "call_supabase", return_value=_Response([settled])),
            patch.object(lifecycle, "_insert_system_message"),
            patch.object(lifecycle, "_insert_event"),
            patch.object(
                lifecycle,
                "create_user_notification",
                side_effect=RuntimeError("notification store unavailable"),
            ),
        ):
            result = lifecycle.refresh_expired_mentor_consultation_order(object(), order, now=self.now)

        self.assertEqual(result["order_status"], "timeout")
        self.assertEqual(result["payment_status"], "refunded")

    def test_lost_conditional_transition_does_not_emit_notification(self):
        order = self._order(status="pending_accept")
        current = {**order, "order_status": "accepted"}

        def fake_call_supabase(_operation, *, operation_name: str):
            if operation_name == "consultation instant timeout settlement":
                return _Response([])
            if operation_name == "consultation lifecycle order refresh":
                return _Response([current])
            self.fail(f"unexpected operation: {operation_name}")

        with (
            patch.object(lifecycle, "call_supabase", side_effect=fake_call_supabase),
            patch.object(lifecycle, "create_user_notification") as create_notification,
        ):
            result = lifecycle.refresh_expired_mentor_consultation_order(object(), order, now=self.now)

        self.assertEqual(result["order_status"], "accepted")
        create_notification.assert_not_called()


if __name__ == "__main__":
    unittest.main()
