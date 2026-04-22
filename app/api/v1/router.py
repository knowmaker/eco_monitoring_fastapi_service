from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.monitoring_posts import router as monitoring_posts_router


api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(monitoring_posts_router)
