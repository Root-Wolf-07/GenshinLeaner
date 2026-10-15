"""Conversation and Message database models.
"""

import uuid
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from backend.db.compat import (
    String, Text, JSON, ForeignKey, Index, Mapped, mapped_column, relationship
)
from backend.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.models.user import User


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), default="New Study Session", nullable=False)
    source_mode: Mapped[str] = mapped_column(
        String(50), default="both", nullable=False
    )  # uploaded, general, both
    selected_document_ids: Mapped[List[str]] = mapped_column(
        JSON, default=list, nullable=False
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at"
    )


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Validated citations returned by citation validation engine
    citations: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False
    )
    source_mode: Mapped[str] = mapped_column(String(50), default="both", nullable=False)
    message_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index("idx_conversation_created", "conversation_id", "created_at"),
    )
