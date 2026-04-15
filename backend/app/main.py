"""
LEARN: The FastAPI Application Entry Point
==========================================
This is equivalent to src/index.js in the Node.js version.

Key differences from Express:
  - `FastAPI()` instead of `express()`
  - Middleware uses `app.add_middleware()` instead of `app.use()`
  - Routers are added with `app.include_router()` instead of `app.use()`
  - FastAPI auto-generates docs at /docs (Swagger UI) and /redoc
  - Startup/shutdown events use `@app.on_event()` or lifespan context

The biggest win: go to http://localhost:8000/docs after starting
and you get a FULLY INTERACTIVE API explorer — automatically generated
from your type hints and Pydantic schemas. No extra work needed.
"""
from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import engine, Base

# Import all routers
from app.routers import auth, listings, rentals, orders, services, messages, reviews, notifications, payments, reports, users

# LEARN: `lifespan` is a modern way to run setup/teardown code.
# It replaces @app.on_event("startup") / @app.on_event("shutdown")
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────
    print("\n🎓 CampusLoop FastAPI starting up...")

    # Create tables if they don't exist
    # In production, use Alembic migrations instead
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print(f"📡 Environment: {settings.APP_ENV}")
    print(f"📖 API Docs: http://localhost:{settings.APP_PORT}/docs\n")

    yield  # App runs here

    # ── Shutdown ─────────────────────────────
    await engine.dispose()
    print("👋 CampusLoop shutting down...")


# LEARN: Rate limiter — same concept as express-rate-limit
limiter = Limiter(key_func=get_remote_address)

# ─── Create FastAPI App ───────────────────────
app = FastAPI(
    title="CampusLoop API",
    description="P2P rental, marketplace, and services platform for verified college students",
    version="1.0.0",
    lifespan=lifespan,
    # In production, hide the docs
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
)

# ─── Rate Limiting ────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── CORS ────────────────────────────────────
# LEARN: CORS (Cross-Origin Resource Sharing) lets your frontend
# (running on localhost:3000) talk to the backend (localhost:8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CLIENT_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Include Routers ─────────────────────────
# LEARN: `prefix="/api/v1"` prepends this to all routes in the router
# `tags` groups them in the Swagger docs
API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(users.router, prefix=API_PREFIX)
app.include_router(listings.router, prefix=API_PREFIX)
app.include_router(rentals.router, prefix=API_PREFIX)
app.include_router(orders.router, prefix=API_PREFIX)
app.include_router(services.router, prefix=API_PREFIX)
app.include_router(messages.router, prefix=API_PREFIX)
app.include_router(reviews.router, prefix=API_PREFIX)
app.include_router(notifications.router, prefix=API_PREFIX)
app.include_router(payments.router, prefix=API_PREFIX)
app.include_router(reports.router, prefix=API_PREFIX)


# ─── Health Check ────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    return {
        "status": "ok",
        "service": "CampusLoop API",
        "version": "1.0.0",
        "environment": settings.APP_ENV,
    }