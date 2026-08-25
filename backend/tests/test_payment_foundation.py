from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException

from app.routes import mentor_consultation, wallet
from app.schemas.mentor_consultation import MentorConsultationMessageCreateRequest
from app.services.user_notifications import create_user_notification
from app.services.wallet_ledger import consultation_fund_mode


class _Response:
    def __init__(self, data):
        self.data = data


class _MessageQuery:
    def __init__(self, client, action="select", payload=None):
        self.client = client
        self.action = action
        self.payload = payload

    def select(self, *_args, **_kwargs):
        self.action = "select"
        return self

    def insert(self, payload):
        self.action = "insert"
        self.payload = payload
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        if self.action == "select":
            return _Response(self.client.existing)
        self.client.inserted.append(self.payload)
        return _Response([self.client.saved])


class _MessageClient:
    def __init__(self, *, existing=None, saved=None):
        self.existing = existing or []
        self.saved = saved or {}
        self.inserted = []

    def table(self, _name):
        return _MessageQuery(self)


class _StoreQuery:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.action = "select"
        self.payload = None
        self.filters = []

    def select(self, *_args, **_kwargs):
        self.action = "select"
        return self

    def insert(self, payload):
        self.action = "insert"
        self.payload = payload
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        rows = self.client.rows.setdefault(self.table_name, [])
        if self.action == "insert":
            saved = {"id": f"row-{len(rows) + 1}", **self.payload}
            rows.append(saved)
            return _Response([saved])
        matches = [
            row for row in rows
            if all(row.get(field) == value for field, value in self.filters)
        ]
        return _Response(matches)


class _StoreClient:
    def __init__(self):
        self.rows = {}

    def table(self, table_name):
        return _StoreQuery(self, table_name)


class PaymentFoundationTests(unittest.TestCase):
    def test_order_fingerprint_is_stable_and_content_sensitive(self):
        kwargs = {
            "mentor_id": str(uuid4()),
            "consultation_type": "booking",
            "slot_id": str(uuid4()),
            "questionnaire": {
                "name": "张同学",
                "school": "示例大学",
                "major": "经济学",
                "grade": "大四",
                "graduation_year": 2027,
                "question": "如何准备复试？",
            },
            "service_rules_version": "2026-08-23",
        }
        first = mentor_consultation._order_request_fingerprint(**kwargs)
        second = mentor_consultation._order_request_fingerprint(**kwargs)
        changed = mentor_consultation._order_request_fingerprint(
            **{**kwargs, "questionnaire": {**kwargs["questionnaire"], "question": "如何准备初试？"}}
        )
        self.assertEqual(first, second)
        self.assertNotEqual(first, changed)

    def test_fund_mode_never_mixes_demo_and_real(self):
        self.assertEqual(consultation_fund_mode({"payment_mode": "demo"}), "demo")
        self.assertEqual(consultation_fund_mode({"payment_mode": "real", "payment_reference": "DEMO-X"}), "real")
        self.assertEqual(consultation_fund_mode({"payment_reference": "DEMO-X"}), "demo")

    def test_message_retry_returns_original_even_after_order_closed(self):
        user_id = str(uuid4())
        order_id = uuid4()
        existing = {
            "id": str(uuid4()),
            "order_id": str(order_id),
            "sender_role": "applicant",
            "sender_user_id": user_id,
            "message_type": "text",
            "content": "同一条消息",
            "duration_seconds": None,
            "client_message_id": "client-1",
            "created_at": "2026-08-24T08:00:00+00:00",
        }
        client = _MessageClient(existing=[existing])
        with (
            patch.object(mentor_consultation, "get_supabase_admin", return_value=client),
            patch.object(
                mentor_consultation,
                "_get_order_participant",
                return_value=({"order_status": "completed"}, "applicant", {}),
            ),
        ):
            result = mentor_consultation.create_mentor_consultation_message(
                order_id=order_id,
                payload=MentorConsultationMessageCreateRequest(
                    content="同一条消息",
                    client_message_id="client-1",
                ),
                user_id=user_id,
            )
        self.assertEqual(result.id, existing["id"])
        self.assertEqual(client.inserted, [])

    def test_message_key_reuse_with_different_content_is_conflict(self):
        user_id = str(uuid4())
        order_id = uuid4()
        existing = {
            "id": str(uuid4()),
            "order_id": str(order_id),
            "sender_role": "applicant",
            "sender_user_id": user_id,
            "message_type": "text",
            "content": "原正文",
            "duration_seconds": None,
            "client_message_id": "client-2",
            "created_at": "2026-08-24T08:00:00+00:00",
        }
        client = _MessageClient(existing=[existing])
        with (
            patch.object(mentor_consultation, "get_supabase_admin", return_value=client),
            patch.object(
                mentor_consultation,
                "_get_order_participant",
                return_value=({"order_status": "in_progress"}, "applicant", {}),
            ),
        ):
            with self.assertRaises(HTTPException) as raised:
                mentor_consultation.create_mentor_consultation_message(
                    order_id=order_id,
                    payload=MentorConsultationMessageCreateRequest(
                        content="篡改后的正文",
                        client_message_id="client-2",
                    ),
                    user_id=user_id,
                )
        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(client.inserted, [])

    def test_wallet_projection_hides_participant_internal_ids(self):
        item = wallet._activity_to_item({
            "id": str(uuid4()),
            "transaction_no": "WTX-TEST",
            "business_type": "consultation_payment",
            "fund_mode": "real",
            "display_amount_cents": -3900,
            "description": "咨询订单支付确认",
            "occurred_at": "2026-08-24T08:00:00+00:00",
            "metadata": {
                "applicant_user_id": str(uuid4()),
                "mentor_owner_user_id": str(uuid4()),
                "order_no": "M202608240001",
                "mentor_display_name": "钟*宏",
            },
        })
        self.assertEqual(item.amount, -39)
        self.assertEqual(item.metadata["order_no"], "M202608240001")
        self.assertNotIn("applicant_user_id", item.metadata)
        self.assertNotIn("mentor_owner_user_id", item.metadata)

    def test_notification_source_enqueues_outbox_once(self):
        client = _StoreClient()
        recipient_id = str(uuid4())
        kwargs = {
            "recipient_user_id": recipient_id,
            "category": "consultation",
            "notification_type": "mentor_order_status",
            "title": "咨询状态更新",
            "summary": "前辈已接单",
            "related_type": "mentor_consultation_order",
            "related_id": "order-1:accepted",
            "route_path": "/pages/circle/my-consultations",
        }
        create_user_notification(client, **kwargs)
        create_user_notification(client, **kwargs)
        self.assertEqual(len(client.rows.get("user_notification_outbox", [])), 1)
        self.assertEqual(client.rows.get("user_notifications", []), [])

    def test_production_capability_stays_closed_without_real_provider(self):
        settings = SimpleNamespace(
            mentor_consultation_demo_payment_enabled=False,
            mentor_consultation_real_payment_enabled=False,
            mentor_consultation_payment_provider="unconfigured",
            mentor_consultation_payment_checkout_url=None,
            payment_webhook_secret=None,
            wallet_withdrawal_enabled=False,
            mentor_consultation_service_rules_version="2026-08-23",
        )
        with patch.object(mentor_consultation, "get_settings", return_value=settings):
            capability = mentor_consultation.get_mentor_consultation_payment_capability()
            with self.assertRaises(HTTPException) as raised:
                mentor_consultation._assert_order_creation_enabled()
        self.assertFalse(capability.order_creation_enabled)
        self.assertFalse(capability.real_payment_enabled)
        self.assertFalse(capability.withdrawal_enabled)
        self.assertEqual(capability.payment_mode, "disabled")
        self.assertEqual(raised.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
