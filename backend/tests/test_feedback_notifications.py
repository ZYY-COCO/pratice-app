from __future__ import annotations

import unittest
from unittest.mock import patch

from app.routes import admin, notifications
from app.schemas.admin import AdminFeedbackStatusRequest
from app.schemas.notifications import UserNotificationReadTargetRequest
from app.services.user_notifications import normalize_notification_route_path


class _Response:
    def __init__(self, data):
        self.data = data


class _FeedbackUpdateQuery:
    def __init__(self, row: dict):
        self.row = dict(row)
        self.update_data: dict = {}
        self.filters: list[tuple[str, object]] = []

    def update(self, values: dict):
        self.update_data = dict(values)
        return self

    def eq(self, field: str, value: object):
        self.filters.append((field, value))
        return self

    def execute(self):
        return _Response([{**self.row, **self.update_data}])


class _FeedbackClient:
    def __init__(self, row: dict):
        self.query = _FeedbackUpdateQuery(row)

    def table(self, table_name: str):
        if table_name != "beta_feedback":
            raise AssertionError(f"unexpected table: {table_name}")
        return self.query


class _NotificationReadQuery:
    def __init__(self, client):
        self.client = client
        self.operation = "select"
        self.update_values: dict = {}
        self.filters: list[tuple[str, str, object]] = []

    def select(self, *_args, **_kwargs):
        self.operation = "select"
        return self

    def update(self, values: dict):
        self.operation = "update"
        self.update_values = dict(values)
        return self

    def eq(self, field: str, value: object):
        self.filters.append(("eq", field, value))
        return self

    def is_(self, field: str, value: object):
        self.filters.append(("is", field, value))
        return self

    def in_(self, field: str, values: list[str]):
        self.filters.append(("in", field, list(values)))
        return self

    def execute(self):
        def matches(row: dict) -> bool:
            for kind, field, value in self.filters:
                if kind == "eq" and row.get(field) != value:
                    return False
                if kind == "is" and value == "null" and row.get(field) is not None:
                    return False
                if kind == "in" and row.get(field) not in value:
                    return False
            return True

        rows = [row for row in self.client.rows if matches(row)]
        if self.operation == "update":
            for row in rows:
                row.update(self.update_values)
        return _Response(rows)


class _NotificationReadClient:
    def __init__(self, rows: list[dict]):
        self.rows = rows

    def table(self, table_name: str):
        if table_name != "user_notifications":
            raise AssertionError(f"unexpected table: {table_name}")
        return _NotificationReadQuery(self)


class FeedbackNotificationTests(unittest.TestCase):
    def test_unread_summary_points_to_circle_tabs_and_concrete_targets(self):
        rows = [
            {
                "id": "chat-comment",
                "category": "community",
                "notification_type": "community_post_comment",
                "route_path": "/pages/home/index?tab=circle&section=community&communityTab=chat&postId=post-chat",
                "delivery_payload": {"post_id": "post-chat"},
            },
            {
                "id": "experience-like",
                "category": "community",
                "notification_type": "community_post_like",
                "route_path": "/pages/home/index?tab=circle&section=community&communityTab=experience&postId=post-exp",
                "delivery_payload": {"post_id": "post-exp"},
            },
            {
                "id": "mentor-order",
                "category": "consultation",
                "notification_type": "mentor_order_created",
                "delivery_payload": {"audience": "mentor", "order_id": "order-mentor"},
            },
            {
                "id": "applicant-message",
                "category": "consultation",
                "notification_type": "mentor_chat_message",
                "delivery_payload": {"sender_role": "mentor", "order_id": "order-applicant"},
            },
            {
                "id": "report-result",
                "category": "community",
                "notification_type": "community_report_status",
                "delivery_payload": {},
            },
        ]

        summary = notifications._summarize_unread_rows(rows)

        self.assertEqual(summary.total, 5)
        self.assertEqual(summary.circle, 4)
        self.assertEqual(summary.community_chat, 1)
        self.assertEqual(summary.community_experience, 1)
        self.assertEqual(summary.applicant_consultations, 1)
        self.assertEqual(summary.mentor_consultations, 1)
        self.assertEqual(summary.community_post_targets["chat"], {"post-chat": 1})
        self.assertEqual(summary.community_post_targets["experience"], {"post-exp": 1})
        self.assertEqual(summary.consultation_order_targets["mentor"], {"order-mentor": 1})
        self.assertEqual(summary.consultation_order_targets["applicant"], {"order-applicant": 1})

    def test_target_read_matching_does_not_clear_another_post_or_order(self):
        post_target = UserNotificationReadTargetRequest(target_type="community_post", target_id="post-1")
        order_target = UserNotificationReadTargetRequest(target_type="consultation_order", target_id="order-1")

        self.assertTrue(notifications._notification_matches_target({
            "notification_type": "community_post_comment",
            "delivery_payload": {"post_id": "post-1"},
        }, post_target))
        self.assertFalse(notifications._notification_matches_target({
            "notification_type": "community_post_comment",
            "delivery_payload": {"post_id": "post-2"},
        }, post_target))
        self.assertTrue(notifications._notification_matches_target({
            "notification_type": "community_post_like",
            "route_path": "/pages/home/index?tab=circle&communityTab=chat&postId=post-1",
            "delivery_payload": {},
        }, post_target))
        self.assertTrue(notifications._notification_matches_target({
            "notification_type": "mentor_order_status",
            "related_type": "mentor_consultation_order",
            "related_id": "order-1:accepted",
            "delivery_payload": {},
        }, order_target))
        self.assertFalse(notifications._notification_matches_target({
            "notification_type": "mentor_report_status",
            "delivery_payload": {"order_id": "order-1"},
        }, order_target))

    def test_legacy_community_notification_uses_related_id_as_post_target(self):
        target = UserNotificationReadTargetRequest(target_type="community_post", target_id="post-legacy")

        self.assertEqual(
            notifications._notification_target_id({
                "related_type": "community_post",
                "related_id": "post-legacy:comment:comment-1",
                "delivery_payload": {},
            }, "community_post"),
            "post-legacy",
        )
        self.assertTrue(notifications._notification_matches_target({
            "notification_type": "community_post_comment",
            "related_type": "community_post",
            "related_id": "post-legacy:comment:comment-1",
            "delivery_payload": {},
        }, target))

    def test_post_target_summary_aggregates_like_and_comment_notifications(self):
        summary = notifications._summarize_unread_rows([
            {
                "category": "community",
                "notification_type": "community_post_like",
                "related_type": "community_post",
                "related_id": "post-1:like:user-1",
                "delivery_payload": {},
            },
            {
                "category": "community",
                "notification_type": "community_post_comment",
                "related_type": "community_post",
                "related_id": "post-1:comment:comment-1",
                "delivery_payload": {},
            },
        ])

        self.assertEqual(summary.community_post_targets["chat"], {"post-1": 2})

    def test_read_target_marks_all_interactions_for_one_post_only(self):
        rows = [
            {
                "id": "like-1",
                "recipient_user_id": "user-1",
                "notification_type": "community_post_like",
                "related_type": "community_post",
                "related_id": "post-1:like:user-2",
                "delivery_payload": {},
                "read_at": None,
            },
            {
                "id": "comment-1",
                "recipient_user_id": "user-1",
                "notification_type": "community_post_comment",
                "related_type": "community_post",
                "related_id": "post-1:comment:comment-1",
                "delivery_payload": {},
                "read_at": None,
            },
            {
                "id": "comment-2",
                "recipient_user_id": "user-1",
                "notification_type": "community_post_comment",
                "related_type": "community_post",
                "related_id": "post-2:comment:comment-2",
                "delivery_payload": {},
                "read_at": None,
            },
        ]
        client = _NotificationReadClient(rows)
        payload = UserNotificationReadTargetRequest(target_type="community_post", target_id="post-1")

        with patch.object(notifications, "get_supabase_admin", return_value=client):
            response = notifications.mark_user_notification_target_read(payload, user_id="user-1")

        self.assertEqual(response.updated_count, 2)
        self.assertTrue(rows[0]["read_at"])
        self.assertTrue(rows[1]["read_at"])
        self.assertIsNone(rows[2]["read_at"])

    def test_legacy_consultation_notification_route_keeps_query_parameters(self):
        self.assertEqual(
            normalize_notification_route_path(
                "/pages/circle/mentor-chat?mentorId=mentor-1&orderId=order-1"
            ),
            "/pages-sub-consultation/consultation/mentor-chat?mentorId=mentor-1&orderId=order-1",
        )

        item = notifications._to_item({
            "id": "notification-1",
            "category": "consultation",
            "notification_type": "mentor_order_status",
            "title": "咨询状态更新",
            "route_path": "/pages/circle/my-consultations",
            "delivery_payload": {"route_path": "/pages/circle/my-consultations"},
        })
        self.assertEqual(item.route_path, "/pages-sub-consultation/consultation/my-consultations")
        self.assertEqual(
            item.delivery_payload["route_path"],
            "/pages-sub-consultation/consultation/my-consultations",
        )

    def test_resolving_feedback_creates_recipient_scoped_notification(self):
        client = _FeedbackClient({
            "id": "feedback-1",
            "user_id": "user-1",
            "content": "希望可以看到处理结果",
            "status": "open",
        })
        payload = AdminFeedbackStatusRequest(status="resolved", admin_note="该问题已修复，请更新后查看。")

        with (
            patch.object(admin, "get_supabase_admin", return_value=client),
            patch.object(admin, "_log_admin_action") as log_action,
            patch.object(admin, "create_user_notification") as create_notification,
        ):
            response = admin.admin_update_feedback_status(
                feedback_id="feedback-1",
                payload=payload,
                admin_profile={"id": "admin-1"},
            )

        self.assertEqual(response["status"], "resolved")
        self.assertEqual(response["admin_note"], "该问题已修复，请更新后查看。")
        self.assertIn(("id", "feedback-1"), client.query.filters)
        log_action.assert_called_once()
        create_notification.assert_called_once_with(
            client,
            recipient_user_id="user-1",
            category="official",
            notification_type="feedback_status_updated",
            title="你的反馈已处理完成",
            summary="该问题已修复，请更新后查看。",
            content="该问题已修复，请更新后查看。",
            related_type="beta_feedback",
            related_id="feedback-1:resolved",
            route_path="/pages/feedback/index",
        )

    def test_anonymous_feedback_status_update_does_not_create_notification(self):
        client = _FeedbackClient({
            "id": "feedback-anonymous",
            "user_id": None,
            "content": "匿名反馈",
            "status": "open",
        })
        payload = AdminFeedbackStatusRequest(status="reviewed", admin_note="已记录")

        with (
            patch.object(admin, "get_supabase_admin", return_value=client),
            patch.object(admin, "_log_admin_action"),
            patch.object(admin, "create_user_notification") as create_notification,
        ):
            admin.admin_update_feedback_status(
                feedback_id="feedback-anonymous",
                payload=payload,
                admin_profile={"id": "admin-1"},
            )

        create_notification.assert_not_called()


if __name__ == "__main__":
    unittest.main()
