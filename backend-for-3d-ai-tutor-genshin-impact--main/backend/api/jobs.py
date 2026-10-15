"""Background Job status and cancellation API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.dependencies import get_current_user
from backend.models.job import BackgroundJob
from backend.models.user import User
from backend.schemas.jobs import JobResponse
from backend.services.job_queue import job_queue

router = APIRouter(tags=["Background Jobs"])


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check processing status and progress of an asynchronous background job."""
    job = (
        db.query(BackgroundJob)
        .filter(BackgroundJob.id == job_id, BackgroundJob.owner_id == current_user.id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@router.post("/jobs/{job_id}/cancel", response_model=JobResponse)
def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel a pending or running background job."""
    job = job_queue.cancel_job(job_id=job_id, owner_id=current_user.id, db=db)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or cannot be cancelled.")
    return job
