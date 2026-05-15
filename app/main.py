from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.db.database import init_db
from app.db.database import get_db
from app.core.config import settings

from fastapi.middleware.cors import CORSMiddleware
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
    await init_db()
    yield
    logger.info("Shutting down application...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    version="1.4.2-Prod"
)

# Configure CORS for Production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)

@app.get("/")
async def root():
    return {"message": "Advanced Asynchronous Auth System is Running"}
