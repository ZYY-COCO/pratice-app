from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import UUID, uuid4

from app.routes import mentor_consultation
from app.schemas.mentor_consultation import (
    MentorConsultationReportAppealCreateRequest,
    MentorConsultationReportCreateRequest,
    MentorConsultationReportResponseRequest,
)


class _Response:
    def __init__(self, data, *, count: int | None = None):
        self.data = data
        self.count = len(data) if count is None else count


class _AppealQuery:
    def __init__(self, client, table_name: str):
        self.client = client
        self.table_name = table_name
        self.eq_filters: list[tuple[str, object]] = []
        self.in_filters: list[tuple[str, set[object]]] = []

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, field: str, value: object):
        self.eq_filters.append((field, value))
        return self

    def in_(self, field: str, values):
        self.in_filters.append((field, set(values)))
        return self

    def execute(self):
        rows = [
            row
            for row in self.client.rows.get(self.table_name, [])
            if all(row.get(field) == value for field, value in self.eq_filters)
            and all(row.get(field) in values for field, values in self.in_filters)
        ]
        return _Response(rows)


class _AppealClient:
    def __init__(self, rows: dict[str, list[dict]]):
        self.rows = rows
        self.queries: list[_AppealQuery] = []

    def table(self, table_name: str):
        query = _AppealQuery(self, table_name)
        self.queries.append(query)
        return query


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        mentor_consultation_report_first_response_hours=24,
        mentor_consultation_urgent_report_first_response_hours=4,
        mentor_consultation_report_appeal_first_response_hours=48,
        mentor_consultation_report_sla_warning_hours=2,
    )


def _report_row(
    *,
    status: str = "pending",
    reporter_user_id: str | None = None,
    respondent_user_id: str | None = None,
    reporter_role: str = "applicant",
) -> dict:
    reporter_id = reporter_user_id or str(uuid4())
    respondent_id = respondent_user_id or str(uuid4())
    target_role = "mentor" if reporter_role == "applicant" else "applicant"
    return {
        "id": str(uuid4()),
        "order_id": str(uuid4()),
        "reporter_user_id": reporter_id,
        "reporter_role": reporter_role,
        "respondent_user_id": respondent_id,
        "target_role": target_role,
        "target_user_id": respondent_id,
        "target_mentor_id": str(uuid4()) if target_role == "mentor" else None,
        "issue_type": "其他问题",
        "content": "这是一段至少二十个字的问题反馈说明，用于回归通知闭环。",
        "respondent_content": None,
        "responded_at": None,
        "status": status,
        "resolution": "none",
        "refund_amount_cents": 0,
        "admin_note": None,
        "first_response_due_at": "2026-09-03T08:00:00+00:00",
        "first_response_at": None,
        "priority": "normal",
        "escalation_level": 0,
        "escalated_at": None,
        "created_at": "2026-09-02T08:00:00+00:00",
        "handled_at": None,
    }


def _serialized_report(row: dict, *, user_id: str) -> dict:
    participation_role = (
        "reporter" if str(row.get("reporter_user_id") or "") == user_id else "respondent"
    )
    return {
        "id": str(row.get("id") or ""),
        "order_id": str(row.get("order_id") or ""),
        "reporter_role": str(row.get("reporter_role") or "applicant"),
        "target_role": str(row.get("target_role") or "mentor"),
        "issue_type": str(row.get("issue_type") or "其他问题"),
        "content": str(row.get("content") or ""),
        "respondent_content": row.get("respondent_content"),
        "responded_at": row.get("responded_at"),
        "participation_role": participation_role,
        "can_respond": participation_role == "respondent" and row.get("status") in {"pending", "reviewing"},
        "status": str(row.get("status") or "pending"),
        "resolution": str(row.get("resolution") or "none"),
        "created_at": row.get("created_at"),
    }


def _appeal_row(report: dict, *, appellant_user_id: str, appellant_role: str) -> dict:
    return {
        "id": str(uuid4()),
        "report_id": report["id"],
        "appellant_user_id": appellant_user_id,
        "appellant_role": appellant_role,
        "content": "申请重新核实本次处理结果，并补充相关事实说明。",
        "status": "pending",
        "decision": "none",
        "admin_note": None,
        "first_response_due_at": "2026-09-04T08:00:00+00:00",
        "first_response_at": None,
        "priority": "normal",
        "escalation_level": 0,
        "escalated_at": None,
        "created_at": "2026-09-02T09:00:00+00:00",
        "handled_at": None,
    }


def _serialized_appeal(row: dict) -> dict:
    return {
        "id": row["id"],
        "report_id": row["report_id"],
        "appellant_role": row["appellant_role"],
        "content": row["content"],
        "status": row["status"],
        "decision": row["decision"],
        "created_at": row.get("created_at"),
    }


class MentorConsultationReportParticipantNotificationTests(unittest.TestCase):
    def _create_report(self, report: dict, *, notification_error: Exception | None = None):
        mentor_id = str(report.get("target_mentor_id") or uuid4())
        reporter_is_applicant = report["reporter_role"] == "applicant"
        order = {
            "id": report["order_id"],
            "applicant_user_id": (
                report["reporter_user_id"]
                if reporter_is_applicant
                else report["respondent_user_id"]
            ),
            "mentor_id": mentor_id,
        }
        mentor = {
            "id": mentor_id,
            "owner_user_id": (
                report["respondent_user_id"]
                if reporter_is_applicant
                else report["reporter_user_id"]
            ),
        }

        def fake_call_supabase(_operation, *, operation_name: str):
            if operation_name == "consultation report duplicate lookup":
                return _Response([])
            if operation_name == "consultation report create":
                return _Response([report])
            self.fail(f"unexpected operation: {operation_name}")

        with (
            patch.object(mentor_consultation, "get_supabase_admin", return_value=object()),
            patch.object(
                mentor_consultation,
                "_get_order_participant",
                return_value=(order, report["reporter_role"], mentor),
            ),
            patch.object(mentor_consultation, "call_supabase", side_effect=fake_call_supabase),
            patch.object(mentor_consultation, "get_settings", return_value=_settings()),
            patch.object(mentor_consultation, "_insert_order_event"),
            patch.object(mentor_consultation, "_insert_system_message"),
            patch.object(
                mentor_consultation,
                "_serialize_consultation_report",
                side_effect=lambda row, **_kwargs: _serialized_report(
                    row,
                    user_id=report["reporter_user_id"],
                ),
            ),
            patch.object(
                mentor_consultation,
                "create_user_notification",
                side_effect=notification_error,
            ) as create_notification,
        ):
            result = mentor_consultation.create_mentor_consultation_report(
                UUID(report["order_id"]),
                MentorConsultationReportCreateRequest(
                    issue_type="其他问题",
                    content=report["content"],
                ),
                user_id=report["reporter_user_id"],
            )
        return result, create_notification

    def _respond_to_report(self, report: dict, *, notification_error: Exception | None = None):
        updated = {
            **report,
            "respondent_content": "被反馈方已提交一段至少二十个字的事实说明与处理回应。",
            "responded_at": "2026-09-02T09:30:00+00:00",
        }

        def fake_call_supabase(_operation, *, operation_name: str):
            if operation_name == "consultation report respondent response":
                return _Response([updated])
            self.fail(f"unexpected operation: {operation_name}")

        with (
            patch.object(mentor_consultation, "get_supabase_admin", return_value=object()),
            patch.object(
                mentor_consultation,
                "_get_participant_consultation_report_or_404",
                return_value=(report, "respondent"),
            ),
            patch.object(mentor_consultation, "call_supabase", side_effect=fake_call_supabase),
            patch.object(mentor_consultation, "_insert_order_event"),
            patch.object(mentor_consultation, "_insert_system_message"),
            patch.object(mentor_consultation, "_fetch_consultation_report_evidence_summary", return_value={}),
            patch.object(
                mentor_consultation,
                "_serialize_consultation_report",
                side_effect=lambda row, **_kwargs: _serialized_report(
                    row,
                    user_id=report["respondent_user_id"],
                ),
            ),
            patch.object(
                mentor_consultation,
                "create_user_notification",
                side_effect=notification_error,
            ) as create_notification,
        ):
            result = mentor_consultation.respond_to_mentor_consultation_report(
                UUID(report["id"]),
                MentorConsultationReportResponseRequest(content=updated["respondent_content"]),
                user_id=report["respondent_user_id"],
            )
        return result, create_notification

    def _create_appeal(
        self,
        report: dict,
        *,
        participation_role: str,
        notification_error: Exception | None = None,
    ):
        user_id = (
            report["reporter_user_id"]
            if participation_role == "reporter"
            else report["respondent_user_id"]
        )
        appeal = _appeal_row(
            report,
            appellant_user_id=user_id,
            appellant_role=participation_role,
        )

        def fake_call_supabase(_operation, *, operation_name: str):
            if operation_name == "consultation report appeal duplicate lookup":
                return _Response([])
            if operation_name == "consultation report appeal create":
                return _Response([appeal])
            self.fail(f"unexpected operation: {operation_name}")

        with (
            patch.object(mentor_consultation, "get_supabase_admin", return_value=object()),
            patch.object(
                mentor_consultation,
                "_get_participant_consultation_report_or_404",
                return_value=(report, participation_role),
            ),
            patch.object(mentor_consultation, "call_supabase", side_effect=fake_call_supabase),
            patch.object(mentor_consultation, "get_settings", return_value=_settings()),
            patch.object(mentor_consultation, "_insert_order_event"),
            patch.object(mentor_consultation, "_insert_system_message"),
            patch.object(
                mentor_consultation,
                "_serialize_consultation_report_appeal",
                side_effect=lambda row: _serialized_appeal(row),
            ),
            patch.object(
                mentor_consultation,
                "create_user_notification",
                side_effect=notification_error,
            ) as create_notification,
        ):
            result = mentor_consultation.create_mentor_consultation_report_appeal(
                UUID(report["id"]),
                MentorConsultationReportAppealCreateRequest(content=appeal["content"]),
                user_id=user_id,
            )
        return result, create_notification, appeal

    def test_report_creation_notifies_the_respondent_with_stable_payload(self):
        report = _report_row()

        result, create_notification = self._create_report(report)

        self.assertEqual(result.id, report["id"])
        create_notification.assert_called_once()
        kwargs = create_notification.call_args.kwargs
        self.assertEqual(kwargs["recipient_user_id"], report["respondent_user_id"])
        self.assertEqual(kwargs["category"], "consultation")
        self.assertEqual(kwargs["notification_type"], "mentor_report_status")
        self.assertEqual(kwargs["related_type"], "mentor_consultation_report")
        self.assertEqual(kwargs["related_id"], f"{report['id']}:created:respondent")
        self.assertEqual(
            kwargs["route_path"],
            f"/pages-sub-consultation/consultation/mentor-response?reportId={report['id']}",
        )
        self.assertEqual(kwargs["delivery_payload"]["audience"], "mentor")
        self.assertEqual(kwargs["delivery_payload"]["participation_role"], "respondent")
        self.assertEqual(kwargs["delivery_payload"]["event"], "created")
        self.assertEqual(kwargs["delivery_payload"]["order_id"], report["order_id"])
        self.assertEqual(kwargs["delivery_payload"]["report_id"], report["id"])
        self.assertIsNone(kwargs["delivery_payload"]["appeal_id"])

    def test_respondent_response_notifies_the_original_reporter(self):
        report = _report_row()

        result, create_notification = self._respond_to_report(report)

        self.assertEqual(result.id, report["id"])
        create_notification.assert_called_once()
        kwargs = create_notification.call_args.kwargs
        self.assertEqual(kwargs["recipient_user_id"], report["reporter_user_id"])
        self.assertEqual(kwargs["notification_type"], "mentor_report_status")
        self.assertEqual(kwargs["related_id"], f"{report['id']}:responded:reporter")
        self.assertEqual(
            kwargs["route_path"],
            "/pages-sub-consultation/consultation/mentor-support",
        )
        self.assertEqual(kwargs["delivery_payload"]["audience"], "applicant")
        self.assertEqual(kwargs["delivery_payload"]["participation_role"], "reporter")
        self.assertEqual(kwargs["delivery_payload"]["event"], "responded")

    def test_reverse_roles_map_applicant_target_and_mentor_reporter(self):
        created_report = _report_row(reporter_role="mentor")
        responded_report = _report_row(reporter_role="mentor")

        created, created_notification = self._create_report(created_report)
        responded, responded_notification = self._respond_to_report(responded_report)

        self.assertEqual(created.id, created_report["id"])
        created_kwargs = created_notification.call_args.kwargs
        self.assertEqual(created_kwargs["recipient_user_id"], created_report["respondent_user_id"])
        self.assertEqual(created_kwargs["delivery_payload"]["audience"], "applicant")
        self.assertEqual(created_kwargs["delivery_payload"]["participation_role"], "respondent")

        self.assertEqual(responded.id, responded_report["id"])
        responded_kwargs = responded_notification.call_args.kwargs
        self.assertEqual(responded_kwargs["recipient_user_id"], responded_report["reporter_user_id"])
        self.assertEqual(responded_kwargs["delivery_payload"]["audience"], "mentor")
        self.assertEqual(responded_kwargs["delivery_payload"]["participation_role"], "reporter")

    def test_reporter_appeal_notifies_the_respondent(self):
        report = _report_row(status="resolved")

        result, create_notification, appeal = self._create_appeal(
            report,
            participation_role="reporter",
        )

        self.assertEqual(result.id, appeal["id"])
        create_notification.assert_called_once()
        kwargs = create_notification.call_args.kwargs
        self.assertEqual(kwargs["recipient_user_id"], report["respondent_user_id"])
        self.assertEqual(kwargs["notification_type"], "mentor_report_appeal_status")
        self.assertEqual(kwargs["related_type"], "mentor_consultation_report_appeal")
        self.assertEqual(kwargs["related_id"], f"{appeal['id']}:created:counterparty")
        self.assertEqual(kwargs["route_path"], "/pages/circle/community-reports")
        self.assertEqual(kwargs["delivery_payload"]["audience"], "mentor")
        self.assertEqual(kwargs["delivery_payload"]["participation_role"], "respondent")
        self.assertEqual(kwargs["delivery_payload"]["event"], "appeal_created")
        self.assertEqual(kwargs["delivery_payload"]["appeal_id"], appeal["id"])

    def test_respondent_appeal_notifies_the_reporter(self):
        report = _report_row(status="dismissed")

        result, create_notification, appeal = self._create_appeal(
            report,
            participation_role="respondent",
        )

        self.assertEqual(result.id, appeal["id"])
        create_notification.assert_called_once()
        kwargs = create_notification.call_args.kwargs
        self.assertEqual(kwargs["recipient_user_id"], report["reporter_user_id"])
        self.assertEqual(kwargs["related_id"], f"{appeal['id']}:created:counterparty")
        self.assertEqual(kwargs["delivery_payload"]["audience"], "applicant")
        self.assertEqual(kwargs["delivery_payload"]["participation_role"], "reporter")

    def test_all_report_events_skip_self_notification(self):
        report = _report_row(status="resolved")
        actor_user_id = report["reporter_user_id"]
        cases = (
            {
                "event": "created",
                "audience": "mentor",
                "participation_role": "respondent",
                "appeal_id": None,
            },
            {
                "event": "responded",
                "audience": "applicant",
                "participation_role": "reporter",
                "appeal_id": None,
            },
            {
                "event": "appeal_created",
                "audience": "mentor",
                "participation_role": "respondent",
                "appeal_id": str(uuid4()),
            },
        )

        with patch.object(mentor_consultation, "create_user_notification") as create_notification:
            for case in cases:
                with self.subTest(event=case["event"]):
                    mentor_consultation._notify_consultation_report_participant(
                        object(),
                        report=report,
                        recipient_user_id=actor_user_id,
                        audience=case["audience"],
                        participation_role=case["participation_role"],
                        event=case["event"],
                        actor_user_id=actor_user_id,
                        appeal_id=case["appeal_id"],
                    )

        create_notification.assert_not_called()

    def test_notification_failure_does_not_change_any_successful_case_response(self):
        delivery_error = RuntimeError("notification store unavailable")
        created_report = _report_row()
        responded_report = _report_row()
        appealed_report = _report_row(status="resolved")

        created, _created_notification = self._create_report(
            created_report,
            notification_error=delivery_error,
        )
        responded, _responded_notification = self._respond_to_report(
            responded_report,
            notification_error=delivery_error,
        )
        appealed, _appeal_notification, appeal = self._create_appeal(
            appealed_report,
            participation_role="reporter",
            notification_error=delivery_error,
        )

        self.assertEqual(created.id, created_report["id"])
        self.assertEqual(responded.id, responded_report["id"])
        self.assertEqual(appealed.id, appeal["id"])

    def test_embedded_appeal_summary_remains_scoped_to_the_current_appellant(self):
        report = _report_row(status="resolved")
        own_user_id = report["respondent_user_id"]
        other_appeal = _appeal_row(
            report,
            appellant_user_id=report["reporter_user_id"],
            appellant_role="reporter",
        )
        own_appeal = _appeal_row(
            report,
            appellant_user_id=own_user_id,
            appellant_role="respondent",
        )
        client = _AppealClient({
            "mentor_consultation_report_appeals": [other_appeal, own_appeal],
            "mentor_consultation_report_appeal_evidence": [],
        })

        with patch.object(
            mentor_consultation,
            "call_supabase",
            side_effect=lambda operation, **_kwargs: operation(),
        ):
            summary = mentor_consultation._fetch_consultation_report_appeal_summary(
                client,
                [report["id"]],
                own_user_id,
            )

        self.assertEqual(summary[report["id"]]["id"], own_appeal["id"])
        appeal_query = next(
            query
            for query in client.queries
            if query.table_name == "mentor_consultation_report_appeals"
        )
        self.assertIn(("appellant_user_id", own_user_id), appeal_query.eq_filters)


if __name__ == "__main__":
    unittest.main()
