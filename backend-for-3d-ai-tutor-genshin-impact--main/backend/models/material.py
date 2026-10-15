"""StudyMaterial database model.
"""

import uuid
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from backend.db.compat import (
    String, Text, JSON, ForeignKey, Index, Mapped, mapped_column, relationship
)
from backend.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.models.user import User


class StudyMaterial(Base, TimestampMixin):
    __tablename__ = "study_materials"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    material_type: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False
    )  # study_notes, summary, revision_sheet, flashcards, practice_questions, mock_exam, tutorial, comparison, formula_sheet, glossary
    student_level: Mapped[str] = mapped_column(String(50), default="undergraduate", nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), default="intermediate", nullable=False)
    content_format: Mapped[str] = mapped_column(String(50), default="structured_json", nullable=False)

    # Structured JSON content (sections, flashcards list, question items, rubrics, etc.)
    content: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Rendered Markdown representation compatible with frontend Markdown & KaTeX renderers
    raw_markdown: Mapped[str] = mapped_column(Text, default="", nullable=False)

    source_mode: Mapped[str] = mapped_column(String(50), default="both", nullable=False)
    document_ids: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)

    # Validated citations
    citations: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)

    status: Mapped[str] = mapped_column(String(50), default="ready", index=True, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="materials")

    __table_args__ = (
        Index("idx_material_owner_topic", "owner_id", "topic"),
    )
