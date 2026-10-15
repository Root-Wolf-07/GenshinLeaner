"""Character Tutor catalog and profile API endpoints.
Provides discovery for all 9 character tutors, subjects, personality, animations, and voice profiles.
"""

from typing import List
from fastapi import APIRouter, HTTPException, status
from backend.schemas.tutor import TutorProfile, TutorSummary
from backend.schemas.rig import CharacterRigCapability, CharacterPerformanceCommand
from backend.services.tutor_profiles import tutor_registry
from backend.services.character_rigs import CharacterPerformanceInterpreter

router = APIRouter(tags=["Character Tutors"])


@router.get("/tutors", response_model=List[TutorSummary])
def list_tutors() -> List[TutorSummary]:
    """List all available character tutors and their primary specialized subjects."""
    profiles = tutor_registry.get_all_tutors(enabled_only=True)
    return [
        TutorSummary(
            id=p.id,
            display_name=p.display_name,
            description=p.description,
            supported_subjects=p.supported_subjects,
            teaching_personality=p.teaching_personality,
            avatar_asset_ref=p.avatar_asset_ref,
            is_enabled=p.is_enabled,
            voice_provider=p.voice_provider,
        )
        for p in profiles
    ]


@router.get("/tutors/{tutor_id}", response_model=TutorProfile)
def get_tutor(tutor_id: str) -> TutorProfile:
    """Retrieve full pedagogical profile, animation states, and voice settings for a specific tutor."""
    profile = tutor_registry.get_tutor_by_id(tutor_id)
    if not profile or not profile.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character tutor '{tutor_id}' not found.",
        )
    return profile


@router.get("/tutors/{tutor_id}/capabilities", response_model=CharacterRigCapability)
def get_tutor_capabilities(tutor_id: str) -> CharacterRigCapability:
    """Retrieve 3D rig capabilities, morph targets, viseme mapping, and integration limitations."""
    cap = CharacterPerformanceInterpreter.get_rig_capability(tutor_id)
    if not cap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"3D character rig capability for '{tutor_id}' not found.",
        )
    return cap


@router.get("/tutors-capabilities", response_model=List[CharacterRigCapability])
def list_all_tutor_capabilities() -> List[CharacterRigCapability]:
    """Retrieve 3D rig capabilities for all 9 characters."""
    return CharacterPerformanceInterpreter.list_all_capabilities()


@router.post("/tutors/{tutor_id}/performance", response_model=CharacterPerformanceCommand)
def generate_tutor_performance(
    tutor_id: str,
    session_id: str = "demo-session",
    conversation_state: str = "speaking",
    semantic_expression: str = "warm_smile",
    text: str = "Welcome! Let us begin our lesson.",
    duration_ms: int = 2500,
) -> CharacterPerformanceCommand:
    """Generates an executable 3D character performance command with model-accurate morph weights and visemes."""
    cap = CharacterPerformanceInterpreter.get_rig_capability(tutor_id)
    if not cap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character tutor '{tutor_id}' not found.",
        )
    return CharacterPerformanceInterpreter.build_performance_command(
        character_id=tutor_id,
        session_id=session_id,
        conversation_state=conversation_state,
        semantic_expression=semantic_expression,
        text=text,
        duration_ms=duration_ms,
    )


@router.get("/tutors/{tutor_id}/assets/{asset_name}")
def get_tutor_asset(tutor_id: str, asset_name: str):
    """Securely stream 3D models and textures for a character."""
    import os
    from fastapi.responses import FileResponse

    base_dir = os.path.abspath(
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "character_assets", tutor_id)
    )
    file_path = os.path.abspath(os.path.join(base_dir, asset_name))

    # Reject path traversal
    if not file_path.startswith(base_dir) or not os.path.isfile(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset '{asset_name}' not found for character '{tutor_id}'.",
        )

    # Detect MIME type
    ext = os.path.splitext(asset_name)[1].lower()
    media_types = {
        ".glb": "model/gltf-binary",
        ".gltf": "model/gltf+json",
        ".bin": "application/octet-stream",
        ".fbx": "application/octet-stream",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }
    media_type = media_types.get(ext, "application/octet-stream")
    return FileResponse(file_path, media_type=media_type, filename=asset_name)
