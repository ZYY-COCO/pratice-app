from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException

from app.routes import mentor_consultation
from app.schemas.mentor_consultation import MentorConsultationPaymentWebhookRequest


class _Response:
    def __init__(self, data):
        self.data = data


class _OrderQuery:
    def __init__(self, client, table_name: str):
        self.client = client
        self.table_name = table_name
        self.action = "select"
        self.payload: dict | None = None
        self.filters: list[tuple[str, object]] = []
        self.in_filters: list[tuple[str, set[object]]] = []
        self.limit_value: int | None = None

    def select(self, *_args, **_kwargs):
        return self

    def update(self, payload: dict):
        self.action = "update"
        self.payload = dict(payload)
        return self

    def eq(self, field: str, value: object):
        self.filters.append((field, value))
        return self

    def in_(self, field: str, values):
        self.in_filters.append((field, set(values)))
        return self

    def limit(self, value: int):
        self.limit_value = value
        return self

    def execute(self):
        rows = self.client.rows.setdefault(self.table_name, [])
        matched = [
            row
            for row in rows
            if all(row.get(field) == value for field, value in self.filters)
            and all(row.get(field) in values for field, values in self.in_filters)
        ]
        if self.action == "update":
            for row in matched:
                row.update(self.payload or {})
        if self.limit_value is not None:
            matched = matched[: self.limit_value]
        return _Response(matched)


class _OrderClient:
    def __init__(self, order: dict):
        self.rows = {"mentor_consultation_orders": [order]}

    def table(self, table_name: str):
        return _OrderQuery(self, table_name)


def _order(*, payment_status: str, order_status: str = "cancelled") -> dict:
    return {
        "id": str(uuid4()),
        "order_no": f"M{uuid4().hex[:12].upper()}",
        "client_order_id": None,
        "applicant_user_id": str(uuid4()),
        "mentor_id": str(uuid4()),
        "slot_id": None,
        "consultation_type": "instant",
        "order_status": order_status,
        "payment_status": payment_status,
        "questionnaire": {
            "name": "张同学",
            "school": "示例大学",
            "major": "经济学",
            "grade": "大四",
            "graduation_year": 2027,
            "question": "如何准备复试？",
        },
        "price_cents": 3900,
        "consultation_window_minutes": 60,
        "payment_reference": "PAY-TEST-001",
        "payment_expires_at": None,
        "payment_mode": "real",
        "accepted_at": None,
        "expires_at": None,
        "started_at": None,
        "ended_at": "2026-09-02T08:00:00+00:00",
        "applicant_completion_confirmed_at": None,
        "mentor_completion_confirmed_at": None,
        "refund_amount_cents": 3900,
        "refund_reference": "REFUND-TEST-001",
        "created_at": "2026-09-02T07:00:00+00:00",
        "updated_at": "2026-09-02T08:00:00+00:00",
    }


def _payload(status: str, *, failure_reason: str | None = None) -> MentorConsultationPaymentWebhookRequest:
    kwargs = {
        "provider": "wechat",
        "provider_event_id": f"event-{status}-{uuid4()}",
        "order_no": "MPLACEHOLDER",
        "payment_reference": "PAY-TEST-001",
        "status": status,
        "amount_cents": 3900,
        "failure_reason": failure_reason,
    }
    if status in {"refunded", "refund_failed"}:
        kwargs.update({
            "refund_amount_cents": 3900,
            "refund_reference": "REFUND-TEST-001",
        })
    return MentorConsultationPaymentWebhookRequest(**kwargs)


class MentorConsultationPaymentNotificationTests(unittest.TestCase):
    def _call_webhook(self, order: dict, payload: MentorConsultationPaymentWebhookRequest, **patches):
        payload.order_no = order["order_no"]
        client = _OrderClient(order)
        settings = SimpleNamespace(payment_webhook_secret="webhook-secret")
        stack = [
            patch.object(mentor_consultation, "get_settings", return_value=settings),
            patch.object(mentor_consultation, "_real_payment_ready", return_value=True),
            patch.object(mentor_consultation, "_configured_payment_provider", return_value="wechat"),
            patch.object(mentor_consultation, "get_supabase_admin", return_value=client),
            patch.object(mentor_consultation, "_refresh_pending_accept_status", side_effect=lambda _client, row: row),
            patch.object(mentor_consultation, "_insert_order_event"),
            patch.object(mentor_consultation, "_insert_system_message"),
            patch.object(mentor_consultation, "record_consultation_refund"),
        ]
        for name, value in patches.items():
            stack.append(patch.object(mentor_consultation, name, value))

        entered = []
        try:
            for item in stack:
                entered.append(item)
                item.start()
            result = mentor_consultation.handle_mentor_consultation_payment_webhook(
                payload,
                x_payment_webhook_secret="webhook-secret",
            )
        finally:
            for item in reversed(entered):
                item.stop()
        return result, client

    def test_payment_status_helper_uses_existing_consultation_red_dot_contract(self):
        order = _order(payment_status="refunded")

        with patch.object(mentor_consultation, "create_user_notification") as create_notification:
            mentor_consultation._notify_consultation_applicant_payment_status(
                object(),
                order=order,
                event="refund_completed",
            )

        create_notification.assert_called_once()
        kwargs = create_notification.call_args.kwargs
        self.assertEqual(kwargs["recipient_user_id"], order["applicant_user_id"])
        self.assertEqual(kwargs["category"], "consultation")
        self.assertEqual(kwargs["notification_type"], "mentor_order_status")
        self.assertEqual(kwargs["related_type"], "mentor_consultation_order")
        self.assertEqual(
            kwargs["related_id"],
            f"{order['id']}:refund_completed:{order['refund_reference']}",
        )
        self.assertEqual(
            kwargs["route_path"],
            "/pages-sub-consultation/consultation/my-consultations",
        )
        self.assertIn("¥39.00", kwargs["summary"])
        self.assertEqual(kwargs["delivery_payload"]["audience"], "applicant")
        self.assertEqual(kwargs["delivery_payload"]["event"], "refund_completed")
        self.assertEqual(kwargs["delivery_payload"]["order_id"], order["id"])
        self.assertEqual(kwargs["delivery_payload"]["refund_amount_cents"], 3900)

    def test_refunded_callback_updates_order_and_notifies_applicant(self):
        order = _order(payment_status="refunding")
        payload = _payload("refunded")

        with patch.object(mentor_consultation, "_notify_consultation_applicant_payment_status") as notify:
            result, client = self._call_webhook(order, payload)

        self.assertFalse(result.idempotent)
        self.assertEqual(result.order.payment_status, "refunded")
        self.assertEqual(client.rows["mentor_consultation_orders"][0]["payment_status"], "refunded")
        notify.assert_called_once()
        self.assertEqual(notify.call_args.kwargs["event"], "refund_completed")
        self.assertEqual(notify.call_args.kwargs["order"]["id"], order["id"])

    def test_refunded_callback_retry_is_idempotent_and_retries_notification_enqueue(self):
        order = _order(payment_status="refunded")
        payload = _payload("refunded")

        with patch.object(mentor_consultation, "_notify_consultation_applicant_payment_status") as notify:
            result, _client = self._call_webhook(order, payload)

        self.assertTrue(result.idempotent)
        self.assertEqual(result.order.payment_status, "refunded")
        notify.assert_called_once()
        self.assertEqual(notify.call_args.kwargs["event"], "refund_completed")

    def test_refund_failed_callback_preserves_reason_in_notification(self):
        order = _order(payment_status="refunding")
        payload = _payload("refund_failed", failure_reason="支付渠道暂时拒绝")

        with patch.object(mentor_consultation, "_notify_consultation_applicant_payment_status") as notify:
            result, client = self._call_webhook(order, payload)

        self.assertFalse(result.idempotent)
        self.assertEqual(result.order.payment_status, "failed")
        self.assertEqual(client.rows["mentor_consultation_orders"][0]["payment_status"], "failed")
        notify.assert_called_once()
        self.assertEqual(notify.call_args.kwargs["event"], "refund_failed")
        self.assertEqual(notify.call_args.kwargs["detail"], "支付渠道暂时拒绝")

    def test_late_payment_requests_refund_notification_even_on_retry(self):
        order = _order(payment_status="unpaid", order_status="pending_payment")
        order["refund_amount_cents"] = 0
        order["refund_reference"] = None
        payload = _payload("paid")
        refreshed = {**order, "order_status": "cancelled", "payment_status": "refunding"}
        late_order = {
            **refreshed,
            "refund_amount_cents": 3900,
            "refund_reference": "LATE-REFUND-001",
        }

        def failed_payment_confirmation(*_args, **_kwargs):
            raise HTTPException(status_code=409, detail="payment hold expired")

        with patch.object(mentor_consultation, "_notify_consultation_applicant_payment_status") as notify:
            result, _client = self._call_webhook(
                order,
                payload,
                _mark_mentor_consultation_order_paid=failed_payment_confirmation,
                _get_order_or_404=lambda *_args, **_kwargs: refreshed,
                _register_late_consultation_payment_for_refund=lambda *_args, **_kwargs: late_order,
            )

        self.assertTrue(result.idempotent)
        self.assertEqual(result.order.payment_status, "refunding")
        notify.assert_called_once()
        self.assertEqual(notify.call_args.kwargs["event"], "refund_requested")
        self.assertEqual(notify.call_args.kwargs["order"]["refund_reference"], "LATE-REFUND-001")

    def test_payment_failed_callback_notifies_with_failure_reason(self):
        order = _order(payment_status="unpaid", order_status="pending_payment")
        order["refund_amount_cents"] = 0
        order["refund_reference"] = None
        payload = _payload("failed", failure_reason="用户取消支付")

        with patch.object(mentor_consultation, "_notify_consultation_applicant_payment_status") as notify:
            result, client = self._call_webhook(order, payload)

        self.assertFalse(result.idempotent)
        self.assertEqual(result.order.payment_status, "failed")
        self.assertEqual(client.rows["mentor_consultation_orders"][0]["payment_status"], "failed")
        notify.assert_called_once()
        self.assertEqual(notify.call_args.kwargs["event"], "payment_failed")
        self.assertEqual(notify.call_args.kwargs["detail"], "用户取消支付")

    def test_notification_write_failure_does_not_change_refund_callback_result(self):
        order = _order(payment_status="refunding")
        payload = _payload("refunded")

        with patch.object(
            mentor_consultation,
            "create_user_notification",
            side_effect=RuntimeError("notification store unavailable"),
        ):
            result, client = self._call_webhook(order, payload)

        self.assertFalse(result.idempotent)
        self.assertEqual(result.detail, "退款确认成功")
        self.assertEqual(result.order.payment_status, "refunded")
        self.assertEqual(client.rows["mentor_consultation_orders"][0]["payment_status"], "refunded")


if __name__ == "__main__":
    unittest.main()
