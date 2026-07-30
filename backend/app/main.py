import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import config
from app.db import init_db
from app.routes.interviews import router as interviews_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="AI Interviewer API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.CORS_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interviews_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception in request")
    # Provider calls (retried once already in services/retry.py) are the expected source of
    # transient failures here - surface those as a sanitized 502 rather than a bare 500, so the
    # frontend can tell "try again shortly" apart from "this is a real bug". Anything else still
    # falls through as a 500 rather than being mislabeled as a provider issue.
    is_provider_error = type(exc).__module__.startswith(("openai", "google.genai", "anthropic"))
    if is_provider_error:
        return JSONResponse(
            status_code=502,
            content={"detail": "The AI provider is temporarily unavailable. Please try again."},
        )
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})
