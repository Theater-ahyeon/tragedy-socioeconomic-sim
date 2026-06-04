"""FastAPI application factory for the Tragedy simulation server."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tragedy.api.routes import config, metrics, simulation
from tragedy.api.websocket import get_stream, router as ws_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown."""
    # Startup
    logger.info("Tragedy simulation server starting...")
    stream = get_stream()
    stream.start()

    yield

    # Shutdown
    logger.info("Tragedy simulation server shutting down...")
    stream.stop()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        A fully configured FastAPI instance ready to serve.
    """
    app = FastAPI(
        title="Tragedy — Socio-Economic Simulation",
        description="Agent-Based Computational Economics simulation engine with real-time visualization",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS — allow frontend dev server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",  # Vite dev server
            "http://localhost:3000",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount routers
    app.include_router(simulation.router)
    app.include_router(config.router)
    app.include_router(metrics.router)
    app.include_router(ws_router)

    @app.get("/")
    async def root():
        return {
            "name": "Tragedy",
            "version": "0.1.0",
            "description": "Agent-Based Socio-Economic Simulation System",
            "docs": "/docs",
            "websocket": "/ws/simulation",
        }

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


def main() -> None:
    """Entry point for `tragedy-server` command."""
    import uvicorn

    from tragedy.utils.logging import setup_logging

    setup_logging(level="INFO", fmt="console")

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
