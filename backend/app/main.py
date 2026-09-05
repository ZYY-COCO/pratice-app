import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import adaptive_practice, admin, ai, answers, auth, circle_resources, community, favorites, feedback, formulas, home_content, major_catalog, membership, mentor_admin, mentor_consultation, mock_exams, notifications, official_messages, questions, reports, school_announcements, wallet, wrong_questions
from app.services.mentor_consultation_lifecycle import settle_expired_mentor_consultation_orders
from app.services.user_notifications import deliver_pending_user_notifications
from app.services.wallet_ledger import reconcile_consultation_wallet_ledger


logger = logging.getLogger(__name__)


async def _mentor_consultation_lifecycle_loop(interval_seconds: int) -> None:
    """Keep paid timeout/refund outcomes independent from a browser refresh."""

    delay = max(15, min(int(interval_seconds or 60), 3600))
    while True:
        try:
            settled = await asyncio.to_thread(settle_expired_mentor_consultation_orders)
            ledger_updates = await asyncio.to_thread(reconcile_consultation_wallet_ledger)
            if settled or ledger_updates:
                logger.info(
                    "Applied mentor consultation background updates (lifecycle=%s ledger=%s)",
                    settled,
                    ledger_updates,
                )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            # A transient upstream fault should not take down the API. The next
            # periodic pass retries and the conditional state transitions remain safe.
            logger.warning("Mentor consultation lifecycle sweep failed (error_type=%s)", type(exc).__name__)
        await asyncio.sleep(delay)


async def _user_notification_outbox_loop(interval_seconds: int) -> None:
    """Deliver recipient notifications independently from the source request."""

    delay = max(5, min(int(interval_seconds or 10), 300))
    while True:
        try:
            delivered = await asyncio.to_thread(deliver_pending_user_notifications)
            if delivered:
                logger.info("Delivered user notification outbox rows (count=%s)", delivered)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("User notification outbox sweep failed (error_type=%s)", type(exc).__name__)
        await asyncio.sleep(delay)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    lifecycle_task = asyncio.create_task(
        _mentor_consultation_lifecycle_loop(get_settings().mentor_consultation_lifecycle_interval_seconds),
        name="mentor-consultation-lifecycle",
    )
    notification_task = asyncio.create_task(
        _user_notification_outbox_loop(get_settings().user_notification_outbox_interval_seconds),
        name="user-notification-outbox",
    )
    try:
        yield
    finally:
        for task in (lifecycle_task, notification_task):
            task.cancel()
        for task in (lifecycle_task, notification_task):
            try:
                await task
            except asyncio.CancelledError:
                pass


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="港澳台考研初试刷题 App API", version="0.1.0", lifespan=_lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=list(answers.RESPONSIVE_GRADE_HEADER_NAMES),
    )

    app.include_router(auth.router)
    app.include_router(questions.router)
    app.include_router(adaptive_practice.router)
    app.include_router(mock_exams.router)
    app.include_router(answers.router)
    app.include_router(wrong_questions.router)
    app.include_router(favorites.router)
    app.include_router(community.router)
    app.include_router(circle_resources.router)
    app.include_router(mentor_consultation.router)
    app.include_router(mentor_admin.router)
    app.include_router(reports.router)
    app.include_router(feedback.router)
    app.include_router(membership.router)
    app.include_router(ai.router)
    app.include_router(formulas.router)
    app.include_router(major_catalog.router)
    app.include_router(school_announcements.router)
    app.include_router(home_content.router)
    app.include_router(notifications.router)
    app.include_router(wallet.router)
    app.include_router(official_messages.router)
    app.include_router(official_messages.admin_router)
    app.include_router(circle_resources.admin_router)
    app.include_router(mock_exams.admin_router)
    app.include_router(admin.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
