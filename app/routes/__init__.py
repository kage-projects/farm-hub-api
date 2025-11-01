from fastapi import APIRouter
from app.routes import user_routes, project_routes

api_router = APIRouter()

api_router.include_router(
    user_routes.router,
    prefix="/api/v1",
    tags=["authentication"]
)

api_router.include_router(
    project_routes.router,
    prefix="/api/v1",
    tags=["projects"]
)