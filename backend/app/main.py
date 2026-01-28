from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import api_router
from app.config import settings
from app.core.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup: Create tables if they don't exist
    # Note: In production, use Alembic migrations instead
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title=settings.app_name,
    description="""
    ShopSmart E-Commerce Recommendation System API

    ## Features
    - **Event Tracking**: Track user interactions (view, add_to_cart, purchase)
    - **Personalized Recommendations**: Get recommendations based on user history
    - **Similar Products**: Find products similar to a given product
    - **Trending Products**: Discover what's popular right now
    - **Product Search**: Search and filter products

    ## Recommendation Strategies
    1. **Personalized**: Item-to-item collaborative filtering for users with history
    2. **Cold Start (Category)**: Trending by category for new users with category context
    3. **Trending**: Global trending for completely new users
    """,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }
