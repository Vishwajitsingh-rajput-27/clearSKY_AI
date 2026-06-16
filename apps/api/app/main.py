from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    auth,
    benchmarks,
    demo,
    files,
    health,
    inference,
    jobs,
    model_registry,
    projects,
    research,
    scenes,
    users,
)
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import register_middleware
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Operational API foundation for LISS-IV cloud removal and reconstruction.",
        docs_url=f"{settings.api_prefix}/docs",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_middleware(app)
    register_exception_handlers(app)

    app.include_router(health.router, prefix=settings.api_prefix, tags=["health"])
    app.include_router(auth.router, prefix=f"{settings.api_prefix}/auth", tags=["auth"])
    app.include_router(users.router, prefix=f"{settings.api_prefix}/users", tags=["users"])
    app.include_router(projects.router, prefix=f"{settings.api_prefix}/projects", tags=["projects"])
    app.include_router(scenes.router, prefix=f"{settings.api_prefix}/scenes", tags=["scenes"])
    app.include_router(jobs.router, prefix=f"{settings.api_prefix}/jobs", tags=["jobs"])
    app.include_router(files.router, prefix=f"{settings.api_prefix}/files", tags=["files"])
    app.include_router(demo.router, prefix=f"{settings.api_prefix}/demo", tags=["demo"])
    app.include_router(
        benchmarks.router,
        prefix=f"{settings.api_prefix}/benchmarks",
        tags=["benchmarks"],
    )
    app.include_router(
        model_registry.router,
        prefix=f"{settings.api_prefix}/model-registry",
        tags=["model-registry"],
    )
    app.include_router(
        research.router,
        prefix=f"{settings.api_prefix}/research",
        tags=["research"],
    )
    app.include_router(
        inference.router,
        prefix=f"{settings.api_prefix}/inference",
        tags=["inference"],
    )

    return app


app = create_app()
