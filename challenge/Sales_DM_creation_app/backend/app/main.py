"""
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.security import APIError
from app.core.exceptions import api_exception_handler, general_exception_handler
from app.api.dm import router as dm_router
from app.db.base import Base, engine


# Create tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    pass


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan,
)

# CORS middleware - 開発環境ではすべてのオリジンを許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では settings.cors_origins に変更
    allow_credentials=False,  # allow_origins=["*"] の場合は False にする必要がある
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dm_router)

# Exception handlers
app.add_exception_handler(APIError, api_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": settings.version,
        "app_name": settings.app_name,
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Insight DM Master API",
        "version": settings.version,
        "docs": "/docs",
    }
