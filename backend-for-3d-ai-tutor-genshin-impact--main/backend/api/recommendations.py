"""Study Recommendations API endpoint.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.dependencies import get_current_user
from backend.models.user import User
from backend.schemas.progress import RecommendationsResponse
from backend.services.recommendations import recommendations_service

router = APIRouter(tags=["Recommendations"])


@router.get("/recommendations", response_model=RecommendationsResponse)
def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve actionable, transparent study recommendations grounded in stored performance data."""
    recs = recommendations_service.get_recommendations(user_id=current_user.id, db=db)
    return RecommendationsResponse(recommendations=recs)
