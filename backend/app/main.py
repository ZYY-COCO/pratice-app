from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import ai, answers, auth, feedback, questions, reports, wrong_questions


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="港澳台考研初试刷题 App API", version="0.1.0")

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
    app.include_router(reports.router)
    app.include_router(feedback.router)
    app.include_router(ai.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
