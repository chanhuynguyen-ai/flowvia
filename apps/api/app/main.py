import logging
import uuid

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import check_database, get_db
from app.core.request_context import request_id_var
from app.modules.identity.router import router as identity_router

APP_VERSION = "0.1.0"

settings = get_settings()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="Flowvia API",
    version=APP_VERSION,
    description="Platform foundation for Flowvia. HR remains an optional business pack.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token", "Idempotency-Key", "If-Match"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    token = request_id_var.set(request_id)
    request.state.request_id = request_id
    try:
        response = await call_next(request)
    finally:
        request_id_var.reset(token)
    response.headers["X-Request-ID"] = request_id
    return response


def _error_response(request: Request, status_code: int, code: str, message: str, details=None):
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "details": jsonable_encoder(details),
            "request_id": getattr(request.state, "request_id", ""),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    message = detail if isinstance(detail, str) else "Request failed"
    return _error_response(request, exc.status_code, f"http_{exc.status_code}", message, detail)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return _error_response(
        request,
        422,
        "validation_error",
        "Request validation failed",
        exc.errors(),
    )


@app.get("/health", tags=["system"])
def health():
    return {
        "status": "ok",
        "service": "flowvia-api",
        "version": APP_VERSION,
        "environment": settings.app_env,
    }


@app.get("/ready", tags=["system"])
def ready(db: Session = Depends(get_db)):
    check_database(db)
    return {"status": "ready", "database": "ok"}


app.include_router(identity_router, prefix="/api/v1")
