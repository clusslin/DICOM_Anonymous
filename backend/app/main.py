"""
DICOM Anonymization Platform - Main Application
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.core.config import settings
from app.core.database import init_db, async_session
from app.core.security import get_password_hash
from app.models.user import User
from app.api import auth, servers, query, jobs, settings as settings_api
from app.services.settings_service import SettingsService, load_settings_cache

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def create_default_admin():
    """Create default admin user if not exists"""
    async with async_session() as db:
        result = await db.execute(
            select(User).where(User.username == settings.DEFAULT_ADMIN_USERNAME)
        )
        existing_user = result.scalar_one_or_none()

        if not existing_user:
            admin_user = User(
                username=settings.DEFAULT_ADMIN_USERNAME,
                hashed_password=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
                is_admin=True,
                is_active=True
            )
            db.add(admin_user)
            await db.commit()
            logger.info(f"Created default admin user: {settings.DEFAULT_ADMIN_USERNAME}")


async def initialize_system_settings():
    """Initialize system settings with defaults"""
    async with async_session() as db:
        service = SettingsService(db)
        await service.initialize_defaults()
        await load_settings_cache(db)
        logger.info("System settings initialized")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info("Starting DICOM Anonymization Platform...")
    await init_db()
    await create_default_admin()
    await initialize_system_settings()
    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="DICOM影像匿名化平台 - 從DICOM伺服器下載影像並進行匿名化處理",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api")
app.include_router(servers.router, prefix="/api")
app.include_router(query.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(settings_api.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
