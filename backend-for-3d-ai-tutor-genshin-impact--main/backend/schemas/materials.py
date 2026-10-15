"""Study Material schemas for Study Material Studio.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from backend.schemas.compat import BaseModel, Field
from backend.schemas.chat import Citation

MaterialTypeEnum = Literal[
    "study_notes",
    "summary",
    "revision_sheet",
    "flashcards",
    "practice_questions",
    "mock_exam",
    "tutorial",
    "comparison",
    "formula_sheet",
    "glossary",
]


class StudyMaterialGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=255)
    material_type: MaterialTypeEnum = "study_notes"
    document_ids: Optional[List[str]] = Field(default_factory=list)
    student_level: Optional[str] = "undergraduate"
    difficulty: Optional[str] = "intermediate"  # beginner, intermediate, advanced
    detail_level: Optional[str] = "comprehensive"  # brief, moderate, comprehensive
    language: Optional[str] = "English"
    approximate_length: Optional[str] = "medium"  # short, medium, in_depth
    source_mode: Literal["uploaded", "general", "both"] = "both"
    learning_objectives: Optional[List[str]] = None
    character_id: Optional[str] = None
    subject: Optional[str] = None
    include_worked_examples: bool = True
    include_formulas: bool = True
    include_practice_questions: bool = True


class StudyMaterialUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    raw_markdown: Optional[str] = None


class SectionRegenerateRequest(BaseModel):
    section_index: int = Field(..., ge=0)
    section_title: str
    additional_instructions: Optional[str] = None


class MaterialExportRequest(BaseModel):
    format: Literal["markdown", "txt", "html"] = "markdown"


class MaterialExportResponse(BaseModel):
    material_id: str
    format: str
    filename: str
    content: str


class StudyMaterialResponse(BaseModel):
    id: str
    owner_id: str
    title: str
    topic: str
    material_type: str
    student_level: str
    difficulty: str
    content_format: str
    content: Dict[str, Any]
    raw_markdown: str
    source_mode: str
    document_ids: List[str]
    citations: List[Citation]
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
