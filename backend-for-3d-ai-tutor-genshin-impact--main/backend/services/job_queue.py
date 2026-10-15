"""Background Job Queue Service.
Manages asynchronous processing jobs with persistence, status tracking, and progress reporting.
"""

from __future__ import annotations

import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from backend.db.session import Session, SessionLocal
from backend.models.job import BackgroundJob

logger = logging.getLogger(__name__)

# Dedicated thread pool for async tasks
_executor = ThreadPoolExecutor(max_workers=4)


class JobQueueService:
    """Tracks and executes background tasks."""

    @staticmethod
    def create_job(
        owner_id: str,
        job_type: str,
        resource_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> BackgroundJob:
        """Create a new job record."""
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        job = BackgroundJob(
            id=str(uuid.uuid4()),
            owner_id=owner_id,
            job_type=job_type,
            status="pending",
            progress=0.0,
            resource_id=resource_id,
            result={},
            error_message=None,
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        if should_close:
            db.close()
        return job

    @staticmethod
    def update_job(
        job_id: str,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Update job status and progress in a clean DB session."""
        db = SessionLocal()
        try:
            job = db.query(BackgroundJob).filter(BackgroundJob.id == job_id).first()
            if job:
                if status:
                    job.status = status
                if progress is not None:
                    job.progress = progress
                if result is not None:
                    job.result = result
                if error_message is not None:
                    job.error_message = error_message
                job.updated_at = datetime.now(timezone.utc)
                db.commit()
        finally:
            db.close()

    @classmethod
    def submit_task(
        cls,
        job_id: str,
        fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Submit a task to execute asynchronously on thread pool."""
        def _wrapper():
            cls.update_job(job_id, status="running", progress=0.1)
            try:
                res = fn(*args, **kwargs)
                cls.update_job(
                    job_id,
                    status="completed",
                    progress=1.0,
                    result={"data": str(res) if res else "success"},
                )
            except Exception as e:
                logger.exception(f"Job {job_id} encountered error: {e}")
                cls.update_job(
                    job_id,
                    status="failed",
                    progress=1.0,
                    error_message=str(e),
                )

        _executor.submit(_wrapper)

    @classmethod
    def cancel_job(cls, job_id: str, owner_id: str, db: Session) -> Optional[BackgroundJob]:
        """Cancel a pending or running job."""
        job = db.query(BackgroundJob).filter(
            BackgroundJob.id == job_id,
            BackgroundJob.owner_id == owner_id,
        ).first()
        if not job:
            return None

        if job.status in ("pending", "running"):
            job.status = "cancelled"
            job.error_message = "Cancelled by user"
            db.commit()
            db.refresh(job)
        return job


# Global instance
job_queue = JobQueueService()
