from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException

from app.routes import mentor_admin


class _Response:
    def __init__(self, data):
        self.data = data


def _application_row(*, consultation_enabled: bool = True, application_status: str = "pending") -> dict:
    return {
        "id": str(uuid4()),
        "applicant_user_id": str(uuid4()),
        "legal_name": "张同学",
        "school": "示例大学",
        "major": "经济学",
        "admission_year": 2025,
        "graduation_year": 2027,
        "exam_type": "Z001",
        "score": 110,
        "skills": ["院校选择"],
        "bio": "经验简介",
        "price_cents": 3900,
        "consultation_enabled": consultation_enabled,
        "application_status": application_status,
        "admin_note": None,
        "reviewed_at": None,
        "created_at": "2026-09-01T08:00:00+00:00",
        "updated_at": "2026-09-01T08:00:00+00:00",
    }


def _profile_change_row(*, request_status: str = "pending") -> dict:
    return {
        "id": str(uuid4()),
        "mentor_id": str(uuid4()),
        "owner_user_id": str(uuid4()),
        "school": "示例大学",
        "major": "经济学",
        "exam_type": "Z001",
        "score": 112,
        "skills": ["院校选择"],
        "bio": "更新后的简介",
        "price_cents": 4900,
        "request_status": request_status,
        "admin_note": None,
        "reviewed_at": None,
        "created_at": "2026-09-01T08:00:00+00:00",
        "updated_at": "2026-09-01T08:00:00+00:00",
    }


class MentorAdminNotificationTests(unittest.TestCase):
    def _decide_application(self, application: dict, *, decision: str, admin_note: str | None = None):
        mentor_id = str(uuid4())
        result_status = "approved" if decision == "approve" else "rejected"

        def fake_call_supabase(_operation, *, operation_name: str):
            if operation_name == "approved mentor profile lookup":
                return _Response([])
            if operation_name == "approved mentor profile create":
                return _Response([{"id": mentor_id}])
            if operation_name == "admin mentor application decision":
                return _Response([{**application, "application_status": result_status, "admin_note": admin_note}])
            self.fail(f"unexpected operation: {operation_name}")

        with (
            patch.object(mentor_admin, "get_supabase_admin", return_value=object()),
            patch.object(mentor_admin, "_get_mentor_application_or_404", return_value=application),
            patch.object(mentor_admin, "call_supabase", side_effect=fake_call_supabase),
            patch.object(mentor_admin, "_replace_mentor_skills"),
            patch.object(mentor_admin, "_log_application_action"),
            patch.object(mentor_admin, "_fetch_application_document_counts", return_value={}),
            patch.object(mentor_admin, "create_user_notification") as create_notification,
        ):
            result = mentor_admin.decide_admin_mentor_verification_application(
                application["id"],
                SimpleNamespace(decision=decision, admin_note=admin_note),
                {"id": str(uuid4())},
            )
        return result, create_notification, mentor_id

    def test_approved_verification_creates_recipient_scoped_official_notification(self):
        application = _application_row()

        result, create_notification, mentor_id = self._decide_application(
            application,
            decision="approve",
            admin_note="材料核验无误",
        )

        self.assertEqual(result.application_status, "approved")
        create_notification.assert_called_once()
        args, kwargs = create_notification.call_args
        self.assertEqual(len(args), 1)
        self.assertEqual(kwargs["recipient_user_id"], application["applicant_user_id"])
        self.assertEqual(kwargs["category"], "official")
        self.assertEqual(kwargs["notification_type"], "mentor_verification_status")
        self.assertEqual(kwargs["title"], "你的前辈认证已通过")
        self.assertIn("材料核验无误", kwargs["content"])
        self.assertEqual(kwargs["related_id"], f"{application['id']}:approved")
        self.assertEqual(
            kwargs["route_path"],
            "/pages-sub-consultation/consultation/mentor-apply?mode=center",
        )
        self.assertEqual(kwargs["delivery_payload"]["mentor_id"], mentor_id)

    def test_rejected_verification_includes_admin_note_and_reapply_route(self):
        application = _application_row()

        result, create_notification, _mentor_id = self._decide_application(
            application,
            decision="reject",
            admin_note="请补充录取证明首页",
        )

        self.assertEqual(result.application_status, "rejected")
        create_notification.assert_called_once()
        kwargs = create_notification.call_args.kwargs
        self.assertEqual(kwargs["title"], "你的前辈认证暂未通过")
        self.assertEqual(kwargs["content"], "审核说明：请补充录取证明首页")
        self.assertEqual(kwargs["related_id"], f"{application['id']}:rejected")
        self.assertEqual(
            kwargs["route_path"],
            "/pages-sub-consultation/consultation/mentor-apply",
        )

    def test_rejected_verification_requires_a_specific_reason(self):
        application = _application_row()

        for admin_note in (None, "", "   ", "太短"):
            with self.subTest(admin_note=admin_note):
                with (
                    patch.object(mentor_admin, "get_supabase_admin", return_value=object()),
                    patch.object(mentor_admin, "_get_mentor_application_or_404", return_value=application),
                    patch.object(mentor_admin, "call_supabase") as call_supabase,
                    self.assertRaises(HTTPException) as raised,
                ):
                    mentor_admin.decide_admin_mentor_verification_application(
                        application["id"],
                        SimpleNamespace(decision="reject", admin_note=admin_note),
                        {"id": str(uuid4())},
                    )

                self.assertEqual(raised.exception.status_code, 422)
                self.assertEqual(raised.exception.detail, "驳回申请时请填写至少 5 个字的理由")
                call_supabase.assert_not_called()

    def test_opted_out_approval_copy_does_not_prompt_consultation_setup(self):
        application = _application_row(consultation_enabled=False)

        _result, create_notification, _mentor_id = self._decide_application(
            application,
            decision="approve",
        )

        kwargs = create_notification.call_args.kwargs
        self.assertIn("未开通前辈咨询服务", kwargs["content"])
        self.assertNotIn("设置预约时段", kwargs["content"])
        self.assertFalse(kwargs["delivery_payload"]["consultation_enabled"])

    def test_processed_application_does_not_create_duplicate_notification(self):
        application = _application_row(application_status="approved")
        with (
            patch.object(mentor_admin, "get_supabase_admin", return_value=object()),
            patch.object(mentor_admin, "_get_mentor_application_or_404", return_value=application),
            patch.object(mentor_admin, "create_user_notification") as create_notification,
            self.assertRaises(HTTPException) as raised,
        ):
            mentor_admin.decide_admin_mentor_verification_application(
                application["id"],
                SimpleNamespace(decision="approve", admin_note=None),
                {"id": str(uuid4())},
            )

        self.assertEqual(raised.exception.status_code, 409)
        create_notification.assert_not_called()

    def test_notification_failure_does_not_change_successful_decision_response(self):
        application = _application_row()

        def fake_call_supabase(_operation, *, operation_name: str):
            if operation_name == "admin mentor application decision":
                return _Response([{**application, "application_status": "rejected"}])
            self.fail(f"unexpected operation: {operation_name}")

        with (
            patch.object(mentor_admin, "get_supabase_admin", return_value=object()),
            patch.object(mentor_admin, "_get_mentor_application_or_404", return_value=application),
            patch.object(mentor_admin, "call_supabase", side_effect=fake_call_supabase),
            patch.object(mentor_admin, "_log_application_action"),
            patch.object(mentor_admin, "_fetch_application_document_counts", return_value={}),
            patch.object(mentor_admin, "create_user_notification", side_effect=RuntimeError("delivery unavailable")),
        ):
            result = mentor_admin.decide_admin_mentor_verification_application(
                application["id"],
                SimpleNamespace(decision="reject", admin_note="申请材料需要补充"),
                {"id": str(uuid4())},
            )

        self.assertEqual(result.application_status, "rejected")

    def test_profile_change_decision_creates_official_notification(self):
        request_row = _profile_change_row()
        resolved = {
            **request_row,
            "request_status": "approved",
            "admin_note": "资料内容清晰",
            "reviewed_at": "2026-09-01T09:00:00+00:00",
        }

        with (
            patch.object(mentor_admin, "get_supabase_admin", return_value=object()),
            patch.object(mentor_admin, "_get_mentor_profile_change_request_or_404", return_value=request_row),
            patch.object(mentor_admin, "call_supabase", return_value=_Response([resolved])),
            patch.object(mentor_admin, "_log_profile_change_request_action"),
            patch.object(mentor_admin, "create_user_notification") as create_notification,
        ):
            result = mentor_admin.decide_admin_mentor_profile_change_request(
                request_row["id"],
                SimpleNamespace(decision="approve", admin_note="资料内容清晰"),
                {"id": str(uuid4())},
            )

        self.assertEqual(result.request_status, "approved")
        create_notification.assert_called_once()
        kwargs = create_notification.call_args.kwargs
        self.assertEqual(kwargs["recipient_user_id"], request_row["owner_user_id"])
        self.assertEqual(kwargs["category"], "official")
        self.assertEqual(kwargs["notification_type"], "mentor_profile_change_status")
        self.assertEqual(kwargs["title"], "你的前辈资料修改已通过")
        self.assertEqual(kwargs["content"], "审核说明：资料内容清晰")
        self.assertEqual(kwargs["related_id"], f"{request_row['id']}:approved")
        self.assertEqual(
            kwargs["route_path"],
            "/pages-sub-consultation/consultation/mentor-info",
        )


if __name__ == "__main__":
    unittest.main()
