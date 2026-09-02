from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import ANY, patch

from app.routes import mentor_admin


class _Response:
    def __init__(self, data):
        self.data = data


def _report_row(**overrides) -> dict:
    row = {
        "id": "report-1",
        "order_id": "order-1",
        "reporter_user_id": "applicant-user",
        "reporter_role": "applicant",
        "respondent_user_id": "mentor-user",
        "target_user_id": "mentor-user",
        "target_role": "mentor",
        "target_mentor_id": "mentor-1",
        "status": "reviewing",
        "resolution": "none",
        "priority": "normal",
        "escalation_level": 0,
        "first_response_at": None,
    }
    row.update(overrides)
    return row


def _appeal_row(**overrides) -> dict:
    row = {
        "id": "appeal-1",
        "report_id": "report-1",
        "appellant_user_id": "mentor-user",
        "appellant_role": "respondent",
        "status": "reviewing",
        "decision": "none",
        "priority": "normal",
        "escalation_level": 0,
        "first_response_at": None,
    }
    row.update(overrides)
    return row


def _order_row(**overrides) -> dict:
    row = {
        "id": "order-1",
        "order_no": "M202609020001",
        "applicant_user_id": "applicant-user",
        "mentor_id": "mentor-1",
        "consultation_type": "instant",
        "order_status": "in_progress",
        "payment_status": "paid",
        "price_cents": 3900,
        "slot_id": None,
    }
    row.update(overrides)
    return row


class MentorAdminParticipantNotificationTests(unittest.TestCase):
    def test_report_status_notifies_reporter_and_respondent_with_stable_targets(self):
        report = _report_row(status="resolved", resolution="warn_participant")

        with patch.object(mentor_admin, "create_user_notification") as create_notification:
            mentor_admin._notify_consultation_report_participants(
                object(),
                report=report,
                status_value="resolved",
                resolution="warn_participant",
                admin_note="平台已完成核实",
            )

        self.assertEqual(create_notification.call_count, 2)
        calls = {
            call.kwargs["delivery_payload"]["participant_role"]: call.kwargs
            for call in create_notification.call_args_list
        }
        self.assertEqual(set(calls), {"reporter", "respondent"})
        self.assertEqual(calls["reporter"]["recipient_user_id"], "applicant-user")
        self.assertEqual(calls["reporter"]["delivery_payload"]["audience"], "applicant")
        self.assertEqual(calls["respondent"]["recipient_user_id"], "mentor-user")
        self.assertEqual(calls["respondent"]["delivery_payload"]["audience"], "mentor")
        for audience, kwargs in (("applicant", calls["reporter"]), ("mentor", calls["respondent"])):
            self.assertEqual(kwargs["category"], "official")
            self.assertEqual(kwargs["notification_type"], "mentor_report_status")
            self.assertEqual(kwargs["related_type"], "mentor_consultation_report")
            self.assertEqual(
                kwargs["related_id"],
                f"report-1:report_status:resolved:warn_participant:{audience}",
            )
            self.assertEqual(kwargs["delivery_payload"]["order_id"], "order-1")
            self.assertEqual(kwargs["delivery_payload"]["report_id"], "report-1")

    def test_report_status_deduplicates_same_recipient(self):
        report = _report_row(respondent_user_id="applicant-user", target_user_id="applicant-user")

        with patch.object(mentor_admin, "create_user_notification") as create_notification:
            mentor_admin._notify_consultation_report_participants(
                object(),
                report=report,
                status_value="reviewing",
                resolution="none",
                admin_note=None,
            )

        create_notification.assert_called_once()
        self.assertEqual(create_notification.call_args.kwargs["recipient_user_id"], "applicant-user")

    def test_report_status_preserves_reversed_mentor_and_applicant_audiences(self):
        report = _report_row(
            reporter_user_id="mentor-user",
            reporter_role="mentor",
            respondent_user_id="applicant-user",
            target_user_id="applicant-user",
            target_role="applicant",
        )

        with patch.object(mentor_admin, "create_user_notification") as create_notification:
            mentor_admin._notify_consultation_report_participants(
                object(),
                report=report,
                status_value="reviewing",
                resolution="none",
                admin_note=None,
            )

        self.assertEqual(create_notification.call_count, 2)
        calls = {
            call.kwargs["delivery_payload"]["participant_role"]: call.kwargs
            for call in create_notification.call_args_list
        }
        self.assertEqual(calls["reporter"]["recipient_user_id"], "mentor-user")
        self.assertEqual(calls["reporter"]["delivery_payload"]["audience"], "mentor")
        self.assertEqual(calls["respondent"]["recipient_user_id"], "applicant-user")
        self.assertEqual(calls["respondent"]["delivery_payload"]["audience"], "applicant")
        self.assertTrue(calls["reporter"]["related_id"].endswith(":mentor"))
        self.assertTrue(calls["respondent"]["related_id"].endswith(":applicant"))

    def test_appeal_status_notifies_appellant_and_other_affected_party(self):
        report = _report_row()
        appeal = _appeal_row(status="dismissed", decision="uphold")

        with patch.object(mentor_admin, "create_user_notification") as create_notification:
            mentor_admin._notify_consultation_report_appeal_participants(
                object(),
                appeal=appeal,
                report=report,
                status_value="dismissed",
                decision="uphold",
                admin_note="维持原处理结论",
            )

        self.assertEqual(create_notification.call_count, 2)
        calls = {
            call.kwargs["delivery_payload"]["participant_role"]: call.kwargs
            for call in create_notification.call_args_list
        }
        self.assertEqual(calls["appellant"]["recipient_user_id"], "mentor-user")
        self.assertEqual(calls["appellant"]["delivery_payload"]["audience"], "mentor")
        self.assertEqual(calls["affected_party"]["recipient_user_id"], "applicant-user")
        self.assertEqual(calls["affected_party"]["delivery_payload"]["audience"], "applicant")
        for audience, kwargs in (("mentor", calls["appellant"]), ("applicant", calls["affected_party"])):
            self.assertEqual(kwargs["category"], "official")
            self.assertEqual(kwargs["notification_type"], "mentor_report_appeal_status")
            self.assertEqual(
                kwargs["related_id"],
                f"appeal-1:appeal_status:dismissed:uphold:{audience}",
            )
            self.assertEqual(kwargs["delivery_payload"]["order_id"], "order-1")
            self.assertEqual(kwargs["delivery_payload"]["report_id"], "report-1")
            self.assertEqual(kwargs["delivery_payload"]["appeal_id"], "appeal-1")

    def test_one_notification_failure_does_not_block_other_participant(self):
        with patch.object(
            mentor_admin,
            "create_user_notification",
            side_effect=[RuntimeError("outbox unavailable"), None],
        ) as create_notification:
            mentor_admin._notify_consultation_report_participants(
                object(),
                report=_report_row(),
                status_value="reviewing",
                resolution="none",
                admin_note=None,
            )

        self.assertEqual(create_notification.call_count, 2)

    def test_notify_participants_action_writes_order_notifications_for_both_sides(self):
        order = _order_row()
        mentor = {"id": "mentor-1", "owner_user_id": "mentor-user"}

        with (
            patch.object(mentor_admin, "get_supabase_admin", return_value=object()),
            patch.object(mentor_admin, "_get_consultation_order_or_404", return_value=order),
            patch.object(mentor_admin, "_refresh_pending_accept_status", return_value=order),
            patch.object(mentor_admin, "_insert_consultation_admin_system_message"),
            patch.object(mentor_admin, "_insert_consultation_admin_event"),
            patch.object(mentor_admin, "_log_consultation_order_action"),
            patch.object(mentor_admin, "_fetch_consultation_order_reports", return_value=[]),
            patch.object(mentor_admin, "_fetch_application_users", return_value={}),
            patch.object(mentor_admin, "_fetch_report_mentors", return_value={"mentor-1": mentor}),
            patch.object(mentor_admin, "_fetch_consultation_order_slots", return_value={}),
            patch.object(mentor_admin, "_summarize_consultation_order_reports", return_value={}),
            patch.object(mentor_admin, "_serialize_admin_consultation_order", return_value={"id": "order-1"}),
            patch.object(mentor_admin, "AdminMentorConsultationOrderItem", side_effect=lambda **kwargs: kwargs),
            patch.object(mentor_admin, "create_user_notification") as create_notification,
        ):
            result = mentor_admin.intervene_admin_mentor_consultation_order(
                "order-1",
                SimpleNamespace(
                    action="notify_participants",
                    admin_note="请双方继续在站内沟通",
                    refund_amount=0,
                ),
                {"id": "admin-1"},
            )

        self.assertEqual(result, {"id": "order-1"})
        self.assertEqual(create_notification.call_count, 2)
        calls = {
            call.kwargs["delivery_payload"]["audience"]: call.kwargs
            for call in create_notification.call_args_list
        }
        self.assertEqual(set(calls), {"applicant", "mentor"})
        for audience, kwargs in calls.items():
            self.assertEqual(kwargs["category"], "official")
            self.assertEqual(kwargs["notification_type"], "mentor_order_status")
            self.assertEqual(kwargs["delivery_payload"]["order_id"], "order-1")
            self.assertIn(f":{audience}", kwargs["related_id"])

    def test_report_endpoint_wires_updated_row_to_participant_notifier(self):
        report = _report_row(status="pending")
        updated = _report_row(status="reviewing", admin_note="核实中")

        with (
            patch.object(mentor_admin, "get_supabase_admin", return_value=object()),
            patch.object(mentor_admin, "_get_consultation_report_or_404", return_value=report),
            patch.object(mentor_admin, "_fetch_report_orders", return_value={"order-1": _order_row()}),
            patch.object(mentor_admin, "call_supabase", return_value=_Response([updated])),
            patch.object(mentor_admin, "_notify_consultation_report_participants") as notify_participants,
            patch.object(mentor_admin, "_insert_consultation_admin_system_message"),
            patch.object(mentor_admin, "_insert_consultation_admin_event"),
            patch.object(mentor_admin, "_fetch_application_users", return_value={}),
            patch.object(mentor_admin, "_fetch_report_mentors", return_value={}),
            patch.object(mentor_admin, "_fetch_report_evidence_counts", return_value={}),
            patch.object(mentor_admin, "_fetch_report_evidence_role_counts", return_value={}),
            patch.object(mentor_admin, "_log_consultation_report_action"),
            patch.object(mentor_admin, "_serialize_admin_consultation_report", return_value={"id": "report-1"}),
            patch.object(mentor_admin, "AdminMentorConsultationReportItem", side_effect=lambda **kwargs: kwargs),
        ):
            result = mentor_admin.update_admin_mentor_consultation_report_status(
                "report-1",
                SimpleNamespace(
                    status="reviewing",
                    resolution="none",
                    refund_amount=0,
                    admin_note="核实中",
                    priority=None,
                ),
                {"id": "admin-1"},
            )

        self.assertEqual(result, {"id": "report-1"})
        notify_participants.assert_called_once_with(
            ANY,
            report=updated,
            status_value="reviewing",
            resolution="none",
            admin_note="核实中",
        )

    def test_appeal_endpoint_wires_updated_row_and_original_parties(self):
        appeal = _appeal_row(status="pending")
        updated = _appeal_row(status="reviewing", admin_note="复核中")
        report = _report_row(status="resolved")

        with (
            patch.object(mentor_admin, "get_supabase_admin", return_value=object()),
            patch.object(mentor_admin, "_get_consultation_report_appeal_or_404", return_value=appeal),
            patch.object(mentor_admin, "_get_consultation_report_or_404", return_value=report),
            patch.object(mentor_admin, "call_supabase", return_value=_Response([updated])),
            patch.object(mentor_admin, "_notify_consultation_report_appeal_participants") as notify_participants,
            patch.object(mentor_admin, "_insert_consultation_admin_system_message"),
            patch.object(mentor_admin, "_insert_consultation_admin_event"),
            patch.object(mentor_admin, "_fetch_application_users", return_value={}),
            patch.object(mentor_admin, "_fetch_report_mentors", return_value={}),
            patch.object(mentor_admin, "_fetch_report_orders", return_value={}),
            patch.object(mentor_admin, "_fetch_report_appeal_evidence_counts", return_value={}),
            patch.object(mentor_admin, "_log_consultation_report_appeal_action"),
            patch.object(mentor_admin, "_serialize_admin_consultation_report_appeal", return_value={"id": "appeal-1"}),
            patch.object(mentor_admin, "AdminMentorConsultationReportAppealItem", side_effect=lambda **kwargs: kwargs),
        ):
            result = mentor_admin.update_admin_mentor_consultation_report_appeal_status(
                "appeal-1",
                SimpleNamespace(
                    status="reviewing",
                    decision="none",
                    admin_note="复核中",
                    priority=None,
                ),
                {"id": "admin-1"},
            )

        self.assertEqual(result, {"id": "appeal-1"})
        notify_participants.assert_called_once_with(
            ANY,
            appeal=updated,
            report=report,
            status_value="reviewing",
            decision="none",
            admin_note="复核中",
        )


if __name__ == "__main__":
    unittest.main()
