# backend/app/api/api.py
from fastapi import APIRouter

from app.api.v1.endpoints import recommendations, auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(recommendations.router, prefix="/movies", tags=["movies"])