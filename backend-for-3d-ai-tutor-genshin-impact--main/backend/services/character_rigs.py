"""Ground-truth 3D character rig registry and performance command interpreter.
Maintains exact skeletal, facial, and viseme capabilities discovered from model inspection.
"""
from typing import Dict, List, Optional
from backend.schemas.rig import (
    CharacterRigCapability,
    CharacterPerformanceCommand,
    RigType,
    FacialControlType,
    EyeControlType,
    JawMouthControlType,
    VisemeCue,
)

# Complete 9-character ground-truth rig capabilities
CHARACTER_RIG_REGISTRY: Dict[str, CharacterRigCapability] = {
    "nahida": CharacterRigCapability(
        character_id="nahida",
        display_name="Nahida",
        model_format="FBX 7.3 Binary",
        rig_type=RigType.MORPH_AND_SKELETON,
        has_skeleton=True,
        bone_count=119,
        has_facial_rig=True,
        facial_control_type=FacialControlType.MORPH_TARGETS,
        morph_targets=[
            "Brow_Default", "Brow_Trouble_L", "Brow_Trouble_R", "Brow_Smily_L", "Brow_Smily_R",
            "Brow_Angry_L", "Brow_Angry_R", "Brow_Shy_L", "Brow_Shy_R", "Brow_Up_L", "Brow_Up_R",
            "Brow_Down_L", "Brow_Down_R", "Brow_Squeeze_L", "Brow_Squeeze_R", "Mouth_Default",
            "Mouth_A01", "Mouth_Open01", "Mouth_Smile01", "Mouth_Smile02", "Mouth_Angry01",
            "Mouth_Angry02", "Mouth_Angry03", "Mouth_Fury01", "Mouth_Doya01", "Mouth_Doya02",
            "Mouth_Neko01", "Mouth_Pero01", "Mouth_Pero02", "Mouth_Line01", "Mouth_Line02",
            "Mouth_BigTongue01", "Eye_Default", "Eye_WinkA_L", "Eye_WinkA_R", "Eye_WinkB_L",
            "Eye_WinkB_R", "Eye_WinkC_L", "Eye_WinkC_R", "Eye_Ha", "Eye_Jito", "Eye_Wail",
            "Eye_Hostility", "Eye_Tired", "Eye_WUp", "Eye_WDown", "Eye_Lowereyelid"
        ],
        viseme_mapping={
            "sil": "Mouth_Default",
            "aa": "Mouth_A01",
            "ih": "Mouth_Smile01",
            "ou": "Mouth_Open01",
            "e": "Mouth_Smile02",
            "oh": "Mouth_Open01",
        },
        expression_mapping={
            "neutral_attentive": {"Brow_Default": 1.0, "Eye_Default": 1.0, "Mouth_Default": 1.0},
            "warm_smile": {"Brow_Smily_L": 0.8, "Brow_Smily_R": 0.8, "Mouth_Smile01": 0.75, "Eye_Ha": 0.3},
            "curious": {"Brow_Up_L": 0.85, "Brow_Down_R": 0.4, "Mouth_Open01": 0.3, "Eye_WUp": 0.4},
            "thoughtful": {"Brow_Squeeze_L": 0.7, "Brow_Squeeze_R": 0.7, "Eye_Lowereyelid": 0.4, "Mouth_Line01": 0.6},
            "celebrating": {"Brow_Smily_L": 1.0, "Brow_Smily_R": 1.0, "Mouth_Smile02": 0.9, "Eye_Ha": 0.8},
            "gentle_concern": {"Brow_Trouble_L": 0.7, "Brow_Trouble_R": 0.7, "Mouth_Line02": 0.5},
            "confused_gently": {"Brow_Trouble_L": 0.6, "Brow_Up_R": 0.7, "Eye_Jito": 0.4},
            "explaining": {"Brow_Default": 0.5, "Brow_Smily_L": 0.3, "Brow_Smily_R": 0.3},
        },
        eye_controls=EyeControlType.MORPH_BLINK,
        jaw_mouth_controls=JawMouthControlType.MORPH_VISEMES,
        existing_animation_clips=[],
        asset_file="character_assets/nahida/NPC_Avatar_YoungGirl_Catalyst_Nahida (merge).fbx",
        texture_files=[
            "character_assets/nahida/Avatar_YoungGirl_Catalyst_Nahida_Tex_Hair_.png",
            "character_assets/nahida/Avatar_YoungGirl_Catalyst_Nahida_Tex_Body_.png",
            "character_assets/nahida/Avatar_YoungGirl_Catalyst_Nahida_Tex_Face_.png",
        ],
        missing_capabilities=["prebaked_animation_clips"],
        recommended_animation_strategy="Morph-target facial animation with procedural breathing and head-turn IK",
        estimated_integration_limitations="Requires client-side procedural IK or bone rotations for arm gestures; full facial rig ready."
    ),

    "furina": CharacterRigCapability(
        character_id="furina",
        display_name="Furina",
        model_format="FBX 7.4 Binary",
        rig_type=RigType.MORPH_AND_SKELETON,
        has_skeleton=True,
        bone_count=240,
        has_facial_rig=True,
        facial_control_type=FacialControlType.MORPH_TARGETS,
        morph_targets=[
            "あ", "い", "う", "え", "お", "にやり", "ワ", "ん", "い１", "い２", "あ２", "にやり２",
            "にやり３", "ω", "てへぺろ", "ぺろっ", "口角上げ", "口角下げ", "口横広げ", "口横狭め",
            "舌広げ", "まばたき", "笑い", "ウィンク", "ウィンク右", "ウィンク２", "ウィンク２右",
            "なごみ", "なごみ左", "なごみ右", "びっくり", "じと目", "悲しむ", "怒り目", "ジト目",
            "眼角上", "眼角下", "下眼上", "真面目", "困る", "にこり", "怒り", "恥ずかしい", "上",
            "下", "前", "困る左", "困る右", "にこり左", "にこり右", "怒り左", "怒り右", "恥ずかしい左",
            "恥ずかしい右", "上左", "上右", "下左", "下右", "前左", "前右"
        ],
        viseme_mapping={
            "sil": "ん",
            "aa": "あ",
            "ih": "い",
            "ou": "う",
            "e": "え",
            "oh": "お",
        },
        expression_mapping={
            "neutral_attentive": {"真面目": 0.4},
            "warm_smile": {"笑い": 0.6, "口角上げ": 0.7, "にこり": 0.5},
            "curious": {"びっくり": 0.5, "上": 0.4},
            "thoughtful": {"じと目": 0.4, "困る": 0.4},
            "celebrating": {"にやり２": 0.8, "ワ": 0.5, "笑い": 0.7},
            "gentle_concern": {"困る": 0.6, "口角下げ": 0.4},
            "confused_gently": {"困る左": 0.6, "じと目": 0.3},
            "explaining": {"真面目": 0.5, "口角上げ": 0.3},
        },
        eye_controls=EyeControlType.MORPH_BLINK,
        jaw_mouth_controls=JawMouthControlType.MORPH_VISEMES,
        existing_animation_clips=[],
        asset_file="character_assets/furina/Furina2.fbx",
        texture_files=[
            "character_assets/furina/髮.png",
            "character_assets/furina/颜.png",
            "character_assets/furina/髮2.png",
            "character_assets/furina/髮_1.png",
            "character_assets/furina/体_1.png",
        ],
        missing_capabilities=["prebaked_animation_clips"],
        recommended_animation_strategy="High-expression MMD morph target blending with procedural theatrical gestures",
        estimated_integration_limitations="High bone count (240); ideal for rich upper body and finger poses."
    ),

    "ganyu": CharacterRigCapability(
        character_id="ganyu",
        display_name="Ganyu",
        model_format="FBX 7.4 Binary",
        rig_type=RigType.MORPH_AND_SKELETON,
        has_skeleton=True,
        bone_count=229,
        has_facial_rig=True,
        facial_control_type=FacialControlType.MORPH_TARGETS,
        morph_targets=[
            "まばたき", "笑い", "ウィンク", "ウィンク右", "ウィンク２", "ウィンク２右", "なごみ", "なごみ左",
            "なごみ右", "びっくり", "じと目", "悲しむ", "怒り目", "ジト目", "眼角上", "眼角下", "下眼上",
            "あ", "い", "う", "え", "お", "にやり", "ワ", "ん", "い１", "い２", "あ２", "にやり２",
            "にやり３", "ω", "てへぺろ", "ぺろっ", "口角上げ", "口角下げ", "口横広げ", "口横狭め",
            "舌広げ", "真面目", "困る", "にこり", "怒り", "恥ずかしい", "上", "下", "前", "困る左",
            "困る右", "にこり左", "にこり右", "怒り左", "怒り右", "恥ずかしい左", "恥ずかしい右",
            "上左", "上右", "下左", "下右", "前左", "前右", "星目", "瞳小", "ハイライト消"
        ],
        viseme_mapping={
            "sil": "ん",
            "aa": "あ",
            "ih": "い",
            "ou": "う",
            "e": "え",
            "oh": "お",
        },
        expression_mapping={
            "neutral_attentive": {"なごみ": 0.3},
            "warm_smile": {"なごみ": 0.5, "口角上げ": 0.6, "にこり": 0.4},
            "curious": {"びっくり": 0.3, "上": 0.3},
            "thoughtful": {"じと目": 0.4, "困る": 0.3},
            "celebrating": {"笑い": 0.7, "口角上げ": 0.8},
            "gentle_concern": {"困る": 0.5, "悲しむ": 0.3},
            "confused_gently": {"困る左": 0.5, "なごみ右": 0.3},
            "explaining": {"真面目": 0.4, "口角上げ": 0.3},
        },
        eye_controls=EyeControlType.MORPH_BLINK,
        jaw_mouth_controls=JawMouthControlType.MORPH_VISEMES,
        existing_animation_clips=[],
        asset_file="character_assets/ganyu/SK预览最终.fbx",
        texture_files=[
            "character_assets/ganyu/颜.png",
            "character_assets/ganyu/体.png",
            "character_assets/ganyu/髮.png",
        ],
        missing_capabilities=["prebaked_animation_clips"],
        recommended_animation_strategy="Calm, restrained facial morphs with precise, methodical posture shifts",
        estimated_integration_limitations="Requires procedural arm posing; full 63-shape facial rig ready."
    ),

    "keqing": CharacterRigCapability(
        character_id="keqing",
        display_name="Keqing",
        model_format="FBX 7.4 Binary",
        rig_type=RigType.MORPH_AND_SKELETON,
        has_skeleton=True,
        bone_count=240,
        has_facial_rig=True,
        facial_control_type=FacialControlType.MORPH_TARGETS,
        morph_targets=[
            "あ", "い", "う", "え", "お", "にやり", "ワ", "ん", "い１", "い２", "あ２", "にやり２",
            "にっこり", "ω", "てへぺろ", "ぺろっ", "口角上げ", "口横広げ", "口横狭め", "舌広げ",
            "まばたき", "笑い", "なごみ", "ウィンク", "ウィンク右", "ウィンク２", "ウィンク２右",
            "なごみ左", "なごみ右", "びっくり", "じと目", "喜び", "怒り目", "ジト目", "眼角上",
            "眼角下", "下眼上", "真面目", "困る", "にこり", "怒り", "困る２", "上", "下", "前",
            "困る左", "困る右", "にこり左", "にこり右", "怒り左", "怒り右", "困る２左", "困る２右",
            "上左", "上右", "下左", "下右", "前左", "前右", "星目", "照れ"
        ],
        viseme_mapping={
            "sil": "ん",
            "aa": "あ",
            "ih": "い",
            "ou": "う",
            "e": "え",
            "oh": "お",
        },
        expression_mapping={
            "neutral_attentive": {"真面目": 0.6},
            "warm_smile": {"にっこり": 0.6, "口角上げ": 0.6},
            "curious": {"びっくり": 0.4, "上": 0.3},
            "thoughtful": {"真面目": 0.7, "じと目": 0.4},
            "celebrating": {"喜び": 0.8, "にやり": 0.6},
            "gentle_concern": {"困る": 0.5, "真面目": 0.4},
            "confused_gently": {"困る２左": 0.5},
            "explaining": {"真面目": 0.6, "口角上げ": 0.3},
        },
        eye_controls=EyeControlType.MORPH_BLINK,
        jaw_mouth_controls=JawMouthControlType.MORPH_VISEMES,
        existing_animation_clips=[],
        asset_file="character_assets/keqing/Keqing.fbx",
        texture_files=[
            "character_assets/keqing/面.png",
            "character_assets/keqing/表情.png",
            "character_assets/keqing/服.png",
            "character_assets/keqing/发.png",
            "character_assets/keqing/肌.png",
        ],
        missing_capabilities=["prebaked_animation_clips"],
        recommended_animation_strategy="Focused, efficient facial blending with decisive head gestures",
        estimated_integration_limitations="Contains tongue bones in addition to morph targets."
    ),

    "sucrose": CharacterRigCapability(
        character_id="sucrose",
        display_name="Sucrose",
        model_format="FBX 7.4 Binary",
        rig_type=RigType.MORPH_AND_SKELETON,
        has_skeleton=True,
        bone_count=220,
        has_facial_rig=True,
        facial_control_type=FacialControlType.MORPH_TARGETS,
        morph_targets=[
            "まばたき", "笑い", "なごみ", "ウィンク", "ウィンク右", "ウィンク２", "ウィンク２右",
            "なごみ左", "なごみ右", "びっくり", "じと目", "喜び", "怒り目", "ジト目", "眼角上",
            "眼角下", "下眼上", "あ", "い", "う", "え", "お", "にやり", "ワ", "ん", "い１",
            "い２", "あ２", "にやり２", "にやり３", "ω", "てへぺろ", "ぺろっ", "口角上げ",
            "口横広げ", "口横狭め", "舌広げ", "真面目", "困る", "にこり", "怒り", "上", "下",
            "前", "困る左", "困る右", "にこり左", "にこり右", "怒り左", "怒り右", "真面目左",
            "真面目右", "上左", "上右", "下左", "下右", "前左", "前右", "星目", "瞳小"
        ],
        viseme_mapping={
            "sil": "ん",
            "aa": "あ",
            "ih": "い",
            "ou": "う",
            "e": "え",
            "oh": "お",
        },
        expression_mapping={
            "neutral_attentive": {"なごみ": 0.4},
            "warm_smile": {"にこり": 0.6, "口角上げ": 0.5},
            "curious": {"びっくり": 0.5, "星目": 0.4, "上": 0.3},
            "thoughtful": {"困る": 0.4, "じと目": 0.4},
            "celebrating": {"喜び": 0.8, "星目": 0.7, "口角上げ": 0.7},
            "gentle_concern": {"困る": 0.6, "なごみ": 0.2},
            "confused_gently": {"困る左": 0.5, "びっくり": 0.3},
            "explaining": {"真面目": 0.4, "にこり": 0.3},
        },
        eye_controls=EyeControlType.MORPH_BLINK,
        jaw_mouth_controls=JawMouthControlType.MORPH_VISEMES,
        existing_animation_clips=[],
        asset_file="character_assets/sucrose/Sucrose.fbx",
        texture_files=[
            "character_assets/sucrose/肌.png",
            "character_assets/sucrose/面.png",
            "character_assets/sucrose/发.png",
            "character_assets/sucrose/服.png",
        ],
        missing_capabilities=["prebaked_animation_clips"],
        recommended_animation_strategy="Enthusiastic curious head tilts, secondary ear-bone physics, and morph-based mouth shapes",
        estimated_integration_limitations="Has secondary ear bones ('Ears_0_1_R/L') that can procedurally wiggle on discovery."
    ),

    "zhongli": CharacterRigCapability(
        character_id="zhongli",
        display_name="Zhongli",
        model_format="glTF 2.0",
        rig_type=RigType.SKELETON_ONLY,
        has_skeleton=True,
        bone_count=185,
        has_facial_rig=True,
        facial_control_type=FacialControlType.SKELETAL_JOINTS,
        morph_targets=[],
        viseme_mapping={},
        expression_mapping={
            "neutral_attentive": {},
            "warm_smile": {},
            "curious": {},
            "thoughtful": {},
            "celebrating": {},
            "gentle_concern": {},
            "confused_gently": {},
            "explaining": {},
        },
        eye_controls=EyeControlType.SKELETAL_EYES,
        jaw_mouth_controls=JawMouthControlType.SKELETAL_TONGUE,
        existing_animation_clips=[],
        asset_file="character_assets/zhongli/scene.gltf",
        texture_files=[
            "character_assets/zhongli/material_baseColor.png",
            "character_assets/zhongli/material_1_baseColor.png",
            "character_assets/zhongli/material_2_baseColor.png",
            "character_assets/zhongli/material_3_baseColor.png",
        ],
        missing_capabilities=["facial_blendshapes", "prebaked_animation_clips"],
        recommended_animation_strategy="Skeletal gaze tracking ('Eye_L_07', 'Eye_R_08'), neck/head composure tilts, and procedural breathing",
        estimated_integration_limitations="No facial morph targets. Mouth sync uses skeletal tongue bone micro-rotation and subtle jaw-pitch articulation."
    ),

    "barbara": CharacterRigCapability(
        character_id="barbara",
        display_name="Barbara",
        model_format="FBX 7.7 ASCII",
        rig_type=RigType.SEGMENTED_MESH,
        has_skeleton=False,
        bone_count=0,
        has_facial_rig=True,
        facial_control_type=FacialControlType.SEGMENTED_MESH_TRANSFORMS,
        morph_targets=[],
        viseme_mapping={},
        expression_mapping={},
        eye_controls=EyeControlType.MESH_BLINK,
        jaw_mouth_controls=JawMouthControlType.MESH_SCALE,
        existing_animation_clips=[],
        asset_file="character_assets/barbara/_バーバラ.fbx",
        texture_files=[
            "character_assets/barbara/顔.png",
            "character_assets/barbara/服.png",
            "character_assets/barbara/髪.png",
            "character_assets/barbara/肌.png",
            "character_assets/barbara/表情.png",
        ],
        missing_capabilities=["skeletal_rig", "facial_blendshapes", "prebaked_animation_clips"],
        recommended_animation_strategy="Submesh transform modulation: eye mesh ('目') Y-scale for blinks, mouth mesh ('口舌') Y-scale for visemes, blush mesh ('脸红') material opacity",
        estimated_integration_limitations="Model was converted without skeleton; segmented facial submeshes allow procedural feature scaling."
    ),

    "raiden_shogun": CharacterRigCapability(
        character_id="raiden_shogun",
        display_name="Raiden Ei / Shogun",
        model_format="GLB (glTF 2.0 Binary)",
        rig_type=RigType.STATIC_MESH,
        has_skeleton=False,
        bone_count=0,
        has_facial_rig=False,
        facial_control_type=FacialControlType.NONE,
        morph_targets=[],
        viseme_mapping={},
        expression_mapping={},
        eye_controls=EyeControlType.NONE,
        jaw_mouth_controls=JawMouthControlType.AUDIO_AMPLITUDE_PULSE,
        existing_animation_clips=[],
        asset_file="character_assets/raiden_shogun/raiden_shogun 2.glb",
        texture_files=[
            "character_assets/raiden_shogun/gltf_embedded_0.png",
            "character_assets/raiden_shogun/gltf_embedded_1.png",
            "character_assets/raiden_shogun/gltf_embedded_2.png",
            "character_assets/raiden_shogun/gltf_embedded_3.png",
            "character_assets/raiden_shogun/gltf_embedded_4.png",
            "character_assets/raiden_shogun/gltf_embedded_5.png",
        ],
        missing_capabilities=["skeletal_rig", "facial_blendshapes", "prebaked_animation_clips"],
        recommended_animation_strategy="Cinematic camera framing, breathing scale/bobbing transform, dynamic rim lighting, and speech pulse effect",
        estimated_integration_limitations="Unskinned static GLB. Cannot deform bones or face; graceful degradation keeps character dignified without glitches."
    ),

    "tsaritsa": CharacterRigCapability(
        character_id="tsaritsa",
        display_name="Tsaritsa",
        model_format="FBX 7.5 Binary",
        rig_type=RigType.STATIC_MESH,
        has_skeleton=False,
        bone_count=0,
        has_facial_rig=False,
        facial_control_type=FacialControlType.NONE,
        morph_targets=[],
        viseme_mapping={},
        expression_mapping={},
        eye_controls=EyeControlType.NONE,
        jaw_mouth_controls=JawMouthControlType.AUDIO_AMPLITUDE_PULSE,
        existing_animation_clips=[],
        asset_file="character_assets/tsaritsa/RH9IC74KOYH64ZMLDFBR9M9J6.fbx",
        texture_files=[
            "character_assets/tsaritsa/Avatar_Lady_Bow_Anastasya_Tex_Face_Diffuse.png",
            "character_assets/tsaritsa/Avatar_Lady_Bow_Anastasya_Tex_Hair_Diffuse.png",
            "character_assets/tsaritsa/Avatar_Lady_Bow_Anastasya_Tex_Body_Diffuse.png",
            "character_assets/tsaritsa/Avatar_Lady_Bow_Anastasya_Tex_Dress_Diffuse.png",
            "character_assets/tsaritsa/Avatar_Lady_Bow_Anastasya_Tex_Body01_Diffuse.png",
            "character_assets/tsaritsa/Avatar_Lady_Bow_Anastasya_Tex_Pupil01_Diffuse.png",
            "character_assets/tsaritsa/Avatar_Lady_Bow_Anastasya_Tex_Shell_Diffuse.png",
        ],
        missing_capabilities=["skeletal_rig", "facial_blendshapes", "prebaked_animation_clips"],
        recommended_animation_strategy="Composed pedestal presentation, subtle ice-crystal aura pulses, and camera elevation",
        estimated_integration_limitations="Unskinned multi-group FBX. Uses non-intrusive presentation fallbacks."
    ),
}


class CharacterPerformanceInterpreter:
    """Interprets high-level conversational events into precise 3D performance commands."""

    @classmethod
    def get_rig_capability(cls, character_id: str) -> Optional[CharacterRigCapability]:
        return CHARACTER_RIG_REGISTRY.get(character_id)

    @classmethod
    def list_all_capabilities(cls) -> List[CharacterRigCapability]:
        return list(CHARACTER_RIG_REGISTRY.values())

    @classmethod
    def generate_viseme_cues(
        cls,
        character_id: str,
        text: str,
        duration_ms: int = 2500,
        words_per_minute: int = 150
    ) -> List[VisemeCue]:
        """Generates realistic viseme cues for lip synchronization mapped to the character's rig."""
        cap = cls.get_rig_capability(character_id)
        if not cap or cap.jaw_mouth_controls != JawMouthControlType.MORPH_VISEMES:
            return []

        vmap = cap.viseme_mapping
        cues: List[VisemeCue] = []
        words = text.split()
        if not words:
            return cues

        ms_per_word = max(180, int((60000 / words_per_minute)))
        total_time = min(duration_ms, len(words) * ms_per_word)
        step_ms = 120

        # Pattern of natural speech visemes: aa -> e -> ou -> ih -> oh -> sil
        v_cycle = ["aa", "ih", "ou", "e", "oh", "sil"]
        current_ms = 0
        cycle_idx = 0

        while current_ms < total_time:
            vis = v_cycle[cycle_idx % len(v_cycle)]
            target_morph = vmap.get(vis, vmap.get("sil"))
            intensity = 0.85 if vis != "sil" else 0.0
            cues.append(
                VisemeCue(
                    time_offset_ms=current_ms,
                    viseme=vis,
                    intensity=intensity,
                    character_morph_target=target_morph,
                )
            )
            current_ms += step_ms
            cycle_idx += 1

        # End with silence / relaxed mouth
        cues.append(
            VisemeCue(
                time_offset_ms=current_ms,
                viseme="sil",
                intensity=0.0,
                character_morph_target=vmap.get("sil"),
            )
        )
        return cues

    @classmethod
    def build_performance_command(
        cls,
        character_id: str,
        session_id: str,
        conversation_state: str,
        semantic_expression: str,
        text: Optional[str] = None,
        duration_ms: int = 2000,
        priority: int = 2,
    ) -> CharacterPerformanceCommand:
        """Constructs an executable 3D character performance command."""
        cap = cls.get_rig_capability(character_id) or CHARACTER_RIG_REGISTRY["nahida"]

        # 1. Target morphs
        target_morphs: Dict[str, float] = {}
        if cap.has_facial_rig and cap.facial_control_type == FacialControlType.MORPH_TARGETS:
            expr_map = cap.expression_mapping.get(
                semantic_expression,
                cap.expression_mapping.get("neutral_attentive", {})
            )
            target_morphs = dict(expr_map)

        # 2. Skeletal adjustments (head tilt, neck nod, gaze)
        skeletal_adjustments: Dict[str, Dict[str, float]] = {}
        if cap.has_skeleton:
            if conversation_state == "listening":
                skeletal_adjustments["head"] = {"pitch": 0.05, "yaw": 0.0, "roll": 0.03}
                skeletal_adjustments["neck"] = {"pitch": 0.02, "yaw": 0.0, "roll": 0.0}
            elif conversation_state == "processing":
                skeletal_adjustments["head"] = {"pitch": -0.06, "yaw": 0.08, "roll": -0.04}
            elif conversation_state == "speaking":
                skeletal_adjustments["head"] = {"pitch": 0.02, "yaw": -0.02, "roll": 0.0}
            elif conversation_state == "interrupted":
                skeletal_adjustments["head"] = {"pitch": 0.0, "yaw": 0.0, "roll": 0.0}
            else:
                skeletal_adjustments["head"] = {"pitch": 0.0, "yaw": 0.0, "roll": 0.0}

        # 3. Visemes
        visemes = []
        if text and conversation_state == "speaking":
            visemes = cls.generate_viseme_cues(character_id, text, duration_ms)

        # 4. Gesture
        gesture = "gentle_nod" if conversation_state == "listening" else (
            "thinking_pose" if conversation_state == "processing" else "point_explanation"
        )

        return CharacterPerformanceCommand(
            character_id=character_id,
            session_id=session_id,
            conversation_state=conversation_state,
            semantic_expression=semantic_expression,
            target_morphs=target_morphs,
            skeletal_adjustments=skeletal_adjustments,
            viseme_timeline=visemes,
            gesture_instruction=gesture,
            priority=priority,
            transition_duration_ms=350,
        )
