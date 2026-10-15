"""Schemas for 3D character rigs, capabilities, expressions, and performance contracts."""
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class RigType(str, Enum):
    MORPH_AND_SKELETON = "morph_and_skeleton"
    SKELETON_ONLY = "skeleton_only"
    SEGMENTED_MESH = "segmented_mesh"
    STATIC_MESH = "static_mesh"


class FacialControlType(str, Enum):
    MORPH_TARGETS = "morph_targets"
    SKELETAL_JOINTS = "skeletal_joints"
    SEGMENTED_MESH_TRANSFORMS = "segmented_mesh_transforms"
    NONE = "none"


class EyeControlType(str, Enum):
    MORPH_BLINK = "morph_blink"
    SKELETAL_EYES = "skeletal_eyes"
    MESH_BLINK = "mesh_blink"
    NONE = "none"


class JawMouthControlType(str, Enum):
    MORPH_VISEMES = "morph_visemes"
    SKELETAL_TONGUE = "skeletal_tongue"
    MESH_SCALE = "mesh_scale"
    AUDIO_AMPLITUDE_PULSE = "audio_amplitude_pulse"
    NONE = "none"


class VisemeCue(BaseModel):
    time_offset_ms: int = Field(..., ge=0, description="Millisecond offset from audio start")
    viseme: str = Field(..., description="Standard viseme code: sil, aa, ih, ou, e, oh")
    intensity: float = Field(1.0, ge=0.0, le=1.0, description="Viseme blend weight")
    character_morph_target: Optional[str] = Field(None, description="Model-specific morph target or bone")


class CharacterRigCapability(BaseModel):
    character_id: str
    display_name: str
    model_format: str
    rig_type: RigType
    has_skeleton: bool
    bone_count: int
    has_facial_rig: bool
    facial_control_type: FacialControlType
    morph_targets: List[str] = Field(default_factory=list)
    viseme_mapping: Dict[str, str] = Field(default_factory=dict)
    expression_mapping: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    eye_controls: EyeControlType
    jaw_mouth_controls: JawMouthControlType
    existing_animation_clips: List[str] = Field(default_factory=list)
    asset_file: str
    texture_files: List[str] = Field(default_factory=list)
    missing_capabilities: List[str] = Field(default_factory=list)
    recommended_animation_strategy: str
    estimated_integration_limitations: str


class CharacterPerformanceCommand(BaseModel):
    character_id: str
    session_id: str
    conversation_state: str = Field(..., description="idle, listening, processing, speaking, interrupted, etc.")
    semantic_expression: str = Field(..., description="warm_smile, thoughtful, curious, celebrating, etc.")
    target_morphs: Dict[str, float] = Field(default_factory=dict, description="Active morph target weights")
    skeletal_adjustments: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Head, neck, or spine rotation offsets in radians"
    )
    viseme_timeline: List[VisemeCue] = Field(default_factory=list)
    gesture_instruction: str = Field(..., description="Procedural or clip gesture name")
    priority: int = Field(2, ge=1, le=5)
    transition_duration_ms: int = Field(350, ge=50, le=2000)
