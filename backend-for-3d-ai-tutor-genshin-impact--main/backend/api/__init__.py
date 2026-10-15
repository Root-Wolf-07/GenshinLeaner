"""API router aggregator.
Includes all modular sub-routers under the common API prefix.
"""

from fastapi import APIRouter

from backend.api.health import router as health_router
from backend.api.auth import router as auth_router
from backend.api.dashboard import router as dashboard_router
from backend.api.documents import router as documents_router
from backend.api.chat import router as chat_router
from backend.api.materials import router as materials_router
from backend.api.quizzes import router as quizzes_router
from backend.api.progress import router as progress_router
from backend.api.recommendations import router as recommendations_router
from backend.api.media import router as media_router
from backend.api.jobs import router as jobs_router
from backend.api.tutors import router as tutors_router
from backend.api.tutor_sessions import router as tutor_sessions_router
from backend.api.voice import router as voice_router
from backend.api.gamification import router as gamification_router
from backend.api.interactive_events import router as interactive_events_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(dashboard_router)
api_router.include_router(documents_router)
api_router.include_router(chat_router)
api_router.include_router(materials_router)
api_router.include_router(quizzes_router)
api_router.include_router(progress_router)
api_router.include_router(recommendations_router)
api_router.include_router(media_router)
api_router.include_router(jobs_router)
api_router.include_router(tutors_router)
api_router.include_router(tutor_sessions_router)
api_router.include_router(voice_router)
api_router.include_router(gamification_router)
api_router.include_router(interactive_events_router)

__all__ = ["api_router"]
