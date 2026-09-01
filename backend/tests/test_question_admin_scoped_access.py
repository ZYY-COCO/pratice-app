import json
import unittest
from unittest.mock import ANY, patch

from fastapi import HTTPException

from app import dependencies
from app.routes import admin
from app.schemas.admin import (
    AdminQuestionImageImportCommitResponse,
    AdminQuestionImageImportDryRunResponse,
    AdminQuestionImageImportRequest,
    AdminQuestionStatsResponse,
    QuestionBankItem,
)


Z_BANK_ID = "7822781c-85cd-4f2f-8d56-6ac9c6ae9e57"
OTHER_BANK_ID = "cad66ec8-58a7-43c8-8896-2cf32132e77b"


def scoped_access_row(*bank_ids: str) -> dict:
    return {
        "user_id": "internal-user",
        "is_active": True,
        "note": json.dumps(
            {
                "type": dependencies.QUESTION_ADMIN_PERMISSION_NOTE_TYPE,
                "scope": dependencies.QUESTION_ADMIN_SCOPE_IMPORTER,
                "allowed_question_bank_ids": list(bank_ids),
            }
        ),
    }


def scoped_profile(*bank_ids: str) -> dict:
    permissions = dependencies._question_admin_permissions_from_access_row(
        scoped_access_row(*bank_ids)
    )
    return dependencies._attach_question_admin_permissions(
        {"id": "internal-user", "role": "user"},
        permissions,
    )


class QuestionAdminScopedAccessTests(unittest.TestCase):
    def test_legacy_whitelist_notes_keep_full_access(self):
        permissions = dependencies._question_admin_permissions_from_access_row(
            {"user_id": "legacy-admin", "note": "题库后台"}
        )

        self.assertEqual(permissions["scope"], "full")
        self.assertTrue(permissions["can_access_full_portal"])
        self.assertTrue(permissions["can_manage_questions"])

    def test_invalid_structured_notes_fail_closed(self):
        for note in (
            "{broken-json",
            json.dumps({"type": "unknown_permissions"}),
            json.dumps(
                {
                    "type": dependencies.QUESTION_ADMIN_PERMISSION_NOTE_TYPE,
                    "scope": "unknown_scope",
                }
            ),
        ):
            with self.subTest(note=note):
                permissions = dependencies._question_admin_permissions_from_access_row(
                    {"user_id": "misconfigured-user", "note": note}
                )
                self.assertEqual(permissions["scope"], "none")
                self.assertFalse(permissions["can_access_full_portal"])
                self.assertFalse(permissions["can_view_questions"])
                self.assertFalse(permissions["can_import_questions"])
                self.assertFalse(permissions["can_manage_questions"])

    def test_importer_scope_is_read_and_import_only(self):
        permissions = dependencies._question_admin_permissions_from_access_row(
            scoped_access_row(Z_BANK_ID, Z_BANK_ID)
        )

        self.assertEqual(permissions["scope"], "question_importer")
        self.assertEqual(permissions["allowed_question_bank_ids"], [Z_BANK_ID])
        self.assertTrue(permissions["can_view_questions"])
        self.assertTrue(permissions["can_import_questions"])
        self.assertFalse(permissions["can_manage_questions"])
        self.assertFalse(permissions["can_access_full_portal"])

    def test_importer_bank_scope_is_enforced(self):
        profile = scoped_profile(Z_BANK_ID)

        self.assertEqual(
            dependencies.require_question_admin_bank_access(profile, Z_BANK_ID),
            Z_BANK_ID,
        )
        with self.assertRaises(HTTPException) as missing_bank:
            dependencies.require_question_admin_bank_access(profile, None)
        with self.assertRaises(HTTPException) as other_bank:
            dependencies.require_question_admin_bank_access(profile, OTHER_BANK_ID)

        self.assertEqual(missing_bank.exception.status_code, 403)
        self.assertEqual(other_bank.exception.status_code, 403)

    def test_importer_is_rejected_by_full_management_dependency(self):
        profile = {"id": "internal-user", "role": "user"}
        principal = scoped_profile(Z_BANK_ID)

        with patch.object(dependencies, "_require_question_portal_access", return_value=principal):
            with self.assertRaises(HTTPException) as context:
                dependencies.require_question_admin_user(profile)

        self.assertEqual(context.exception.status_code, 403)

    def test_importer_is_rejected_by_full_portal_dependency(self):
        profile = {"id": "internal-user", "role": "user"}
        principal = scoped_profile(Z_BANK_ID)

        with patch.object(dependencies, "_require_question_portal_access", return_value=principal):
            with self.assertRaises(HTTPException) as context:
                dependencies.require_question_admin_portal_user(profile)

        self.assertEqual(context.exception.status_code, 403)

    def test_question_bank_list_only_returns_allowed_bank(self):
        profile = scoped_profile(Z_BANK_ID)
        banks = [
            QuestionBankItem(id=OTHER_BANK_ID, name="其他题库"),
            QuestionBankItem(id=Z_BANK_ID, name="Z"),
        ]

        with patch.object(admin, "get_supabase_admin", return_value=object()), patch.object(
            admin,
            "_list_question_bank_items",
            return_value=banks,
        ):
            response = admin.admin_question_banks(profile)

        self.assertEqual([item.id for item in response.items], [Z_BANK_ID])

    def test_question_stats_require_an_allowed_bank(self):
        profile = scoped_profile(Z_BANK_ID)

        for question_bank_id in (None, OTHER_BANK_ID):
            with self.subTest(question_bank_id=question_bank_id):
                with self.assertRaises(HTTPException) as context:
                    admin.admin_question_stats(question_bank_id, profile)
                self.assertEqual(context.exception.status_code, 403)

    def test_question_stats_allow_the_scoped_bank(self):
        profile = scoped_profile(Z_BANK_ID)
        expected = AdminQuestionStatsResponse(active=12, archived=3, pending_review=2)

        with patch.object(admin, "get_supabase_admin", return_value=object()), patch.object(
            admin,
            "_count_question_statuses",
            return_value=expected,
        ) as count_statuses:
            response = admin.admin_question_stats(Z_BANK_ID, profile)

        self.assertEqual(response, expected)
        count_statuses.assert_called_once_with(ANY, Z_BANK_ID)

    def test_question_detail_rejects_a_question_from_another_bank(self):
        profile = scoped_profile(Z_BANK_ID)

        with patch.object(admin, "get_supabase_admin", return_value=object()), patch.object(
            admin,
            "_get_manageable_question_or_404",
            return_value={"id": "question-other", "question_bank_id": OTHER_BANK_ID},
        ):
            with self.assertRaises(HTTPException) as context:
                admin.admin_question_detail("question-other", profile)

        self.assertEqual(context.exception.status_code, 403)

    def test_import_routes_allow_the_scoped_bank(self):
        profile = scoped_profile(Z_BANK_ID)
        payload = AdminQuestionImageImportRequest(
            question_bank_id=Z_BANK_ID,
            questions=[{}],
        )
        dry_run = AdminQuestionImageImportDryRunResponse(
            total=1,
            valid_count=0,
            invalid_count=0,
            duplicate_count=0,
            items=[],
        )

        with patch.object(admin, "get_supabase_admin", return_value=object()), patch.object(
            admin,
            "_dry_run_image_import_questions",
            return_value=dry_run,
        ) as run_dry_check:
            dry_run_response = admin.admin_question_image_import_dry_run(payload, profile)
            commit_response = admin.admin_question_image_import_commit(payload, profile)

        self.assertEqual(dry_run_response, dry_run)
        self.assertEqual(
            commit_response,
            AdminQuestionImageImportCommitResponse(inserted_count=0, questions=[]),
        )
        self.assertEqual(run_dry_check.call_count, 2)

    def test_import_routes_reject_another_bank(self):
        profile = scoped_profile(Z_BANK_ID)
        payload = AdminQuestionImageImportRequest(
            question_bank_id=OTHER_BANK_ID,
            questions=[{}],
        )

        for route in (
            admin.admin_question_image_import_dry_run,
            admin.admin_question_image_import_commit,
        ):
            with self.subTest(route=route.__name__):
                with self.assertRaises(HTTPException) as context:
                    route(payload, profile)
                self.assertEqual(context.exception.status_code, 403)

    def test_portal_me_does_not_expose_internal_permission_key(self):
        profile = scoped_profile(Z_BANK_ID)

        response = admin.question_admin_portal_me(profile)

        self.assertNotIn(dependencies.QUESTION_ADMIN_PERMISSION_KEY, response.profile)
        self.assertEqual(response.permissions["scope"], "question_importer")


if __name__ == "__main__":
    unittest.main()
