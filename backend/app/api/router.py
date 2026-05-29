from fastapi import APIRouter

from app.api.v1.agent import router as agent_router
from app.api.v1.auth import router as auth_router
from app.api.v1.games import router as games_router
from app.api.v1.memory import router as memory_router
from app.api.v1.reports import router as reports_router
from app.api.v1.vision import router as vision_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(vision_router)
api_router.include_router(games_router)
api_router.include_router(reports_router)
api_router.include_router(memory_router)
api_router.include_router(agent_router)

