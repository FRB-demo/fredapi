"""Main FastAPI application for the Economic Research Platform."""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.config import settings
from app.routers import data, forecasting, chat, datasets

# --- Structured logging (B-2) ---
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("econsight")


# --- Security headers middleware (S-11) ---
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.is_production:
            response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response


# --- Request logging middleware (B-2) ---
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        return response


# --- Simple API key auth middleware (S-2) ---
class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Optional API key authentication. Skips if no API_KEY is configured."""

    EXEMPT_PATHS = {"/api/v1/health", "/api/health", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next):
        if not settings.api_key:
            return await call_next(request)
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)
        provided = request.headers.get("X-API-Key", "")
        if provided != settings.api_key:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    yield
    # Cleanup: close shared httpx client on shutdown
    from app.services.fred_service import _http_client
    if _http_client and not _http_client.is_closed:
        await _http_client.aclose()
        logger.info("Closed shared HTTP client")


app = FastAPI(
    title="EconSight - Economic Research Platform",
    description="Interactive economic research and forecasting platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware (applied in reverse order)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ApiKeyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,  # S-1: explicit allowlist
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting (S-9)
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded

    limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_requests}/{settings.rate_limit_window} seconds"])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    from slowapi.middleware import SlowAPIMiddleware
    app.add_middleware(SlowAPIMiddleware)
except ImportError:
    logger.warning("slowapi not installed; rate limiting disabled")

# Routers with /api/v1/ prefix (B-5: API versioning)
app.include_router(data.router, prefix="/api/v1/data", tags=["Data"])
app.include_router(forecasting.router, prefix="/api/v1/forecast", tags=["Forecasting"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(datasets.router, prefix="/api/v1/datasets", tags=["Datasets"])

# Backward-compatible unversioned routes
app.include_router(data.router, prefix="/api/data", tags=["Data (compat)"], include_in_schema=False)
app.include_router(forecasting.router, prefix="/api/forecast", tags=["Forecasting (compat)"], include_in_schema=False)
app.include_router(chat.router, prefix="/api/chat", tags=["Chat (compat)"], include_in_schema=False)
app.include_router(datasets.router, prefix="/api/datasets", tags=["Datasets (compat)"], include_in_schema=False)


@app.get("/api/v1/health")
@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "data_mode": "demo" if settings.is_demo_mode else "live",
        "environment": settings.environment,
    }
