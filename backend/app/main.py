import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import admin, ai, answers, auth, community, favorites, feedback, formulas, home_content, major_catalog, membership, mentor_admin, mentor_consultation, notifications, official_messages, questions, reports, school_announcements, wrong_questions
from app.services.mentor_consultation_lifecycle import settle_expired_mentor_consultation_orders


logger = logging.getLogger(__name__)


async def _mentor_consultation_lifecycle_loop(interval_seconds: int) -> None:
    """Keep paid timeout/refund outcomes independent from a browser refresh."""

    delay = max(15, min(int(interval_seconds or 60), 3600))
    while True:
        try:
            settled = await asyncio.to_thread(settle_expired_mentor_consultation_orders)
            if settled:
                logger.info("Applied mentor consultation lifecycle updates (count=%s)", settled)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            # A transient upstream fault should not take down the API. The next
            # periodic pass retries and the conditional state transitions remain safe.
            logger.warning("Mentor consultation lifecycle sweep failed (error_type=%s)", type(exc).__name__)
        await asyncio.sleep(delay)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    task = asyncio.create_task(
        _mentor_consultation_lifecycle_loop(get_settings().mentor_consultation_lifecycle_interval_seconds),
        name="mentor-consultation-lifecycle",
    )
    try:
        yield
    finally:
        task.cancel()
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
    )

    app.include_router(auth.router)
    app.include_router(questions.router)
    app.include_router(answers.router)
    app.include_router(wrong_questions.router)
    app.include_router(favorites.router)
    app.include_router(community.router)
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
    app.include_router(official_messages.router)
    app.include_router(official_messages.admin_router)
    app.include_router(admin.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
