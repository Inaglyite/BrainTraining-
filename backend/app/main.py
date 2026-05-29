from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import time

from app.api.router import api_router
from app.core.config import settings
from app.core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name, version="1.0.0")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed_ms = (time.time() - start) * 1000
    logger.info("%s %s -> %d (%.0fms)", request.method, request.url.path, response.status_code, elapsed_ms)
    return response
frontend_dist = Path(__file__).resolve().parents[2] / "dist"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(f"{settings.api_prefix}/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}


app.include_router(api_router, prefix=settings.api_prefix)


def _safe_dist_file(path: str) -> Path | None:
    if not path:
        return None
    candidate = (frontend_dist / path).resolve()
    if frontend_dist.resolve() not in candidate.parents and candidate != frontend_dist.resolve():
        return None
    if candidate.is_file():
        return candidate
    return None


@app.get("/", include_in_schema=False)
def serve_frontend_index() -> FileResponse:
    return FileResponse(frontend_dist / "index.html")


@app.get("/{path:path}", include_in_schema=False)
def serve_frontend(path: str) -> FileResponse:
    # Keep SPA routes working by falling back to index.html when file is missing.
    file_path = _safe_dist_file(path)
    if file_path is not None:
        return FileResponse(file_path)
    return FileResponse(frontend_dist / "index.html")


