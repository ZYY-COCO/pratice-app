from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException
from pydantic import ValidationError

from app.routes import community, mentor_admin, mentor_consultation
from app.schemas.mentor_consultation import (
    AdminMentorProfileCreateRequest,
    AdminMentorProfileUpdateRequest,
    MentorOwnerAvailabilitySlotCreateRequest,
    MentorOwnerAvailabilitySlotStatusUpdateRequest,
    MentorOwnerAvailabilityUpdateRequest,
    MentorProfileChangeRequestCreateRequest,
    MentorPublicItem,
    MentorVerificationApplicationCreateRequest,
)


TEST_APPLICATION_PHONE = "12345678901"


class _Response:
    def __init__(self, data, *, count=None):
        self.data = data
        self.count = len(data) if count is None else count


class _Query:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.action = "select"
        self.payload = None
        self.filters: list[tuple[str, object]] = []
        self.in_filters: list[tuple[str, set[object]]] = []
        self.limit_value: int | None = None
        self.range_value: tuple[int, int] | None = None

    def select(self, *_args, **_kwargs):
        return self

    def insert(self, payload):
        self.action = "insert"
        self.payload = payload
        return self

    def update(self, payload):
        self.action = "update"
        self.payload = payload
        return self

    def delete(self):
        self.action = "delete"
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def in_(self, field, values):
        self.in_filters.append((field, set(values)))
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def range(self, start, end):
        self.range_value = (start, end)
        return self

    def execute(self):
        rows = self.client.rows.setdefault(self.table_name, [])
        self.client.queries.append(self)
        if self.action == "insert":
            payloads = self.payload if isinstance(self.payload, list) else [self.payload]
            inserted = []
            for payload in payloads:
                row = {"id": str(uuid4()), **dict(payload)}
                rows.append(row)
                inserted.append(row)
            return _Response(inserted)

        matched = [
            row
            for row in rows
            if all(row.get(field) == value for field, value in self.filters)
            and all(row.get(field) in values for field, values in self.in_filters)
        ]
        if self.action == "update":
            for row in matched:
                row.update(self.payload)
            return _Response(matched)
        if self.action == "delete":
            self.client.rows[self.table_name] = [row for row in rows if row not in matched]
            return _Response(matched)

        count = len(matched)
        if self.range_value:
            start, end = self.range_value
            matched = matched[start:end + 1]
        if self.limit_value is not None:
            matched = matched[:self.limit_value]
        return _Response(matched, count=count)


class _Client:
    def __init__(self, rows=None):
        self.rows = rows or {}
        self.queries: list[_Query] = []

    def table(self, table_name):
        return _Query(self, table_name)


def _application_row(*, consultation_enabled: bool | None = None) -> dict:
    row = {
        "id": str(uuid4()),
        "applicant_user_id": str(uuid4()),
        "legal_name": "张同学",
        "school": "示例大学",
        "major": "经济学",
        "phone": TEST_APPLICATION_PHONE,
        "admission_year": 2025,
        "graduation_year": 2027,
        "exam_type": "Z001",
        "score": 110,
        "skills": ["院校选择"],
        "bio": "经验简介",
        "price_cents": 3900,
        "application_status": "pending",
        "admin_note": None,
        "reviewed_at": None,
        "created_at": "2026-09-01T08:00:00+00:00",
        "updated_at": "2026-09-01T08:00:00+00:00",
    }
    if consultation_enabled is not None:
        row["consultation_enabled"] = consultation_enabled
    return row


def _mentor_row(*, consultation_enabled: bool) -> dict:
    return {
        "id": str(uuid4()),
        "owner_user_id": str(uuid4()),
        "display_name": "张*学",
        "avatar_label": "张",
        "avatar_url": None,
        "avatar_tone": "blue",
        "school": "示例大学",
        "major": "经济学",
        "admission_year": 2025,
        "graduation_year": 2027,
        "exam_type": "Z001",
        "score": 110,
        "bio": "经验简介",
        "story": "",
        "price_cents": 3900,
        "consultation_window_minutes": 60,
        "consultation_enabled": consultation_enabled,
        "online_status": "offline",
        "accepts_booking": consultation_enabled,
        "is_featured": False,
        "recommend_score": 0,
        "rating": 0,
        "rating_count": 0,
        "consult_count": 0,
        "verification_status": "verified",
        "is_published": True,
    }


class MentorConsultationOptInTests(unittest.TestCase):
    def test_application_exam_accepts_null_score_across_write_schemas(self):
        application_payload = {
            "legal_name": "张同学",
            "school": "示例大学",
            "major": "经济学",
            "admission_year": 2025,
            "graduation_year": 2027,
            "exam_type": "application",
            "score": None,
        }
        self.assertIsNone(
            MentorVerificationApplicationCreateRequest(
                **application_payload,
                phone=TEST_APPLICATION_PHONE,
            ).score
        )
        self.assertIsNone(AdminMentorProfileCreateRequest(**application_payload).score)
        self.assertIsNone(MentorProfileChangeRequestCreateRequest(
            school="示例大学",
            major="经济学",
            exam_type="application",
            score=None,
            price_cents=3900,
        ).score)

    def test_exam_score_schema_rejects_mismatched_combinations(self):
        base = {
            "legal_name": "张同学",
            "school": "示例大学",
            "major": "经济学",
            "phone": TEST_APPLICATION_PHONE,
            "admission_year": 2025,
            "graduation_year": 2027,
        }
        with self.assertRaises(ValidationError):
            MentorVerificationApplicationCreateRequest(**base, exam_type="application", score=0)
        with self.assertRaises(ValidationError):
            MentorVerificationApplicationCreateRequest(**base, exam_type="Z001", score=None)
        self.assertEqual(
            MentorVerificationApplicationCreateRequest(**base, exam_type="Z002", score=110).score,
            110,
        )

    def test_application_phone_requires_exactly_eleven_digits(self):
        base = {
            "legal_name": "张同学",
            "school": "示例大学",
            "major": "经济学",
            "admission_year": 2025,
            "graduation_year": 2027,
            "exam_type": "Z001",
            "score": 110,
        }
        self.assertEqual(
            MentorVerificationApplicationCreateRequest(**base, phone=TEST_APPLICATION_PHONE).phone,
            TEST_APPLICATION_PHONE,
        )
        for invalid_phone in ("1234567890", "123456789012", "1234567890a", "１２３４５６７８９０１"):
            with self.subTest(phone=invalid_phone), self.assertRaises(ValidationError):
                MentorVerificationApplicationCreateRequest(**base, phone=invalid_phone)

    def test_application_create_and_serializers_preserve_null_score(self):
        user_id = str(uuid4())
        client = _Client({"mentor_profiles": [], "mentor_verification_applications": []})
        payload = MentorVerificationApplicationCreateRequest(
            legal_name="张同学",
            school="示例大学",
            major="经济学",
            phone=TEST_APPLICATION_PHONE,
            admission_year=2025,
            graduation_year=2027,
            exam_type="application",
            score=None,
        )
        with patch.object(mentor_consultation, "get_supabase_admin", return_value=client):
            result = mentor_consultation.create_mentor_verification_application(payload, user_id)
        inserted = client.rows["mentor_verification_applications"][0]
        self.assertIsNone(inserted["score"])
        self.assertEqual(inserted["phone"], TEST_APPLICATION_PHONE)
        self.assertIsNone(result.score)
        self.assertEqual(result.phone, TEST_APPLICATION_PHONE)
        self.assertIsNone(mentor_consultation._serialize_mentor_verification_application(inserted)["score"])
        self.assertIsNone(mentor_admin._serialize_mentor_application(inserted)["score"])
        self.assertEqual(
            mentor_consultation._serialize_mentor_verification_application(inserted)["phone"],
            TEST_APPLICATION_PHONE,
        )
        self.assertEqual(
            mentor_admin._serialize_mentor_application(inserted)["phone"],
            TEST_APPLICATION_PHONE,
        )

        public_row = _mentor_row(consultation_enabled=True)
        public_row.update({"exam_type": "application", "score": None})
        public_payload = mentor_consultation._serialize_mentor_public_profile(public_row)
        self.assertIsNone(public_payload["score"])
        self.assertIsNone(MentorPublicItem(**public_payload).score)

    def test_application_schema_keeps_legacy_default_and_accepts_opt_out(self):
        base = {
            "legal_name": "张同学",
            "school": "示例大学",
            "major": "经济学",
            "phone": TEST_APPLICATION_PHONE,
            "admission_year": 2025,
            "graduation_year": 2027,
            "exam_type": "Z001",
            "score": 110,
        }
        self.assertTrue(MentorVerificationApplicationCreateRequest(**base).consultation_enabled)
        self.assertFalse(
            MentorVerificationApplicationCreateRequest(**base, consultation_enabled=False).consultation_enabled
        )

    def test_application_serializers_default_legacy_rows_to_enabled(self):
        legacy = _application_row()
        self.assertTrue(
            mentor_consultation._serialize_mentor_verification_application(legacy)["consultation_enabled"]
        )
        self.assertTrue(mentor_admin._serialize_mentor_application(legacy)["consultation_enabled"])
        opted_out = _application_row(consultation_enabled=False)
        self.assertFalse(
            mentor_consultation._serialize_mentor_verification_application(opted_out)["consultation_enabled"]
        )
        self.assertFalse(mentor_admin._serialize_mentor_application(opted_out)["consultation_enabled"])

    def test_application_create_persists_opt_out(self):
        user_id = str(uuid4())
        client = _Client({"mentor_profiles": [], "mentor_verification_applications": []})
        payload = MentorVerificationApplicationCreateRequest(
            legal_name="张同学",
            school="示例大学",
            major="经济学",
            phone=TEST_APPLICATION_PHONE,
            admission_year=2025,
            graduation_year=2027,
            exam_type="Z001",
            score=110,
            consultation_enabled=False,
        )
        with patch.object(mentor_consultation, "get_supabase_admin", return_value=client):
            result = mentor_consultation.create_mentor_verification_application(payload, user_id)
        self.assertFalse(result.consultation_enabled)
        self.assertFalse(client.rows["mentor_verification_applications"][0]["consultation_enabled"])
        self.assertEqual(client.rows["mentor_verification_applications"][0]["phone"], TEST_APPLICATION_PHONE)

    def test_revoked_profile_can_submit_a_new_verification_application(self):
        user_id = str(uuid4())
        revoked_profile = _mentor_row(consultation_enabled=False)
        revoked_profile.update({
            "owner_user_id": user_id,
            "verification_status": "revoked",
            "is_published": False,
            "accepts_booking": False,
        })
        previous_application = _application_row(consultation_enabled=True)
        previous_application.update({
            "applicant_user_id": user_id,
            "application_status": "revoked",
            "revocation_reason": "认证信息已发生变化，请重新提交审核",
            "revoked_at": "2026-09-02T08:00:00+00:00",
        })
        client = _Client({
            "mentor_profiles": [revoked_profile],
            "mentor_verification_applications": [previous_application],
        })
        payload = MentorVerificationApplicationCreateRequest(
            legal_name="张同学",
            school="新示例大学",
            major="金融学",
            phone=TEST_APPLICATION_PHONE,
            admission_year=2026,
            graduation_year=2028,
            exam_type="Z001",
            score=115,
        )

        with patch.object(mentor_consultation, "get_supabase_admin", return_value=client):
            result = mentor_consultation.create_mentor_verification_application(payload, user_id)

        applications = client.rows["mentor_verification_applications"]
        self.assertEqual(len(applications), 2)
        self.assertEqual(applications[0]["application_status"], "revoked")
        self.assertEqual(applications[1]["application_status"], "pending")
        self.assertEqual(result.application_status, "pending")
        self.assertEqual(revoked_profile["verification_status"], "revoked")

    def test_verified_profile_still_blocks_duplicate_verification_application(self):
        user_id = str(uuid4())
        verified_profile = _mentor_row(consultation_enabled=True)
        verified_profile["owner_user_id"] = user_id
        client = _Client({"mentor_profiles": [verified_profile], "mentor_verification_applications": []})
        payload = MentorVerificationApplicationCreateRequest(
            legal_name="张同学",
            school="示例大学",
            major="经济学",
            phone=TEST_APPLICATION_PHONE,
            admission_year=2025,
            graduation_year=2027,
            exam_type="Z001",
            score=110,
        )

        with (
            patch.object(mentor_consultation, "get_supabase_admin", return_value=client),
            self.assertRaises(HTTPException) as raised,
        ):
            mentor_consultation.create_mentor_verification_application(payload, user_id)

        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(raised.exception.detail, "你已拥有前辈档案，无需重复申请")
        self.assertEqual(client.rows["mentor_verification_applications"], [])

    def test_revoked_profile_with_pending_reapplication_blocks_duplicate_submit(self):
        user_id = str(uuid4())
        revoked_profile = _mentor_row(consultation_enabled=False)
        revoked_profile.update({"owner_user_id": user_id, "verification_status": "revoked", "is_published": False})
        pending_application = _application_row(consultation_enabled=True)
        pending_application["applicant_user_id"] = user_id
        client = _Client({
            "mentor_profiles": [revoked_profile],
            "mentor_verification_applications": [pending_application],
        })
        payload = MentorVerificationApplicationCreateRequest(
            legal_name="张同学",
            school="示例大学",
            major="经济学",
            phone=TEST_APPLICATION_PHONE,
            admission_year=2025,
            graduation_year=2027,
            exam_type="Z001",
            score=110,
        )

        with (
            patch.object(mentor_consultation, "get_supabase_admin", return_value=client),
            self.assertRaises(HTTPException) as raised,
        ):
            mentor_consultation.create_mentor_verification_application(payload, user_id)

        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(raised.exception.detail, "你已有正在审核的前辈申请")
        self.assertEqual(len(client.rows["mentor_verification_applications"]), 1)

    def test_concurrent_reapplication_unique_conflict_returns_pending_message(self):
        user_id = str(uuid4())
        payload = MentorVerificationApplicationCreateRequest(
            legal_name="张同学",
            school="示例大学",
            major="经济学",
            phone=TEST_APPLICATION_PHONE,
            admission_year=2025,
            graduation_year=2027,
            exam_type="Z001",
            score=110,
        )

        def fake_call_supabase(_operation, *, operation_name: str):
            if operation_name == "mentor verification profile lookup":
                return _Response([{"id": str(uuid4()), "verification_status": "revoked"}])
            if operation_name == "mentor verification pending lookup":
                return _Response([])
            if operation_name == "mentor verification application create":
                raise RuntimeError("duplicate key value violates unique constraint (23505)")
            self.fail(f"unexpected operation: {operation_name}")

        with (
            patch.object(mentor_consultation, "get_supabase_admin", return_value=object()),
            patch.object(mentor_consultation, "call_supabase", side_effect=fake_call_supabase),
            self.assertRaises(HTTPException) as raised,
        ):
            mentor_consultation.create_mentor_verification_application(payload, user_id)

        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(raised.exception.detail, "你已有正在审核的前辈申请")

    def test_approval_keeps_identity_published_but_disables_consultation(self):
        application = _application_row(consultation_enabled=False)
        client = _Client({
            "mentor_verification_applications": [application],
            "mentor_profiles": [],
        })
        payload = SimpleNamespace(decision="approve", admin_note=None)
        with (
            patch.object(mentor_admin, "get_supabase_admin", return_value=client),
            patch.object(mentor_admin, "_replace_mentor_skills"),
            patch.object(mentor_admin, "_log_application_action"),
            patch.object(mentor_admin, "_fetch_application_document_counts", return_value={}),
        ):
            result = mentor_admin.decide_admin_mentor_verification_application(
                application["id"],
                payload,
                {"id": str(uuid4())},
            )
        profile = client.rows["mentor_profiles"][0]
        self.assertFalse(result.consultation_enabled)
        self.assertTrue(profile["is_published"])
        self.assertFalse(profile["consultation_enabled"])
        self.assertFalse(profile["accepts_booking"])
        self.assertEqual(profile["online_status"], "offline")
        self.assertNotIn("phone", profile)

    def test_reapplication_approval_restores_original_profile_without_clearing_history(self):
        user_id = str(uuid4())
        mentor_id = str(uuid4())
        application = _application_row(consultation_enabled=True)
        application.update({
            "applicant_user_id": user_id,
            "legal_name": "李同学",
            "school": "更新大学",
            "major": "金融学",
            "admission_year": 2026,
            "graduation_year": 2028,
            "exam_type": "Z002",
            "score": 118,
            "skills": ["专业选择", "复试经验"],
            "bio": "更新后的认证简介",
            "price_cents": 4900,
        })
        revoked_profile = _mentor_row(consultation_enabled=False)
        revoked_profile.update({
            "id": mentor_id,
            "owner_user_id": user_id,
            "legal_name": "张同学",
            "display_name": "张*学",
            "avatar_url": "https://example.invalid/avatar.png",
            "avatar_tone": "violet",
            "story": "原有完整上岸经历",
            "verification_status": "revoked",
            "is_published": False,
            "is_featured": False,
            "recommend_score": 88,
            "rating": 4.9,
            "rating_count": 12,
            "consult_count": 28,
        })
        closed_slot = {
            "id": str(uuid4()),
            "mentor_id": mentor_id,
            "status": "closed",
        }
        client = _Client({
            "mentor_verification_applications": [application],
            "mentor_profiles": [revoked_profile],
            "mentor_profile_skills": [{"mentor_id": mentor_id, "skill": "旧领域", "sort_order": 1}],
            "mentor_availability_slots": [closed_slot],
        })
        payload = SimpleNamespace(decision="approve", admin_note="重新核验通过")

        with (
            patch.object(mentor_admin, "get_supabase_admin", return_value=client),
            patch.object(mentor_admin, "_log_application_action"),
            patch.object(mentor_admin, "_notify_mentor_verification_decision"),
            patch.object(mentor_admin, "_fetch_application_document_counts", return_value={}),
        ):
            result = mentor_admin.decide_admin_mentor_verification_application(
                application["id"],
                payload,
                {"id": str(uuid4())},
            )

        self.assertEqual(result.application_status, "approved")
        self.assertEqual(len(client.rows["mentor_profiles"]), 1)
        restored = client.rows["mentor_profiles"][0]
        self.assertEqual(restored["id"], mentor_id)
        self.assertEqual(restored["verification_status"], "verified")
        self.assertTrue(restored["is_published"])
        self.assertTrue(restored["consultation_enabled"])
        self.assertEqual(restored["online_status"], "offline")
        self.assertEqual(restored["school"], "更新大学")
        self.assertEqual(restored["major"], "金融学")
        self.assertEqual(restored["avatar_url"], "https://example.invalid/avatar.png")
        self.assertEqual(restored["avatar_tone"], "violet")
        self.assertEqual(restored["story"], "原有完整上岸经历")
        self.assertEqual(restored["recommend_score"], 88)
        self.assertEqual(restored["rating"], 4.9)
        self.assertEqual(restored["rating_count"], 12)
        self.assertEqual(restored["consult_count"], 28)
        self.assertEqual(client.rows["mentor_availability_slots"][0]["status"], "closed")
        self.assertEqual(
            [row["skill"] for row in client.rows["mentor_profile_skills"]],
            ["专业选择", "复试经验"],
        )

    def test_reapplication_rejection_keeps_original_profile_revoked(self):
        user_id = str(uuid4())
        application = _application_row(consultation_enabled=True)
        application["applicant_user_id"] = user_id
        revoked_profile = _mentor_row(consultation_enabled=False)
        revoked_profile.update({
            "owner_user_id": user_id,
            "verification_status": "revoked",
            "is_published": False,
        })
        client = _Client({
            "mentor_verification_applications": [application],
            "mentor_profiles": [revoked_profile],
        })

        with (
            patch.object(mentor_admin, "get_supabase_admin", return_value=client),
            patch.object(mentor_admin, "_log_application_action"),
            patch.object(mentor_admin, "_notify_mentor_verification_decision"),
            patch.object(mentor_admin, "_fetch_application_document_counts", return_value={}),
        ):
            result = mentor_admin.decide_admin_mentor_verification_application(
                application["id"],
                SimpleNamespace(decision="reject", admin_note="证明材料仍需补充"),
                {"id": str(uuid4())},
            )

        self.assertEqual(result.application_status, "rejected")
        self.assertEqual(revoked_profile["verification_status"], "revoked")
        self.assertFalse(revoked_profile["is_published"])

    def test_public_mentor_queries_exclude_opted_out_profiles(self):
        disabled = _mentor_row(consultation_enabled=False)
        client = _Client({"mentor_profiles": [disabled]})
        with patch.object(mentor_consultation, "get_supabase_admin", return_value=client):
            listing = mentor_consultation.list_public_mentors(
                keyword=None,
                exam_type=None,
                admission_year=None,
                admission_year_before=None,
                availability="all",
                min_price=None,
                max_price=None,
                sort="recommended",
                limit=30,
                offset=0,
            )
            with self.assertRaises(HTTPException) as raised:
                mentor_consultation.get_public_mentor(disabled["id"])
        self.assertEqual(listing.count, 0)
        self.assertEqual(raised.exception.status_code, 404)
        profile_queries = [query for query in client.queries if query.table_name == "mentor_profiles"]
        self.assertTrue(profile_queries)
        self.assertTrue(all(("consultation_enabled", True) in query.filters for query in profile_queries))

    def test_favorites_hide_opted_out_profile(self):
        disabled = _mentor_row(consultation_enabled=False)
        user_id = str(uuid4())
        client = _Client({
            "mentor_favorites": [{"mentor_id": disabled["id"], "user_id": user_id}],
            "mentor_profiles": [disabled],
        })
        with patch.object(mentor_consultation, "get_supabase_admin", return_value=client):
            result = mentor_consultation.list_my_mentor_favorites(user_id)
        self.assertEqual(result.count, 1)
        self.assertIsNone(result.items[0].mentor)
        profile_query = next(query for query in client.queries if query.table_name == "mentor_profiles")
        self.assertIn(("consultation_enabled", True), profile_query.filters)

    def test_order_mentor_lookup_requires_enabled_consultation_only_for_new_access(self):
        disabled = _mentor_row(consultation_enabled=False)
        client = _Client({"mentor_profiles": [disabled]})
        with self.assertRaises(HTTPException):
            mentor_consultation._get_order_mentor_or_404(client, disabled["id"])
        existing_order_mentor = mentor_consultation._get_order_mentor_or_404(
            client,
            disabled["id"],
            require_public=False,
        )
        self.assertEqual(existing_order_mentor["id"], disabled["id"])

    def test_opted_out_verified_profile_can_still_author_experience_posts(self):
        disabled = _mentor_row(consultation_enabled=False)
        client = _Client({"mentor_profiles": [disabled]})

        author = community._current_verified_mentor_author(client, disabled["owner_user_id"])

        self.assertEqual(author["id"], disabled["id"])
        profile_query = next(query for query in client.queries if query.table_name == "mentor_profiles")
        self.assertIn(("verification_status", "verified"), profile_query.filters)
        self.assertIn(("is_published", True), profile_query.filters)
        self.assertNotIn(("consultation_enabled", True), profile_query.filters)

    def test_opted_out_mentor_cannot_change_online_status(self):
        disabled = _mentor_row(consultation_enabled=False)
        client = _Client({"mentor_profiles": [disabled]})

        with (
            patch.object(mentor_consultation, "get_supabase_admin", return_value=client),
            self.assertRaises(HTTPException) as raised,
        ):
            mentor_consultation.update_my_owned_mentor_availability(
                MentorOwnerAvailabilityUpdateRequest(online_status="online"),
                disabled["owner_user_id"],
            )

        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(disabled["online_status"], "offline")
        self.assertFalse(any(query.action == "update" for query in client.queries))

    def test_opted_out_mentor_cannot_create_or_update_availability_slots(self):
        disabled = _mentor_row(consultation_enabled=False)
        client = _Client({"mentor_profiles": [disabled], "mentor_availability_slots": []})
        starts_at = datetime.now(timezone.utc) + timedelta(days=1)
        starts_at = starts_at.replace(minute=0, second=0, microsecond=0)

        with (
            patch.object(mentor_consultation, "get_supabase_admin", return_value=client),
            patch.object(mentor_consultation, "_validate_mentor_slot_schedule_window"),
            self.assertRaises(HTTPException) as create_raised,
        ):
            mentor_consultation.create_my_mentor_availability_slot(
                MentorOwnerAvailabilitySlotCreateRequest(
                    starts_at=starts_at,
                    ends_at=starts_at + timedelta(hours=1),
                ),
                disabled["owner_user_id"],
            )

        with (
            patch.object(mentor_consultation, "get_supabase_admin", return_value=client),
            self.assertRaises(HTTPException) as update_raised,
        ):
            mentor_consultation.update_my_mentor_availability_slot(
                uuid4(),
                MentorOwnerAvailabilitySlotStatusUpdateRequest(status="closed"),
                disabled["owner_user_id"],
            )

        self.assertEqual(create_raised.exception.status_code, 409)
        self.assertEqual(update_raised.exception.status_code, 409)
        self.assertEqual(client.rows["mentor_availability_slots"], [])
        self.assertFalse(any(query.action in {"insert", "update"} for query in client.queries))

    def test_admin_disabling_consultation_closes_only_available_slots(self):
        mentor = _mentor_row(consultation_enabled=True)
        slots = [
            {"id": str(uuid4()), "mentor_id": mentor["id"], "status": "available"},
            {"id": str(uuid4()), "mentor_id": mentor["id"], "status": "held"},
            {"id": str(uuid4()), "mentor_id": mentor["id"], "status": "booked"},
        ]
        client = _Client({"mentor_profiles": [mentor], "mentor_availability_slots": slots})

        with (
            patch.object(mentor_admin, "get_supabase_admin", return_value=client),
            patch.object(mentor_admin, "fetch_mentor_skills", return_value={}),
            patch.object(mentor_admin, "fetch_mentor_aggregates", return_value={}),
            patch.object(mentor_admin, "_log_admin_action"),
        ):
            result = mentor_admin.update_admin_mentor(
                mentor["id"],
                AdminMentorProfileUpdateRequest(consultation_enabled=False),
                {"id": str(uuid4())},
            )

        self.assertFalse(result.consultation_enabled)
        self.assertFalse(mentor["accepts_booking"])
        self.assertEqual(mentor["online_status"], "offline")
        self.assertEqual([slot["status"] for slot in slots], ["closed", "held", "booked"])
        slot_update = next(
            query
            for query in client.queries
            if query.table_name == "mentor_availability_slots" and query.action == "update"
        )
        self.assertEqual(slot_update.payload, {"status": "closed"})
        self.assertIn(("mentor_id", mentor["id"]), slot_update.filters)
        self.assertIn(("status", "available"), slot_update.filters)


if __name__ == "__main__":
    unittest.main()
