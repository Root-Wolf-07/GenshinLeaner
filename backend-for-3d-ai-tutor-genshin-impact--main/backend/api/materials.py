"""Study Material Studio API endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.dependencies import get_current_user
from backend.models.material import StudyMaterial
from backend.models.user import User
from backend.schemas.materials import (
    StudyMaterialGenerateRequest,
    StudyMaterialResponse,
    StudyMaterialUpdateRequest,
    SectionRegenerateRequest,
    MaterialExportRequest,
    MaterialExportResponse,
)
from backend.services.export_service import export_service
from backend.services.material_generator import material_generator

router = APIRouter(tags=["Study Material Studio"])


@router.post("/materials/generate", response_model=StudyMaterialResponse, status_code=status.HTTP_201_CREATED)
def generate_study_material(
    request: StudyMaterialGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate structured study notes, flashcards, summaries, mock exams, or tutorials."""
    return material_generator.generate_material(request=request, user_id=current_user.id, db=db)


@router.get("/materials", response_model=List[StudyMaterialResponse])
def list_materials(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all study materials created by the student."""
    return (
        db.query(StudyMaterial)
        .filter(StudyMaterial.owner_id == current_user.id)
        .order_by(StudyMaterial.created_at.desc())
        .all()
    )


@router.get("/materials/{material_id}", response_model=StudyMaterialResponse)
def get_material(
    material_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get single study material with structured content and Markdown view."""
    material = (
        db.query(StudyMaterial)
        .filter(
            StudyMaterial.id == material_id,
            StudyMaterial.owner_id == current_user.id,
        )
        .first()
    )
    if not material:
        raise HTTPException(status_code=404, detail="Study material not found.")
    return material


@router.patch("/materials/{material_id}", response_model=StudyMaterialResponse)
def update_material(
    material_id: str,
    update_in: StudyMaterialUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save student edits to study material title, JSON content, or Markdown."""
    material = (
        db.query(StudyMaterial)
        .filter(
            StudyMaterial.id == material_id,
            StudyMaterial.owner_id == current_user.id,
        )
        .first()
    )
    if not material:
        raise HTTPException(status_code=404, detail="Study material not found.")

    if update_in.title is not None:
        material.title = update_in.title
    if update_in.content is not None:
        material.content = update_in.content
    if update_in.raw_markdown is not None:
        material.raw_markdown = update_in.raw_markdown

    db.commit()
    db.refresh(material)
    return material


@router.post("/materials/{material_id}/regenerate-section", response_model=StudyMaterialResponse)
def regenerate_material_section(
    material_id: str,
    section_in: SectionRegenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Regenerate a specific section within study notes using targeted instructions."""
    material = (
        db.query(StudyMaterial)
        .filter(
            StudyMaterial.id == material_id,
            StudyMaterial.owner_id == current_user.id,
        )
        .first()
    )
    if not material:
        raise HTTPException(status_code=404, detail="Study material not found.")

    return material_generator.regenerate_section(
        material=material,
        section_index=section_in.section_index,
        section_title=section_in.section_title,
        additional_instructions=section_in.additional_instructions,
        user_id=current_user.id,
        db=db,
    )


@router.post("/materials/{material_id}/export", response_model=MaterialExportResponse)
def export_material(
    material_id: str,
    export_in: MaterialExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export study material into Markdown, Plain Text, or HTML format."""
    material = (
        db.query(StudyMaterial)
        .filter(
            StudyMaterial.id == material_id,
            StudyMaterial.owner_id == current_user.id,
        )
        .first()
    )
    if not material:
        raise HTTPException(status_code=404, detail="Study material not found.")

    res = export_service.export(material=material, export_format=export_in.format)
    return MaterialExportResponse(**res)


@router.delete("/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(
    material_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a study material."""
    material = (
        db.query(StudyMaterial)
        .filter(
            StudyMaterial.id == material_id,
            StudyMaterial.owner_id == current_user.id,
        )
        .first()
    )
    if not material:
        raise HTTPException(status_code=404, detail="Study material not found.")

    db.delete(material)
    db.commit()
    return None
