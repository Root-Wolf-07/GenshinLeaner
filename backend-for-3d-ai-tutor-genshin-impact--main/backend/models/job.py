"""BackgroundJob database model for tracking async tasks.
"""

import uuid
from typing import Dict, Any, Optional
from backend.db.compat import (
    String, Float, Text, JSON, ForeignKey, Index, Mapped, mapped_column
)
from backend.db.base import Base, TimestampMixin


class BackgroundJob(Base, TimestampMixin):
    __tablename__ = "background_jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)  # document_ingestion, material_generation, etc.
    status: Mapped[str] = mapped_column(
        String(50), default="pending", index=True, nullable=False
    )  # pending, running, completed, failed, cancelled
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0.0 to 1.0
    resource_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    result: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_job_owner_status", "owner_id", "status"),
    )
