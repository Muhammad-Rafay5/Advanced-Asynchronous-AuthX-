from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.core.config import settings

from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.rate_limit import limiter
from app.redis.blacklist import blacklist_service
import logging

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Database...")
    # await init_db()
    logger.info("Initializing Redis Blacklist Service...")
    await blacklist_service.initialize()
    yield
    logger.info("Shutting down application...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    version="1.4.2-Prod"
)

# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

from fastapi import Request, Response
@app.middleware("http")
async def manual_cors_middleware(request: Request, call_next):
    # 1. Handle OPTIONS (Preflight) requests
    if request.method == "OPTIONS":
        response = Response()
    else:
        response = await call_next(request)

    # 2. Force the Origin
    origin = request.headers.get("origin")
    allowed_origins = [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000"
    ]

    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept, X-Requested-With"
    
    return response

app.include_router(auth_router)
app.include_router(users_router)


@app.get("/")
async def root():
    return {"message": "Advanced Asynchronous Auth System is Running"}
