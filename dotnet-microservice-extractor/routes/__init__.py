from fastapi import APIRouter
from .migration_routes import router as migration_router



api_router = APIRouter()
api_router.include_router(migration_router, prefix="/migration", tags=["Migration"])