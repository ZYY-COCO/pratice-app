from datetime import datetime, timedelta, timezone
import unittest

from app.routes import membership
from app.schemas.membership import MembershipPlan


class MembershipRenewalTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc)
        self.monthly_plan = MembershipPlan(
            code="pro_monthly",
            name="月卡",
            price_cents=8800,
            price_label="88元/月",
            duration_days=31,
            description="测试月卡",
        )

    def test_active_membership_renews_from_existing_expiry(self):
        old_expiry = self.now + timedelta(days=12)
        started_at, expires_at = membership._resolve_membership_period(
            {
                "membership_status": "active",
                "membership_started_at": (self.now - timedelta(days=19)).isoformat(),
                "membership_expires_at": old_expiry.isoformat(),
            },
            self.monthly_plan,
            now=self.now,
        )

        self.assertEqual(started_at, self.now - timedelta(days=19))
        self.assertEqual(expires_at, old_expiry + timedelta(days=31))

    def test_expired_membership_restarts_from_payment_time(self):
        started_at, expires_at = membership._resolve_membership_period(
            {
                "membership_status": "active",
                "membership_started_at": (self.now - timedelta(days=70)).isoformat(),
                "membership_expires_at": (self.now - timedelta(seconds=1)).isoformat(),
            },
            self.monthly_plan,
            now=self.now,
        )

        self.assertEqual(started_at, self.now)
        self.assertEqual(expires_at, self.now + timedelta(days=31))


if __name__ == "__main__":
    unittest.main()
