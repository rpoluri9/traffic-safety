"""Application entry point."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api.v1 import alerts, dashboard, drivers, pages, telemetry, trips, vehicles, violations
from .core.config import settings
from .db import base  # noqa: F401  (register models)
from .db.base import Base
from .db.session import engine


def create_app(*, init_db: bool = True) -> FastAPI:
    """Build the FastAPI app.

    init_db=False is used by the test suite, which manages its own
    (SQLite) database instead of the configured database server.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if init_db:
            Base.metadata.create_all(bind=engine)
        yield

    app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")

    app.include_router(pages.router)
    app.include_router(drivers.router, prefix="/api/v1")
    app.include_router(vehicles.router, prefix="/api/v1")
    app.include_router(trips.router, prefix="/api/v1")
    app.include_router(telemetry.router, prefix="/api/v1")
    app.include_router(violations.router, prefix="/api/v1")
    app.include_router(alerts.router, prefix="/api/v1")
    app.include_router(dashboard.router, prefix="/api/v1")

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok"}

    return app


app = create_app()
