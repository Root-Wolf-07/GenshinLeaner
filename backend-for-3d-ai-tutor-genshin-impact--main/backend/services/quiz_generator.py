"""Adaptive Quiz Generator Service.
Generates Multiple Choice, True/False, Short Answer, and Fill-in-the-blank questions
while securely hiding answer keys on the backend.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional
from backend.db.session import Session

from backend.models.document import Document
from backend.models.quiz import Quiz
from backend.schemas.chat import Citation
from backend.schemas.quizzes import QuizGenerateRequest, QuestionPublic
from backend.services.citation_validator import citation_validator
from backend.services.llm_provider import get_llm_provider
from backend.services.retriever import retriever_service, RetrievedPassage
from backend.services.tutor_profiles import tutor_registry

logger = logging.getLogger(__name__)


class QuizGeneratorService:
    """Generates structured quizzes with answer keys held privately on backend."""

    @classmethod
    def generate_quiz(
        cls,
        request: QuizGenerateRequest,
        user_id: str,
        db: Session,
    ) -> Quiz:
        """Create and persist an adaptive educational quiz."""
        # 1. Retrieve evidence if document IDs provided
        passages: List[RetrievedPassage] = []
        if request.source_mode in ("uploaded", "both") and request.document_ids:
            valid_docs = db.query(Document.id).filter(
                Document.id.in_(request.document_ids),
                Document.owner_id == user_id,
            ).all()
            doc_ids = [d[0] for d in valid_docs]
            if doc_ids:
                passages = retriever_service.retrieve(
                    user_id=user_id,
                    query=request.topic,
                    db=db,
                    allowed_document_ids=doc_ids,
                    top_k=6,
                )

        # 2. Build Prompt
        evidence_str = ""
        if passages:
            evidence_str = "\nCourse Evidence for Questions:\n" + "\n".join(
                [f"[{p.document_title} - P.{p.page_number or 1}]: {p.content}" for p in passages]
            )

        q_types = request.question_types or ["multiple_choice", "true_false", "short_answer"]
        type_str = ", ".join(q_types)

        prompt = (
            f"Generate a rigorous educational quiz on the topic: '{request.topic}'.\n"
            f"Question Count: {request.question_count}\n"
            f"Difficulty: {request.difficulty}\n"
            f"Target Student Level: {request.student_level}\n"
            f"Allowed Question Types: {type_str}\n"
            f"{evidence_str}\n\n"
            "Return valid JSON object with:\n"
            "- 'title': String,\n"
            "- 'questions': Array of objects with:\n"
            "   - 'id': String (e.g. 'q1', 'q2'),\n"
            "   - 'prompt': Clear question text (use KaTeX $...$ for formulas),\n"
            "   - 'question_type': One of ['multiple_choice', 'true_false', 'short_answer', 'fill_in_the_blank'],\n"
            "   - 'options': Array of 4 strings for multiple_choice, ['True', 'False'] for true_false, null for short_answer,\n"
            "   - 'correct_answer': The exact correct answer string or boolean,\n"
            "   - 'explanation': Clear explanation of why this answer is correct,\n"
            "   - 'topic_tag': Subtopic name,\n"
            "   - 'difficulty': 'beginner'|'intermediate'|'advanced',\n"
            "   - 'points': 1.0\n"
        )

        system_prompt = (
            "You are a psychometrician and university professor designing fair, rigorous assessments. "
            "Ensure questions test conceptual understanding rather than mere recall. "
            "Never leak answer hints inside the question prompt."
        )

        if request.character_id:
            tutor = tutor_registry.get_tutor_by_id(request.character_id)
            if tutor:
                system_prompt += (
                    f"\nTUTOR PEDAGOGY GUIDANCE ({tutor.display_name}):\n"
                    f"- Character specialty: {', '.join(tutor.supported_subjects)}.\n"
                    f"- Quiz assessment focus: {tutor.quiz_behavior}.\n"
                    "- Note: Personality may frame questions, but answer keys and grading remain purely objective."
                )

        provider = get_llm_provider()
        questions_list: List[Dict[str, Any]] = []
        quiz_title = f"Quiz: {request.topic}"

        try:
            res = provider.generate(prompt=prompt, system_prompt=system_prompt, json_mode=True, temperature=0.3)
            clean_res = re.sub(r"^```(?:json)?\s*|\s*```$", "", res.strip())
            data = json.loads(clean_res)
            quiz_title = data.get("title", quiz_title)
            questions_list = data.get("questions", [])
        except Exception as e:
            logger.warning(f"Error generating quiz via LLM: {e}. Using deterministic fallback.")
            questions_list = cls._fallback_questions(request)

        # 3. Attach citations to questions if evidence was retrieved
        if passages:
            primary_cit = Citation(
                citation_id=passages[0].chunk_id,
                document_id=passages[0].document_id,
                document_title=passages[0].document_title,
                source_type=passages[0].source_type,
                page_number=passages[0].page_number,
                slide_number=passages[0].slide_number,
                excerpt=passages[0].content[:160],
            )
            for q in questions_list:
                q["citations"] = [primary_cit.model_dump()]
        else:
            for q in questions_list:
                q["citations"] = []

        # 4. Persist Quiz in DB
        quiz = Quiz(
            id=str(uuid.uuid4()),
            owner_id=user_id,
            title=quiz_title,
            topic=request.topic,
            difficulty=request.difficulty,
            student_level=request.student_level or "undergraduate",
            source_mode=request.source_mode,
            document_ids=request.document_ids or [],
            total_questions=len(questions_list),
            questions=questions_list,
        )
        db.add(quiz)
        db.commit()
        db.refresh(quiz)

        return quiz

    @classmethod
    def get_public_questions(cls, quiz: Quiz) -> List[QuestionPublic]:
        """Strip correct_answer, explanation, and citations for safe student viewing."""
        public_qs: List[QuestionPublic] = []
        for q in quiz.questions:
            public_qs.append(
                QuestionPublic(
                    id=str(q.get("id")),
                    prompt=q.get("prompt", ""),
                    question_type=q.get("question_type", "multiple_choice"),
                    options=q.get("options"),
                    topic_tag=q.get("topic_tag", quiz.topic),
                    difficulty=q.get("difficulty", quiz.difficulty),
                    points=float(q.get("points", 1.0)),
                )
            )
        return public_qs

    @staticmethod
    def _fallback_questions(request: QuizGenerateRequest) -> List[Dict[str, Any]]:
        """Fallback questions for test predictability."""
        return [
            {
                "id": "q1",
                "prompt": f"Which principle is central to understanding {request.topic}?",
                "question_type": "multiple_choice",
                "options": [
                    "Empirical verification and invariant checking",
                    "Random guess selection without validation",
                    "Ignoring edge cases and boundary conditions",
                    "Exponential time without caching",
                ],
                "correct_answer": "Empirical verification and invariant checking",
                "explanation": "Invariant verification guarantees safety and algorithmic correctness.",
                "topic_tag": request.topic,
                "difficulty": request.difficulty,
                "points": 1.0,
            },
            {
                "id": "q2",
                "prompt": f"In {request.topic}, edge cases should be evaluated before production deployment.",
                "question_type": "true_false",
                "options": ["True", "False"],
                "correct_answer": "True",
                "explanation": "Edge cases often reveal non-obvious flaws or boundary failures.",
                "topic_tag": request.topic,
                "difficulty": request.difficulty,
                "points": 1.0,
            },
            {
                "id": "q3",
                "prompt": f"Explain briefly why optimal solutions in {request.topic} avoid quadratic growth.",
                "question_type": "short_answer",
                "options": None,
                "correct_answer": "Scalability and efficiency require linear or logarithmic bounds.",
                "explanation": "Quadratic growth becomes prohibitive as input size n grows.",
                "topic_tag": request.topic,
                "difficulty": request.difficulty,
                "points": 1.0,
            },
        ]


# Global instance
quiz_generator = QuizGeneratorService()
