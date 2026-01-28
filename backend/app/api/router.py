from fastapi import APIRouter

from app.api.routes import events, products, recommendations, admin, health

api_router = APIRouter()

# Include all route modules
api_router.include_router(events.router)
api_router.include_router(products.router)
api_router.include_router(recommendations.router)
api_router.include_router(admin.router)
api_router.include_router(health.router)
