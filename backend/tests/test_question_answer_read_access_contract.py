from __future__ import annotations

import re
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAIN_SCHEMA_PATH = PROJECT_ROOT / "database" / "supabase_schema.sql"
HARDENING_MIGRATION_PATH = (
    PROJECT_ROOT / "database" / "question_answer_read_access_hardening.sql"
)


class QuestionAnswerReadAccessContractTests(unittest.TestCase):
    @staticmethod
    def compact(value: str) -> str:
        return re.sub(r"\s+", " ", value.lower()).strip()

    @classmethod
    def setUpClass(cls):
        cls.schemas = {
            "main schema": cls.compact(MAIN_SCHEMA_PATH.read_text(encoding="utf-8")),
            "hardening migration": cls.compact(
                HARDENING_MIGRATION_PATH.read_text(encoding="utf-8")
            ),
        }

    def test_main_schema_and_incremental_migration_close_direct_question_reads(self):
        for label, sql in self.schemas.items():
            with self.subTest(schema=label):
                self.assertIn(
                    'drop policy if exists "authenticated users can read questions" '
                    "on public.questions;",
                    sql,
                )
                self.assertNotIn(
                    'create policy "authenticated users can read questions"',
                    sql,
                )
                self.assertIn(
                    "revoke all privileges on table public.questions "
                    "from public, anon, authenticated;",
                    sql,
                )
                self.assertIn(
                    "revoke select (answer, explanation) on table public.questions "
                    "from public, anon, authenticated;",
                    sql,
                )
                self.assertNotIn(
                    "grant select on table public.questions to authenticated;",
                    sql,
                )

    def test_service_role_keeps_backend_question_crud(self):
        expected_grant = (
            "grant select, insert, update, delete on table public.questions "
            "to service_role;"
        )
        for label, sql in self.schemas.items():
            with self.subTest(schema=label):
                self.assertIn(expected_grant, sql)
                revoke_position = sql.index(
                    "revoke all privileges on table public.questions"
                )
                grant_position = sql.index(expected_grant)
                self.assertLess(revoke_position, grant_position)

    def test_incremental_migration_is_atomic_and_refreshes_postgrest(self):
        sql = self.schemas["hardening migration"]
        self.assertTrue(sql.startswith("--"))
        self.assertIn("begin;", sql)
        self.assertIn("notify pgrst, 'reload schema';", sql)
        self.assertTrue(sql.endswith("commit;"))
        self.assertLess(sql.index("begin;"), sql.index("commit;"))


if __name__ == "__main__":
    unittest.main()
