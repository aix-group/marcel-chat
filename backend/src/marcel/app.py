from fastapi import FastAPI, Request, status
from fastapi.concurrency import asynccontextmanager
from fastapi.responses import JSONResponse
from starlette.applications import Starlette
from starlette.types import Lifespan

from marcel.admin.auth import router as auth_router
from marcel.admin.routes import router as admin_router
from marcel.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan event. Runs before any requests are taken (before yield) and before shutdown (after yield).
    """
    from marcel.experiments.hybrid_pipeline import HybridPipeline

    pipeline = HybridPipeline()
    yield {"pipeline": pipeline}


async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return a json dict that aligns with other API errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error. Please try again."},
    )


def build_app(lifespan: Lifespan[Starlette] = lifespan):
    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    app.include_router(auth_router, prefix="/admin")
    app.include_router(admin_router, prefix="/admin")
    app.add_exception_handler(Exception, handler=global_exception_handler)
    return app
