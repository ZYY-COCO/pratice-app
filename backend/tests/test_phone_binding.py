from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.routes import auth
from app.schemas.auth import BindPhoneRequest, SendBindPhoneCodeRequest


class _Response:
    def __init__(self, data):
        self.data = data


class _UserUpdateQuery:
    def __init__(self, profile: dict):
        self.profile = dict(profile)
        self.update_values: dict = {}
        self.filters: list[tuple[str, object]] = []

    def update(self, values: dict):
        self.update_values = dict(values)
        return self

    def eq(self, field: str, value: object):
        self.filters.append((field, value))
        return self

    def execute(self):
        return _Response([{**self.profile, **self.update_values}])


class _AuthAdmin:
    def __init__(self):
        self.updated_user_id = ""
        self.updated_payload: dict = {}

    def update_user_by_id(self, user_id: str, payload: dict):
        self.updated_user_id = user_id
        self.updated_payload = dict(payload)


class _AuthNamespace:
    def __init__(self):
        self.admin = _AuthAdmin()


class _Client:
    def __init__(self, profile: dict):
        self.query = _UserUpdateQuery(profile)
        self.auth = _AuthNamespace()

    def table(self, table_name: str):
        if table_name != "users":
            raise AssertionError(f"unexpected table: {table_name}")
        return self.query


class PhoneBindingTests(unittest.TestCase):
    def setUp(self):
        self.profile = {
            "id": "user-1",
            "email": "user@example.com",
            "phone": None,
            "auth_provider": "email",
            "nickname": "研友",
        }

    def test_send_bind_phone_code_uses_dedicated_purpose(self):
        with (
            patch.object(auth, "_get_profile_by_id", return_value=self.profile),
            patch.object(auth, "_get_profile_by_phone", return_value=None),
            patch.object(auth, "_send_phone_code", return_value="654321") as send_code,
        ):
            response = auth.send_bind_phone_code(
                SendBindPhoneCodeRequest(phone="13800138000"),
                user_id="user-1",
            )

        self.assertEqual(response.debug_code, "654321")
        send_code.assert_called_once_with("13800138000", "bind_phone")

    def test_bind_phone_verifies_code_and_updates_profile(self):
        client = _Client(self.profile)
        with (
            patch.object(auth, "get_supabase_admin", return_value=client),
            patch.object(auth, "_get_profile_by_id", return_value=self.profile),
            patch.object(auth, "_get_profile_by_phone", return_value=None),
            patch.object(auth, "verify_phone_code_or_raise") as verify_code,
        ):
            response = auth.bind_phone(
                BindPhoneRequest(phone="13800138000", verification_code="123456"),
                user_id="user-1",
            )

        self.assertEqual(response.phone, "13800138000")
        self.assertEqual(client.query.update_values, {"phone": "13800138000"})
        self.assertIn(("id", "user-1"), client.query.filters)
        verify_code.assert_called_once_with(
            supabase=client,
            phone="13800138000",
            purpose="bind_phone",
            code="123456",
        )
        self.assertEqual(client.auth.admin.updated_user_id, "user-1")
        self.assertEqual(
            client.auth.admin.updated_payload["user_metadata"]["phone"],
            "13800138000",
        )

    def test_bind_phone_rejects_number_owned_by_another_account(self):
        client = _Client(self.profile)
        with (
            patch.object(auth, "get_supabase_admin", return_value=client),
            patch.object(auth, "_get_profile_by_id", return_value=self.profile),
            patch.object(auth, "_get_profile_by_phone", return_value={"id": "user-2"}),
        ):
            with self.assertRaises(HTTPException) as raised:
                auth.bind_phone(
                    BindPhoneRequest(phone="13800138000", verification_code="123456"),
                    user_id="user-1",
                )

        self.assertEqual(raised.exception.status_code, 409)


if __name__ == "__main__":
    unittest.main()
