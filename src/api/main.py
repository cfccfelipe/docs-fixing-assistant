"""
Main entry point for the Docs Fixing Assistant.
Orchestrates the lifecycle of the FastAPI application using flat imports.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from starlette.middleware.cors import CORSMiddleware

from api.config import settings
from api.dependencies import (
    fixing_module,
    full_pipeline_module,
    health_module,
    reordering_module,
    strategic_module,
)
from api.handlers.error_handler import register_error_handlers
from domain.utils.logging import setup_logging

API_V1_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    """
    Factory to initialize and configure the FastAPI application.
    """

    setup_logging()

    app = FastAPI(
        title="Docs Fixing Assistant",
        description="AI-driven assistant for repairing technical documentation debt.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,  # ty:ignore[invalid-argument-type]
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)

    app.include_router(
        router=health_module.router, prefix=API_V1_PREFIX, tags=["System"]
    )
    app.include_router(
        router=fixing_module.router, prefix=API_V1_PREFIX, tags=["Document Fixing"]
    )
    app.include_router(router=reordering_module.router, prefix=API_V1_PREFIX)
    app.include_router(strategic_module.router, prefix=API_V1_PREFIX)
    app.include_router(full_pipeline_module.router, prefix=API_V1_PREFIX)

    @app.get("/", include_in_schema=False)
    async def root_redirect():
        """
        Redirects the root URL to the interactive API documentation.
        """
        return RedirectResponse(url="/docs")

    return app


app = create_app()


def start():
    """
    Launcher for the project script.
    Uses centralized settings for host and port.
    """
    uvicorn.run(
        "api.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
    )
