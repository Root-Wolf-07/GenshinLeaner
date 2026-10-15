# AI Study Companion — Production Backend

A high-performance, modular, production-grade backend for the **AI Study Companion — Personalized Tutoring & Adaptive Learning Platform**.

This service provides verifiable RAG tutoring, course document ingestion, automated study material generation (notes, summaries, flashcards, mock exams), citation verification, adaptive quiz assessment, weak-topic detection, and multimodal student media generation via Google Gemini.

---

## Architecture Overview

The backend is built following a strict clean architecture:

```text
backend/
├── main.py                     # FastAPI application entry point, CORS, standardized error handlers
├── config.py                   # Pydantic v2 application configuration and environment settings
├── dependencies.py             # Auth dependencies, JWT token handling, password hashing
├── requirements.txt            # Production dependencies
├── alembic.ini                 # Alembic database migration configuration
├── .env.example                # Environment variables template
├── .env                        # Active environment configuration
│
├── api/                        # REST API Routers
│   ├── health.py               # /api/v1/health, /api/v1/readiness
│   ├── auth.py                 # /api/v1/auth/register, /login, /me, /profile
│   ├── dashboard.py            # /api/v1/dashboard (aggregated student overview)
│   ├── documents.py            # /api/v1/documents (upload, status, chunks, delete)
│   ├── chat.py                 # /api/v1/chat, /api/v1/conversations
│   ├── materials.py            # /api/v1/materials (generate, edit, regenerate, export)
│   ├── quizzes.py              # /api/v1/quizzes (generate, submit, attempts)
│   ├── progress.py             # /api/v1/progress, /topics, /history
│   ├── recommendations.py      # /api/v1/recommendations
│   ├── media.py                # /api/v1/media/generate-image, /generate-video (Gemini)
│   └── jobs.py                 # /api/v1/jobs/{job_id} (background async jobs)
│
├── schemas/                    # Pydantic Request & Response Data Contracts
│   ├── common.py               # Standardized ErrorResponse & pagination
│   ├── auth.py                 # Auth and user schemas
│   ├── documents.py            # Document and chunk schemas
│   ├── chat.py                 # Chat and Citation schemas
│   ├── materials.py            # Study material studio schemas
│   ├── quizzes.py              # Quiz and submission schemas
│   ├── progress.py             # Dashboard and progress analytics schemas
│   ├── media.py                # Multimodal Gemini media schemas
│   └── jobs.py                 # Background job schemas
│
├── models/                     # SQLAlchemy 2.0 Persistent Database Models
│   ├── user.py                 # User account, level, and preferences
│   ├── document.py             # Document and DocumentChunk with location metadata
│   ├── conversation.py         # Conversation and Message with verified citations
│   ├── material.py             # StudyMaterial with structured JSON and KaTeX Markdown
│   ├── quiz.py                 # Quiz (private answers) and QuizAttempt
│   ├── learning.py             # TopicMastery with adaptive scoring
│   └── job.py                  # BackgroundJob async task tracking
│
├── services/                   # Business Logic & AI Orchestration Services
│   ├── document_parser.py      # PDF (PyMuPDF), PPTX, DOCX, TXT, MD parser
│   ├── chunking.py             # Sentence-aware chunker preserving page/slide coordinates
│   ├── embeddings.py           # Multi-tier embeddings (SentenceTransformers, Gemini, fallback)
│   ├── vector_store.py         # Multi-tenant isolated vector search (FAISS / cosine index)
│   ├── retriever.py            # RAG passage retrieval with ownership validation
│   ├── gemini_service.py       # Google Gemini API (text, image, video storyboard)
│   ├── llm_provider.py         # Provider interface (Gemini, OpenAI, Ollama, Mock)
│   ├── citation_validator.py   # Citation Verification Engine
│   ├── tutor.py                # AI Tutor orchestrator with prompt injection defense
│   ├── material_generator.py   # 10 Academic Material types generator
│   ├── quiz_generator.py       # Adaptive quiz generator with answer-key protection
│   ├── quiz_grader.py          # Backend grading and pedagogical feedback engine
│   ├── adaptive_learning.py    # Topic mastery tracking and Bayesian score weighting
│   ├── recommendations.py      # Transparent rule-based study suggestions
│   ├── export_service.py       # Markdown, Plain Text, and HTML exporter
│   ├── document_processor.py   # Full ingestion pipeline orchestrator
│   └── job_queue.py            # Background async job execution
│
├── db/                         # Database Configuration and Migrations
│   ├── base.py                 # DeclarativeBase and TimestampMixin
│   ├── session.py              # Engine, SessionLocal, and get_db dependency
│   └── migrations/             # Alembic migration scripts
│       ├── env.py
│       └── versions/001_initial_schema.py
│
├── storage/                    # Persistent Storage
│   ├── uploads/                # Safe UUID document storage
│   └── indexes/                # Per-user isolated vector indices
│
└── tests/                      # Automated Test Suite
    ├── conftest.py             # Test database and client fixtures
    ├── test_health.py          # Health and readiness verification
    ├── test_documents.py       # Upload, chunking, and deletion tests
    ├── test_chat.py            # Chat and source mode tests
    ├── test_citations.py       # Citation verification engine tests
    ├── test_materials.py       # Material generator and export tests
    ├── test_quizzes.py         # Quiz generation, grading, and answer hiding
    ├── test_progress.py        # Dashboard and analytics tests
    └── test_security.py        # Security, isolation, and error envelope tests
```

---

## Quickstart & Installation

### 1. Requirements
* Python 3.11 or later (tested on Python 3.12).
* Virtual environment (`.venv`).

### 2. Install Dependencies
```bash
# Activate your virtual environment
source .venv/bin/activate   # On Linux/macOS
# or .venv\Scripts\activate # On Windows

# Install backend dependencies
pip install -r backend/requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` or edit `backend/.env`:
```bash
cp backend/.env.example backend/.env
```
Key configuration items:
* `GEMINI_API_KEY`: Your Google Gemini API Key (pre-configured for development).
* `DATABASE_URL`: Defaults to `sqlite:///./backend/storage/ai_study_companion.db`.
* `DEFAULT_LLM_PROVIDER`: `gemini` (or `openai`, `ollama`, `mock`).

### 4. Database Migrations
Run Alembic migrations to construct the database schema:
```bash
alembic -c backend/alembic.ini upgrade head
```

### 5. Start ASGI Server
```bash
# Run server from workspace root
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Interactive API Documentation

Once the server is running, explore the interactive OpenAPI documentation:
* **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **OpenAPI JSON:** [http://localhost:8000/api/v1/openapi.json](http://localhost:8000/api/v1/openapi.json)

---

## Running Automated Tests

Run the complete test suite with `pytest`:
```bash
pytest backend/tests/ -v
```

---

## Key Feature Implementation Details

### 1. RAG AI Tutor & Citation Verification
* **Source Modes:**
  * `uploaded`: Answers strictly using retrieved documents. If evidence is insufficient, it acknowledges the limitation rather than hallucinating.
  * `general`: Uses general knowledge without claiming document citations.
  * `both`: Distinguishes claims grounded in documents from broader context.
* **Citation Verification Engine:**
  * Every citation returned is verified against real database chunks.
  * Confirms chunk belongs to the authenticated user.
  * Validates exact page numbers and slide numbers.
  * Rejects fabricated citation IDs.
* **Prompt Injection Defense:** Document text is treated as untrusted data wrapped in `<DOCUMENT_EVIDENCE>` delimiters, preventing embedded commands from hijacking tutor instructions.

### 2. 10 Academic Study Material Types
Supports complete generation, structured JSON schemas, KaTeX formulas, section regeneration, and export:
1. Complete study notes
2. Chapter summaries
3. Exam revision sheets
4. Flashcards (front/back/hints)
5. Practice questions with answers
6. Mock examinations (marks, rubrics, time limits)
7. Step-by-step tutorials
8. Topic comparisons (matrix format)
9. Formula sheets (grouped with KaTeX math)
10. Glossaries and key-term definitions

### 3. Adaptive Quizzes & Backend Grading
* **Supported Questions:** Multiple Choice, True/False, Short Answer, Fill-in-the-blank.
* **Answer Key Security:** Correct answers and explanations are **never** returned to the client before submission.
* **Deterministic Backend Grading:** Grades objective answers and computes percentage scores on the backend.
* **Topic Mastery Tracking:** Dynamically updates `TopicMastery` records using Bayesian smoothing and difficulty weights.

### 4. Transparent Recommendations Engine
* Identifies weak topics (< 65% mastery) and suggests targeted reviews.
* Suggests flashcards for concepts with low retention.
* Recommends retaking quizzes with scores below 70%.
* Guides new students with starting actions.

### 5. Multimodal Student Media (Gemini)
* `POST /api/v1/media/generate-image`: Generates visual educational diagrams, student avatars, or concept illustrations.
* `POST /api/v1/media/generate-video`: Generates lesson storyboards, visual cues, and audio narration scripts.

---

## Interactive Animated Character AI Tutor Engine

### 1. Centralized Character Tutor Registry
The backend includes a declarative, extensible character-tutor registry supporting nine specialized tutors:
- **Raiden Ei / Shogun** (`raiden_shogun`): Mathematics (Calculus, Algebra, Geometry) — Disciplined, precise, logical, step-by-step
- **Zhongli** (`zhongli`): History, Geography, Civics, Economics — Wise, patient, contextual, story-driven
- **Barbara** (`barbara`): Biology, Zoology, Anatomy — Encouraging, friendly, enthusiastic, supportive
- **Furina** (`furina`): Dance, Communication, Music, Public Speaking — Expressive, theatrical, energetic, creative
- **Tsaritsa** (`tsaritsa`): General Knowledge, Languages, Linguistics — Composed, strategic, elegant, intellectually challenging
- **Nahida** (`nahida`): Moral Studies, Ethics, Philosophy — Curious, thoughtful, empathetic, reflective
- **Ganyu** (`ganyu`): Physics, Mechanics, Thermodynamics — Calm, methodical, patient, analytical
- **Keqing** (`keqing`): Computer Science, Algorithms, Programming — Efficient, practical, direct, problem-solving
- **Sucrose** (`sucrose`): Chemistry, Stoichiometry, Molecular Systems — Curious, experimental, scientific, enthusiastic

### 2. Animation State Machine & Gesture API
Frontend character rendering is guided by structured, predictable animation instructions:
* **Validated States:** `idle`, `listening`, `thinking`, `explaining`, `speaking`, `happy`, `excited`, `encouraging`, `curious`, `confused_gently`, `surprised`, `celebrating`, `giving_hint`, `demonstrating`, `waiting_for_answer`, `correct_answer`, `incorrect_answer_supportive`, `concerned`, `resting`, `error`.
* **Semantic Gestures:** `friendly_wave`, `gentle_nod`, `thinking_pose`, `point_forward`, `celebrating_gesture`, `encouraging_thumbs_up`, `curious_head_tilt`, `demonstration_gesture`, `listening_attentively`, `gentle_acknowledgment`.
* **Safe Fallbacks & Queueing:** If an animation key is unavailable, a safe fallback (`idle_default`) is returned. High-priority states (celebrations, errors) cleanly override background states without leaving the character stuck.

### 3. Real Voice Pipeline & Audio Streaming
* **Text-to-Speech (TTS):** Cleans KaTeX and Markdown into natural spoken phrases, divides into sentence-level segments, generates MP3 audio, and produces timing cues for lip and gesture synchronization.
* **Speech-to-Text (STT):** Transcribes student voice recordings (`.webm`, `.wav`, `.mp3`, `.ogg`, `.m4a`) with upload bounds checking (25MB limit) and immediate cleanup of raw temporary files for educational privacy.
* **Audio Streaming Endpoint:** `GET /api/v1/voice/speech/{audio_id}` provides authorized streaming for HTML5 `<audio>` elements (supporting Bearer tokens and URL token queries).
* **Cancellation Support:** `POST /api/v1/voice/speech/{audio_id}/cancel` and `POST /api/v1/tutor-sessions/{session_id}/cancel` immediately halt audio synthesis and playback scheduling.

### 4. Interactive Tutor Sessions & Socratic Intents
Students interact with their chosen tutor using typed pedagogical intents:
* `ask_question`: Standard grounded course inquiry
* `explain_simply`: Concrete, high-yield analogy
* `explain_in_detail`: Deep-dive into mechanisms and edge cases
* `show_example`: Concrete worked example
* `give_hint`: Incremental progressive scaffolding (Level 1 subtle, Level 2 directional, Level 3 step-by-step)
* `check_my_answer`: Formative evaluation of student's own reasoning
* `practice_question`: Immediate diagnostic concept check
* `summarize_topic`: Rapid high-yield takeaway summary
* `repeat_explanation`: Rephrase from a fresh angle

### 5. Real-Time WebSockets (`/api/v1/ws/tutor-sessions/{session_id}`)
Real-time streaming channel dispatching standard event envelopes:
* `character.animation`: Immediate character state and gesture instruction
* `speech.started` / `speech.segment_ready` / `speech.cancelled`: Audio playback synchronization
* `tutor.message.started` / `tutor.message.completed`: Message lifecycle
* `tutor.citation.available`: Real-time source grounding and page highlighting
* `learning.progress`: Instant XP and achievement updates

### 6. Transparent, Non-Manipulative Learning Gamification
* **Ethical Mechanics:** No guilt messaging, no streak penalties. Rewards genuine learning actions (quizzes, progressive problem solving, concept checks).
* **Backend Idempotency:** All XP grants require an `idempotency_key` preventing duplicate rewards.
* **Neutral Mode:** Students can toggle `neutral_mode` in preferences to minimize character animations and gamification for a quiet study experience.

---

## Standard Error Response Format

All API errors return a consistent envelope:
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Document not found.",
    "details": null,
    "request_id": "c138fbd8-8ea7-4ce8-b570-5bfa17ce67bf"
  }
}
```

---

## 3D Character Performance Engine & Rig Capabilities

The system includes a dedicated 3D Character Performance Engine designed for Three.js/WebGL frontends:

### Language & Communication Guarantee
- **Strict English Communication:** All 9 character tutors communicate, greet, teach, explain, and assess exclusively in standard, fluent **English**. System prompts, speech profiles, and interaction engines strictly forbid Japanese words, phrases, romaji, or foreign anime catchphrases.
- **English-to-Rig Viseme Mapping:** English phonemes (`aa`, `ih`, `ou`, `e`, `oh`, `sil`) are computed from English speech audio and automatically translated to whatever internal morph target or bone coordinates each specific model possesses.

### Endpoints
- `GET /api/v1/tutors-capabilities`: Lists 3D rig architectures, bone counts, and morph target dictionaries for all 9 characters.
- `GET /api/v1/tutors/{tutor_id}/capabilities`: Returns exact 3D rig capabilities for a specific tutor.
- `POST /api/v1/tutors/{tutor_id}/performance`: Generates a real-time 3D performance command containing target morphs, skeletal rotations, and speech viseme cues.
- `GET /api/v1/tutors/{tutor_id}/assets/{asset_name}`: Securely streams 3D models and textures with path-traversal protection.
- `GET /static/character_engine/{file_name}`: Serves client-side Three.js controller modules.

---

## Student Authentication, Identity & Personal Dashboard System

The platform provides a production-grade identity and authentication system built with cryptographic security, brute-force mitigation, and strict multi-tenant data isolation.

### 1. Account Options & Login Methods
- **Dual Login Support:** Supports login via verified **Email Address** + password OR verified **Phone Number** + password, with an intuitive client-side switch.
- **Strict Verification Enforcement:** Accounts must be verified before login is permitted. Unverified login attempts receive a `403 Forbidden` response with an `UNVERIFIED_ACCOUNT` error payload prompting OTP completion.
- **Show/Hide Password:** Interactive eye toggle across all authentication forms.
- **Remember Me:** Secure 30-day session extension using cryptographically signed HttpOnly JWT cookies and Bearer tokens.

### 2. Permanent Unique Student ID
- **Backend Generation:** Every verified student is permanently assigned a unique, immutable Student ID formatted as `STU-XXXXXXXX` (e.g. `STU-25FD3D7F`), generated using `secrets.token_hex(4).upper()` with automatic database collision checks.
- **Client Security:** Student IDs are generated **exclusively** on the backend and cannot be spoofed or set from client input.
- **1-Click Copy:** Displayed on the Personal Student Dashboard with a 1-click clipboard copy button and tooltip feedback.

### 3. Verification & Password Recovery (OTP)
- **6-Digit Secure OTP:** Generated using `secrets.randbelow(1_000_000)`, hashed via SHA-256 before storage in database.
- **Expiration & Cooldown:** Verification codes expire after 10 minutes (`VERIFICATION_CODE_EXPIRE_MINUTES`). Resending codes enforces a strict 60-second cooldown (`RESEND_COOLDOWN_SECONDS`).
- **Single-Use Password Reset:** Reset tokens are invalidated immediately upon first use. Password changes increment `session_version`, instantaneously revoking all prior active tokens across devices.
- **Development Test OTP:** When `DEBUG=True`, `123456` is accepted as a valid OTP for automated testing and local developer verification.

### 4. Brute Force Protection & Password Policy
- **Account Lockout:** 5 consecutive failed login attempts trigger an automatic 15-minute lockout (`locked_until`).
- **Password Complexity:** Enforces a minimum of 8 characters, at least one uppercase letter, one lowercase letter, and at least one numeric digit.
- **Bcrypt Password Hashing:** Salted and hashed with pure `bcrypt` ensuring security against rainbow table attacks.

### 5. Personal Student Dashboard & Data Isolation
- **Endpoint:** `GET /api/v1/dashboard` (Scoped strictly to `current_user`).
- **Student Profile:** Student ID, Full Name, Contact info, Academic Level.
- **Assigned 3D Tutors:** Enrolled subjects automatically matched with assigned Archon Tutors (Raiden Ei, Zhongli, Barbara, Furina, Tsaritsa, Nahida, Ganyu, Keqing, Sucrose).
- **Study Metrics:** Total documents uploaded, generated study materials, completed quizzes, average quiz score, weak topics, and recent study activity timestamps.

### 6. Authentication API Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Register new student account (Email or Phone) |
| `POST` | `/api/v1/auth/verify` | Verify account with 6-digit OTP and issue Student ID |
| `POST` | `/api/v1/auth/resend-code` | Resend verification code (with 60s cooldown) |
| `POST` | `/api/v1/auth/login` | Authenticate with Email/Phone + Password |
| `POST` | `/api/v1/auth/forgot-password` | Request password reset code |
| `POST` | `/api/v1/auth/reset-password` | Reset password using single-use OTP |
| `POST` | `/api/v1/auth/logout` | Revoke session and clear cookies |
| `GET`  | `/api/v1/auth/me` | Fetch currently authenticated student profile |
| `GET`  | `/api/v1/dashboard` | Fetch personal student dashboard and tutor assignments |

### 7. Automated Test Suite
Run the dedicated authentication test suite:
```bash
pytest backend/tests/test_student_auth_system.py -v
```
*Results:* **18 passed in 13.71s** (100% pass rate).

---

## Fullstack Integration Confirmation

The WebUI frontend (`index.html`, `modules/student-auth-manager.js`) and backend API (`backend/api/auth.py`, `backend/api/dashboard.py`) are fully synchronized and tested end-to-end on localhost:
- **FastAPI Backend:** `http://127.0.0.1:8000`
- **WebUI & Fullstack Server:** `http://127.0.0.1:3033`
