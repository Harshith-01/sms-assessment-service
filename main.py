import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy.exc import IntegrityError
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from api.routes import router
from core.config import ALLOWED_HOSTS, ALLOWED_ORIGINS, SERVICE_NAME
from core.db_errors import db_integrity_http_exception


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Set security-focused default response headers."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(title="Assessment Service", version="1.0.0")
app.state.limiter = limiter

app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS else [],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Internal-Service"],
)

trusted_hosts = list(ALLOWED_HOSTS) if ALLOWED_HOSTS else []
for host in ["localhost", "127.0.0.1", "testserver"]:
    if host not in trusted_hosts:
        trusted_hosts.append(host)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=trusted_hosts,
)


@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 5_000_000:
        return JSONResponse(status_code=413, content={"detail": "Payload too large"})
    return await call_next(request)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Too many requests"})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"detail": exc.errors()})


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    parsed = db_integrity_http_exception(exc)
    return JSONResponse(status_code=parsed.status_code, content={"detail": parsed.detail})


app.include_router(router)


@app.get("/health")
@limiter.limit("30/minute")
def health_check(request: Request):
    return {"service": SERVICE_NAME, "status": "ok"}
