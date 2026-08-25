from __future__ import annotations

import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException

from app.routes import community, feedback, wrong_questions
from app.utils.cursor_pagination import (
    build_keyset_filter,
    decode_page_cursor,
    encode_page_cursor,
)


class _Response:
    def __init__(self, data):
        self.data = data


class _WrongQuestionQuery:
    def __init__(self, rows):
        self.rows = rows
        self.filters = []
        self.orders = []
        self.requested_limit = 0

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, field, value):
        self.filters.append(("eq", field, value))
        return self

    def or_(self, expression, **kwargs):
        self.filters.append(("or", expression, kwargs))
        return self

    def order(self, field, **kwargs):
        self.orders.append((field, kwargs))
        return self

    def limit(self, value):
        self.requested_limit = value
        return self

    def execute(self):
        return _Response(self.rows[:self.requested_limit or len(self.rows)])


class _WrongQuestionClient:
    def __init__(self, rows):
        self.query = _WrongQuestionQuery(rows)

    def table(self, table_name):
        if table_name != "wrong_questions":
            raise AssertionError(f"unexpected table: {table_name}")
        return self.query


class _FeedbackQuery:
    def __init__(self, rows):
        self.rows = rows
        self.limit_value = 0

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def execute(self):
        response = _Response(self.rows[:self.limit_value or len(self.rows)])
        response.count = len(self.rows)
        return response


class _FeedbackClient:
    def __init__(self, rows):
        self.query = _FeedbackQuery(rows)

    def table(self, table_name):
        if table_name != "beta_feedback":
            raise AssertionError(f"unexpected table: {table_name}")
        return self.query


class _CommunityQuery:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.after_cursor = False
        self.limit_value = 0
        self.in_values: list[str] = []

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def or_(self, *_args, **_kwargs):
        self.after_cursor = True
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def in_(self, _field, values):
        self.in_values = [str(value) for value in values]
        return self

    def execute(self):
        if self.table_name == "circle_community_likes":
            rows = self.client.like_rows[1:] if self.after_cursor else self.client.like_rows
        elif self.table_name == "circle_community_posts":
            rows = [row for row in self.client.post_rows if str(row["id"]) in self.in_values]
        else:
            raise AssertionError(f"unexpected table: {self.table_name}")
        return _Response(rows[:self.limit_value or len(rows)])


class _CommunityClient:
    def __init__(self, like_rows, post_rows):
        self.like_rows = like_rows
        self.post_rows = post_rows

    def table(self, table_name):
        return _CommunityQuery(self, table_name)


def _question_row(index: int) -> dict:
    question_id = str(uuid4())
    return {
        "id": str(uuid4()),
        "question_id": question_id,
        "wrong_count": index,
        "last_wrong_at": f"2026-08-2{index}T08:00:00+00:00",
        "questions": {
            "id": question_id,
            "exam_code": "Z001",
            "subject": "逻辑推理",
            "module": "演绎推理",
            "submodule": "充分条件",
            "question_type": "single_choice",
            "stem": f"题目 {index}",
            "option_a": "A",
            "option_b": "B",
            "option_c": "C",
            "option_d": "D",
            "answer": "A",
            "explanation": "解析",
            "difficulty": 2,
            "source_type": "official",
            "source_year": 2026,
            "passage_id": None,
        },
    }


class CursorPaginationTests(unittest.TestCase):
    def test_cursor_round_trip_is_bound_to_query_context(self):
        cursor = encode_page_cursor("fixture", {"sort": "latest", "id": "row-1"})
        payload = decode_page_cursor(cursor, kind="fixture", context={"sort": "latest"})
        self.assertEqual(payload["id"], "row-1")

        with self.assertRaises(HTTPException) as raised:
            decode_page_cursor(cursor, kind="fixture", context={"sort": "hot"})
        self.assertEqual(raised.exception.status_code, 422)

    def test_compound_keyset_filter_preserves_tie_break_order(self):
        expression = build_keyset_filter([
            ("created_at", "desc", "2026-08-24T08:00:00+00:00"),
            ("id", "desc", "00000000-0000-0000-0000-000000000001"),
        ])
        self.assertEqual(
            expression,
            "created_at.lt.2026-08-24T08:00:00+00:00,"
            "and(created_at.eq.2026-08-24T08:00:00+00:00,id.lt.00000000-0000-0000-0000-000000000001)",
        )

    def test_wrong_question_route_returns_lookahead_cursor_and_hides_answers(self):
        client = _WrongQuestionClient([_question_row(4), _question_row(3), _question_row(2)])
        with patch.object(wrong_questions, "get_supabase_admin", return_value=client):
            response = wrong_questions.list_wrong_questions(
                user_id="user-1",
                subject="逻辑推理",
                module=None,
                submodule=None,
                limit=2,
                cursor=None,
            )

        self.assertEqual(len(response.items), 2)
        self.assertTrue(response.has_more)
        self.assertTrue(response.next_cursor)
        self.assertIsNone(response.items[0].question.answer)
        self.assertIsNone(response.items[0].question.explanation)
        self.assertEqual(client.query.requested_limit, 3)
        self.assertEqual([item[0] for item in client.query.orders], ["last_wrong_at", "id"])

    def test_feedback_route_is_scoped_to_current_user(self):
        client = _FeedbackClient([{
            "id": "feedback-1",
            "feedback_type": "功能建议",
            "content": "希望增加反馈结果页面",
            "status": "resolved",
            "admin_note": "已加入排期",
            "source_page": "about",
            "created_at": "2026-08-24T08:00:00+00:00",
            "handled_at": "2026-08-24T09:00:00+00:00",
        }])
        with patch.object(feedback, "get_supabase_admin", return_value=client):
            response = feedback.list_my_feedback(user_id="user-1", limit=50)
        self.assertEqual(response.count, 1)
        self.assertEqual(response.items[0].status, "resolved")
        self.assertEqual(response.items[0].admin_note, "已加入排期")

    def test_liked_posts_cursor_reaches_a_distinct_second_page(self):
        post_ids = [str(uuid4()) for _ in range(3)]
        like_rows = [
            {
                "post_id": post_id,
                "created_at": f"2026-08-{24 - index:02d}T08:00:00+00:00",
            }
            for index, post_id in enumerate(post_ids)
        ]
        post_rows = [
            {
                "id": post_id,
                "author_id": "author-1",
                "author_name": "研友",
                "post_type": "chat",
                "title": f"帖子 {index + 1}",
                "content": "分页测试内容",
                "created_at": like_rows[index]["created_at"],
                "is_published": True,
            }
            for index, post_id in enumerate(post_ids)
        ]
        client = _CommunityClient(like_rows, post_rows)

        with (
            patch.object(community, "get_supabase_admin", return_value=client),
            patch.object(community, "_fetch_community_profiles", return_value={}),
            patch.object(community, "_fetch_verified_mentor_owner_ids", return_value=set()),
            patch.object(community, "_fetch_comment_previews", return_value={}),
        ):
            first = community.list_liked_community_posts(limit=1, cursor=None, user_id="user-1")
            second = community.list_liked_community_posts(
                limit=1,
                cursor=first.next_cursor,
                user_id="user-1",
            )

        self.assertTrue(first.has_more)
        self.assertTrue(first.next_cursor)
        self.assertEqual([item.id for item in first.items], [post_ids[0]])
        self.assertEqual([item.id for item in second.items], [post_ids[1]])
        self.assertNotEqual(first.items[0].id, second.items[0].id)


if __name__ == "__main__":
    unittest.main()
