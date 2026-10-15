"""Services package root.
Exports all business logic and orchestration services.
"""

from backend.services.document_parser import DocumentParser, ExtractedSection, ParseResult
from backend.services.chunking import TextChunker, ProcessedChunk
from backend.services.embeddings import EmbeddingService, embedding_service
from backend.services.vector_store import VectorStoreService, vector_store
from backend.services.retriever import RetrieverService, retriever_service, RetrievedPassage
from backend.services.gemini_service import GeminiService, gemini_service
from backend.services.llm_provider import LLMProvider, get_llm_provider
from backend.services.citation_validator import CitationValidator, citation_validator
from backend.services.tutor import TutorService, tutor_service
from backend.services.agentic_tutor import AgenticTutorService, agentic_tutor
from backend.services.material_generator import MaterialGeneratorService, material_generator
from backend.services.quiz_generator import QuizGeneratorService, quiz_generator
from backend.services.quiz_grader import QuizGraderService, quiz_grader
from backend.services.adaptive_learning import AdaptiveLearningService, adaptive_learning
from backend.services.recommendations import RecommendationsService, recommendations_service
from backend.services.export_service import ExportService, export_service
from backend.services.document_processor import DocumentProcessor, document_processor
from backend.services.job_queue import JobQueueService, job_queue
from backend.services.tutor_profiles import TutorProfileRegistry, tutor_registry
from backend.services.animation_events import AnimationEventService, animation_service
from backend.services.text_to_speech import TextToSpeechService, tts_service
from backend.services.speech_to_text import SpeechToTextService, stt_service
from backend.services.voice_service import VoiceService, voice_service
from backend.services.character_behavior import CharacterBehaviorService, character_behavior
from backend.services.interactive_sessions import InteractiveSessionService, interactive_sessions
from backend.services.learning_rewards import LearningRewardsService, learning_rewards
from backend.services.character_rigs import CharacterPerformanceInterpreter, CHARACTER_RIG_REGISTRY

__all__ = [
    "AgenticTutorService",
    "agentic_tutor",
    "DocumentParser",
    "ExtractedSection",
    "ParseResult",
    "TextChunker",
    "ProcessedChunk",
    "EmbeddingService",
    "embedding_service",
    "VectorStoreService",
    "vector_store",
    "RetrieverService",
    "retriever_service",
    "RetrievedPassage",
    "GeminiService",
    "gemini_service",
    "LLMProvider",
    "get_llm_provider",
    "CitationValidator",
    "citation_validator",
    "TutorService",
    "tutor_service",
    "MaterialGeneratorService",
    "material_generator",
    "QuizGeneratorService",
    "quiz_generator",
    "QuizGraderService",
    "quiz_grader",
    "AdaptiveLearningService",
    "adaptive_learning",
    "RecommendationsService",
    "recommendations_service",
    "ExportService",
    "export_service",
    "DocumentProcessor",
    "document_processor",
    "JobQueueService",
    "job_queue",
    "TutorProfileRegistry",
    "tutor_registry",
    "AnimationEventService",
    "animation_service",
    "TextToSpeechService",
    "tts_service",
    "SpeechToTextService",
    "stt_service",
    "VoiceService",
    "voice_service",
    "CharacterBehaviorService",
    "character_behavior",
    "InteractiveSessionService",
    "interactive_sessions",
    "LearningRewardsService",
    "learning_rewards",
]
