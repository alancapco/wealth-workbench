import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger("app.main")

from app.api.health import router as health_router
from app.api.v1 import api_router
from app.core.authorization import AuthorizationError
from app.core.config import settings


def _outbox_worker_enabled() -> bool:
    """Default-on switch; set OUTBOX_WORKER_ENABLED=false to disable the loop."""
    return os.getenv("OUTBOX_WORKER_ENABLED", "true").strip().lower() not in {
        "0", "false", "no", "off",
    }


@asynccontextmanager
async def lifespan(_: FastAPI):
    worker_task: asyncio.Task | None = None
    if _outbox_worker_enabled():
        try:
            # Imported lazily so a broken worker module cannot break app startup.
            from app.services.actions.outbox_worker import run_outbox_worker, set_action_dispatcher
            from app.services.journey.oms import sandbox_oms_dispatcher
            set_action_dispatcher(sandbox_oms_dispatcher)
            worker_task = asyncio.create_task(run_outbox_worker())
            logger.info("Outbox worker started with sandbox OMS dispatcher")
        except Exception:
            logger.warning("Outbox worker startup failed; continuing without it", exc_info=True)
    try:
        yield
    finally:
        if worker_task is not None:
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.warning("Outbox worker exited with an error", exc_info=True)


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Relationship Manager Workbench API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.exception_handler(AuthorizationError)
async def authorization_error_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
    """Map authorization failures to 403, not a 500.

    AuthorizationError is raised both by route-level calls (e.g. check_book_access)
    and by shared dependencies. Without a handler Starlette returns a bare 500.
    """
    return JSONResponse(
        status_code=403,
        content={"detail": str(exc), "error_code": "FORBIDDEN"},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a structured, CORS-safe 500 instead of Starlette's bare text 500.

    Starlette's ServerErrorMiddleware wraps the app *outside* CORSMiddleware, so
    an unhandled exception bypasses the CORS layer entirely. The browser then
    hides the response from axios and reports "Network Error", hiding the real
    status and message. Echo the allowed origin explicitly so any unexpected
    failure still reaches the UI as a readable HTTP error.
    """
    # Pass exc_info explicitly: inside an exception handler sys.exc_info() may
    # already be cleared, which would log "NoneType: None" instead of the cause.
    logger.error(
        "Unhandled error on %s %s",
        request.method,
        request.url.path,
        exc_info=exc,
    )
    origin = request.headers.get("origin")
    headers: dict[str, str] = {}
    if origin and origin in settings.BACKEND_CORS_ORIGINS:
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Vary": "Origin",
        }
    return JSONResponse(
        status_code=500,
        content={
            "detail": {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"{type(exc).__name__}: {exc}",
                    "retryable": False,
                }
            }
        },
        headers=headers,
    )


# Health endpoints are registered without prefix
app.include_router(health_router, prefix="")
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root() -> dict:
    return {"message": settings.PROJECT_NAME, "version": "1.0.0", "status": "active"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
