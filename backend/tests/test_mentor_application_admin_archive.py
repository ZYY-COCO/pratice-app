import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException

from app.routes import mentor_admin
from app.schemas.mentor_consultation import AdminMentorVerificationArchiveRequest


ADMIN_ID = "22222222-2222-4222-8222-222222222222"
APPLICATION_ID = "33333333-3333-4333-8333-333333333333"


class _RpcCall:
    def __init__(self, client, name, payload):
        self.client = client
        self.name = name
        self.payload = payload

    def execute(self):
        self.client.calls.append((self.name, self.payload))
        if self.client.error:
            raise self.client.error
        return SimpleNamespace(data=self.client.result)


class _RpcClient:
    def __init__(self, result=None, *, error=None):
        self.result = result or []
        self.error = error
        self.calls = []

    def rpc(self, name, payload):
        return _RpcCall(self, name, payload)


class _ApplicationListQuery:
    def __init__(self, rows):
        self.rows = rows
        self.operations = []

    def select(self, *args, **kwargs):
        self.operations.append(("select", args, kwargs))
        return self

    def is_(self, *args):
        self.operations.append(("is", args))
        return self

    def eq(self, *args):
        self.operations.append(("eq", args))
        return self

    def order(self, *args, **kwargs):
        self.operations.append(("order", args, kwargs))
        return self

    def range(self, *args):
        self.operations.append(("range", args))
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows, count=len(self.rows))


class _ApplicationListClient:
    def __init__(self, rows):
        self.query = _ApplicationListQuery(rows)

    def table(self, name):
        if name != "mentor_verification_applications":
            raise AssertionError(f"unexpected table: {name}")
        return self.query


def _revoked_application_row():
    return {
        "id": APPLICATION_ID,
        "applicant_user_id": "11111111-1111-4111-8111-111111111111",
        "legal_name": "张同学",
        "school": "示例大学",
        "major": "经济学",
        "phone": None,
        "admission_year": 2025,
        "graduation_year": 2027,
        "exam_type": "Z001",
        "score": 110,
        "skills": ["院校选择"],
        "bio": "经验简介",
        "price_cents": 3900,
        "consultation_enabled": False,
        "application_status": "revoked",
        "admin_note": None,
        "revocation_reason": "认证信息复核未通过",
        "revoked_at": "2026-09-03T08:00:00+00:00",
        "reviewed_at": "2026-09-01T08:00:00+00:00",
        "created_at": "2026-09-01T08:00:00+00:00",
        "updated_at": "2026-09-03T08:00:00+00:00",
    }


class MentorApplicationAdminArchiveTests(unittest.TestCase):
    def test_archive_revoked_applications_uses_atomic_rpc_and_deduplicates_ids(self):
        client = _RpcClient([{"application_id": APPLICATION_ID}])
        payload = AdminMentorVerificationArchiveRequest(ids=[APPLICATION_ID, APPLICATION_ID])

        with (
            patch.object(mentor_admin, "get_supabase_admin", return_value=client),
            patch.object(mentor_admin, "_log_application_action") as log_action,
        ):
            result = mentor_admin.archive_admin_revoked_mentor_applications(payload, {"id": ADMIN_ID})

        self.assertEqual(result.affected_count, 1)
        self.assertEqual(client.calls, [(
            "archive_revoked_mentor_applications",
            {"p_application_ids": [APPLICATION_ID], "p_admin_user_id": ADMIN_ID},
        )])
        self.assertEqual(log_action.call_args.args[2:5], (
            "archive_revoked_mentor_applications",
            None,
            {"application_ids": [APPLICATION_ID], "affected_count": 1},
        ))

    def test_archive_rejects_non_revoked_or_stale_selection_atomically(self):
        client = _RpcClient(error=RuntimeError("MENTOR_APPLICATION_ARCHIVE_INELIGIBLE"))
        payload = AdminMentorVerificationArchiveRequest(ids=[APPLICATION_ID])

        with (
            patch.object(mentor_admin, "get_supabase_admin", return_value=client),
            self.assertRaises(HTTPException) as raised,
        ):
            mentor_admin.archive_admin_revoked_mentor_applications(payload, {"id": ADMIN_ID})

        self.assertEqual(raised.exception.status_code, 409)
        self.assertIn("尚未取消资格", raised.exception.detail)

    def test_archive_rejects_partial_rpc_result(self):
        first_id = str(uuid4())
        second_id = str(uuid4())
        client = _RpcClient([{"application_id": first_id}])
        payload = AdminMentorVerificationArchiveRequest(ids=[first_id, second_id])

        with (
            patch.object(mentor_admin, "get_supabase_admin", return_value=client),
            self.assertRaises(HTTPException) as raised,
        ):
            mentor_admin.archive_admin_revoked_mentor_applications(payload, {"id": ADMIN_ID})

        self.assertEqual(raised.exception.status_code, 409)

    def test_application_list_excludes_admin_archived_rows_after_migration(self):
        client = _ApplicationListClient([_revoked_application_row()])

        with (
            patch.object(mentor_admin, "get_supabase_admin", return_value=client),
            patch.object(mentor_admin, "_fetch_application_users", return_value={}),
            patch.object(mentor_admin, "_fetch_application_document_counts", return_value={}),
        ):
            result = mentor_admin.list_admin_mentor_verification_applications(
                application_status="revoked",
                keyword=None,
                limit=20,
                offset=0,
                _={},
            )

        self.assertEqual(result.count, 1)
        self.assertEqual(result.items[0].application_status, "revoked")
        self.assertIn(("is", ("admin_archived_at", "null")), client.query.operations)
        self.assertIn(("eq", ("application_status", "revoked")), client.query.operations)

    def test_archive_migration_preserves_accounts_profiles_and_business_history(self):
        migration = (
            Path(__file__).resolve().parents[2]
            / "database"
            / "mentor_application_admin_archive.sql"
        ).read_text(encoding="utf-8")
        normalized = migration.lower()

        self.assertIn("application.application_status = 'revoked'", normalized)
        self.assertIn("application.admin_archived_at is null", normalized)
        self.assertIn("mentor_application_archive_ineligible", normalized)
        self.assertIn("update public.mentor_verification_applications", normalized)
        self.assertNotIn("delete from public.users", normalized)
        self.assertNotIn("update public.mentor_profiles", normalized)
        self.assertNotIn("delete from public.mentor_", normalized)


if __name__ == "__main__":
    unittest.main()
