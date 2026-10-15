"""Provider-independent LLM service interface and implementations.
Supports Google Gemini, OpenAI-compatible APIs, Ollama, and an offline test Mock.
"""

from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import urllib.request
import urllib.error

from backend.config import settings
from backend.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.4,
    ) -> str:
        """Generate text or JSON response."""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Check provider configuration and readiness without raising exceptions."""
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini language model provider."""

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.4,
    ) -> str:
        schema = {"type": "OBJECT"} if json_mode else None
        return gemini_service.generate_content(
            prompt=prompt,
            system_instruction=system_prompt,
            temperature=temperature,
            response_schema=schema,
        )

    def health_check(self) -> Dict[str, Any]:
        configured = gemini_service.is_configured()
        return {
            "provider": "gemini",
            "model": settings.GEMINI_MODEL,
            "configured": configured,
            "status": "ready" if configured else "missing_api_key",
        }


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible language model provider with resilient fallback."""

    def __init__(self):
        self.mock_fallback = MockProvider()

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.4,
    ) -> str:
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("your-"):
            logger.warning("OPENAI_API_KEY is not configured. Serving pedagogical fallback.")
            return self.mock_fallback.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                json_mode=json_mode,
                temperature=temperature,
            )

        url = f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            logger.error(f"OpenAI API HTTP error {e.code}: {err_body}")
            # If quota exceeded, invalid auth, or rate limit, serve structured fallback to keep system alive
            if e.code in (401, 429, 500, 502, 503):
                logger.warning("OpenAI error caught, serving fallback to prevent application interruption.")
                return self.mock_fallback.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    json_mode=json_mode,
                    temperature=temperature,
                )
            raise RuntimeError(f"OpenAI API error ({e.code}): {err_body}")
        except Exception as e:
            logger.warning(f"OpenAI connection error: {e}. Serving pedagogical fallback.")
            return self.mock_fallback.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                json_mode=json_mode,
                temperature=temperature,
            )

    def health_check(self) -> Dict[str, Any]:
        configured = bool(settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("your-"))
        return {
            "provider": "openai",
            "model": settings.OPENAI_MODEL,
            "configured": configured,
            "status": "ready" if configured else "missing_api_key",
        }


class OllamaProvider(LLMProvider):
    """Ollama local language model provider with resilient offline fallback."""

    def __init__(self):
        self.mock_fallback = MockProvider()

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.4,
    ) -> str:
        url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False,
            "options": {"temperature": temperature},
        }
        if json_mode:
            payload["format"] = "json"

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=40) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("response", "")
        except (urllib.error.URLError, ConnectionError, OSError) as e:
            logger.warning(
                f"Ollama daemon at {settings.OLLAMA_BASE_URL} is unreachable ({e}). "
                "Serving structured pedagogical fallback response."
            )
            return self.mock_fallback.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                json_mode=json_mode,
                temperature=temperature,
            )

    def health_check(self) -> Dict[str, Any]:
        is_live = False
        try:
            tag_url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags"
            req = urllib.request.Request(tag_url, method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    is_live = True
        except Exception:
            is_live = False

        return {
            "provider": "ollama",
            "model": settings.OLLAMA_MODEL,
            "base_url": settings.OLLAMA_BASE_URL,
            "configured": True,
            "status": "connected" if is_live else "daemon_offline (resilient fallback active)",
        }


class MockProvider(LLMProvider):
    """Deterministic offline mock provider for automated tests and offline development."""

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.4,
    ) -> str:
        if json_mode:
            # Check what kind of structured JSON was requested
            if "quiz" in prompt.lower():
                return json.dumps({
                    "title": "Practice Quiz: Core Concepts",
                    "questions": [
                        {
                            "id": "q1",
                            "prompt": "What is the primary benefit of binary search over linear search?",
                            "question_type": "multiple_choice",
                            "options": [
                                "It works on unsorted lists",
                                "O(log n) time complexity on sorted data",
                                "Uses more memory",
                                "Only works on strings",
                            ],
                            "correct_answer": "O(log n) time complexity on sorted data",
                            "explanation": "Binary search halves the search space each step, achieving logarithmic time.",
                            "topic_tag": "Algorithms",
                            "difficulty": "intermediate",
                        },
                        {
                            "id": "q2",
                            "prompt": "Quicksort has an average time complexity of O(n log n).",
                            "question_type": "true_false",
                            "options": ["True", "False"],
                            "correct_answer": "True",
                            "explanation": "Quicksort runs in O(n log n) average time on randomly distributed inputs.",
                            "topic_tag": "Sorting",
                            "difficulty": "intermediate",
                        },
                    ],
                })
            elif "flashcard" in prompt.lower():
                return json.dumps({
                    "title": "Topic Flashcards",
                    "flashcards": [
                        {
                            "id": "fc1",
                            "front": "What is the time complexity of QuickSort average case?",
                            "back": "O(n log n)",
                        },
                        {
                            "id": "fc2",
                            "front": "What data structure operates on LIFO (Last In First Out)?",
                            "back": "Stack",
                        },
                    ],
                })
            else:
                return json.dumps({
                    "title": "Generated Study Guide",
                    "sections": [
                        {
                            "title": "1. Overview & Objectives",
                            "content": "This topic covers essential algorithmic principles and foundations.",
                        },
                        {
                            "title": "2. Detailed Analysis",
                            "content": "We analyze asymptotic behavior and formal recurrences: $$T(n) = 2T(n/2) + O(n)$$.",
                        },
                    ],
                    "key_takeaways": ["Understand base cases", "Optimize space complexity"],
                    "citations": [],
                })

        return (
            "### Conceptual Explanation\n\n"
            "Here is a comprehensive, step-by-step breakdown of your question:\n\n"
            "1. **Core Principle**: The foundation relies on divide-and-conquer strategy.\n"
            "2. **Mathematical Formulation**: Asymptotics are represented via $$O(n \\log n)$$.\n"
            "3. **Practical Application**: In real-world software systems, this pattern ensures predictable low latency.\n\n"
            "Let me know if you would like worked examples or targeted quiz questions on this topic!"
        )

    def health_check(self) -> Dict[str, Any]:
        return {
            "provider": "mock",
            "model": "offline-educational-mock",
            "status": "ready",
        }


def get_llm_provider(provider_name: Optional[str] = None) -> LLMProvider:
    """Factory retrieving the configured LLM provider."""
    name = (provider_name or settings.DEFAULT_LLM_PROVIDER).lower()
    if name == "gemini":
        if gemini_service.is_configured():
            return GeminiProvider()
        # If gemini is requested but not configured, fallback gracefully to mock
        return MockProvider()
    elif name == "openai":
        return OpenAIProvider()
    elif name == "ollama":
        return OllamaProvider()
    elif name == "mock":
        return MockProvider()
    return MockProvider()
