# Genshin Cognitive Academy • 3D AI Tutor & Study Companion

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Three.js](https://img.shields.io/badge/Three.js-WebGL%203D-black.svg?logo=three.js&logoColor=white)](https://threejs.org/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-2.5%20Flash-4285F4.svg?logo=google&logoColor=white)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An immersive, full-stack educational platform combining **interactive 3D Genshin Impact character tutors** with an enterprise-grade **AI Study Companion backend**. 

Students receive personalized Socratic instruction across 9 academic disciplines with synchronized 3D character animations, real-time voice synthesis, verifiable Retrieval-Augmented Generation (RAG) over uploaded course materials, and adaptive topic assessments.

---

## Architecture Overview

The repository is organized to allow either **unified full-stack execution** (frontend + backend served concurrently on one port) or **decoupled microservice execution**:

```text
GenshinLeaner/
├── index.html                   # 3D Animated WebUI frontend (HTML5/Tailwind/Three.js)
├── styles.css                   # Custom Genshin celestial glassmorphic UI design system
├── app.js                       # Frontend controller, state machine, SSE & audio playback
├── server.py                    # Unified FastAPI Server (serves WebUI + SSE + /api/v1 routes)
├── .env.example                 # Root environment variables template
├── assets/                      # High-resolution backdrops, textures, and generated audio
├── Charater Models/             # 3D GLTF / GLB / FBX models for all 9 academic tutors
│   ├── furina/                  # Lady Furina (Dance, Communication & Music)
│   ├── barbara/                 # Barbara Pegg (Biology & Zoology)
│   ├── ganyu/                   # Ganyu (Physics & Mechanics)
│   ├── keqing/                  # Keqing (Computer Science & Algorithms)
│   ├── nahida/                  # Nahida (Moral Studies & Philosophy)
│   ├── sucrose/                 # Sucrose (Chemistry & Stoichiometry)
│   ├── tsaritsa/                # The Tsaritsa (General Knowledge & Languages)
│   └── zhongli/                 # Zhongli (Humanities & Social Sciences)
│
└── backend-for-3d-ai-tutor-genshin-impact--main/
    └── backend/                 # Enterprise Production Backend
        ├── main.py              # Standalone FastAPI entry point & exception handlers
        ├── config.py            # Pydantic v2 application configuration & safe environment loader
        ├── dependencies.py      # JWT authentication, bcrypt hashing & demo student fixture
        ├── api/                 # REST routers (auth, chat, documents, materials, quizzes, etc.)
        ├── models/              # SQLAlchemy 2.0 ORM database models
        ├── schemas/             # Pydantic data validation schemas & event contracts
        ├── services/            # RAG, FAISS vector search, Gemini AI, parser & adaptive grader
        ├── storage/             # SQLite database, uploaded files, and vector indices
        └── tests/               # Automated unit, integration, and security test suite
```

---

## Frontend Use Cases & Features

The frontend is an interactive 3D WebGL web application engineered with **Three.js**, **Tailwind CSS**, and modern browser APIs:

### 1. Interactive 3D Character AI Tutors
* **Full 3D Character Viewports:** Loads high-fidelity 3D models with orbit controls, dynamic lighting, and responsive aspect ratios.
* **9 Academic Disciplines & Character Personas:**
  | Academic Discipline | Assigned Character Tutor | Element Affinity | Core Pedagogical Focus |
  | :--- | :--- | :--- | :--- |
  | **Dance, Communication & Music** | **Lady Furina ✦** | Hydro (Ousia) | Theatrical oratory, rhetoric, public speaking & artistic expression |
  | **Mathematics & Calculus** | **Raiden Ei / Shogun** | Electro | Invariant axioms, calculus, algebra, and rigorous formal logic |
  | **Humanities & Social Sciences** | **Zhongli** | Geo | Contracts, economic trade routes, historical epochs & civilization |
  | **Biology & Zoology** | **Barbara Pegg** | Hydro | Cellular respiration, genetics, double-helix DNA & living ecosystems |
  | **Moral Studies & Philosophy** | **Lesser Lord Kusanali (Nahida)** | Dendro | Ethical dilemmas, Veil of Ignorance & critical moral reflection |
  | **Physics & Mechanics** | **Ganyu** | Cryo | Newtonian mechanics, conservation laws, kinematics & equilibrium |
  | **Computer Science** | **Keqing** | Electro | Algorithms, asymptotic time complexity O(n), trees & system architecture |
  | **Chemistry & Stoichiometry** | **Sucrose** | Anemo | Molecular bonding, Le Chatelier's principle & reaction mechanisms |
  | **General Knowledge & Languages**| **The Tsaritsa** | Cryo | Linguistics, comparative syntax, literature & world history |

### 2. Socratic State Machine & Reactive Dialogue
* Dynamically shifts character states across: `idle`, `thinking`, `speaking`, `explaining`, `questioning`, `encouraging`, and `celebrating`.
* The interface dynamically transitions accent colors, elemental particle glows, and character dialogues based on the user's inquiry.

### 3. Real-Time Speech Synthesis & Lip-Sync (Visemes)
* Emits timestamped viseme speech events (`aa`, `oh`, `ee`, `ou`, `closed`) synchronized with audio playback.
* Integrated audio unlocking banner allowing seamless local browser speech playback via Web Audio API or local macOS system voices (`say`).

### 4. Student Portal & Gamification
* Real-time **Primogem counter** (`✦ 1,600 PRIMOS`) that rewards consistent study habits and correct quiz submissions.
* Quick API Key configuration modal (allowing live Gemini or OpenAI keys to be configured directly in-browser or read from server `.env`).

---

## Backend Use Cases & Features

The backend is built with **FastAPI**, **SQLAlchemy 2.0**, **FAISS**, and **Google Gemini**:

### 1. Verifiable RAG & Course Document Ingestion
* Ingests multi-format lecture documents: **PDF** (via PyMuPDF), **DOCX**, **PPTX**, **TXT**, and **Markdown**.
* Sentence-aware chunker preserves page numbers and slide coordinates for verified provenance.
* Hybrid vector retrieval with **FAISS** and SentenceTransformers (`all-MiniLM-L6-v2`) or Gemini Embeddings (`text-embedding-004`).

### 2. Automated Study Material Studio
Generates 10 structured academic material formats on demand:
* Comprehensive study notes with KaTeX equations
* Executive summary cheat sheets
* Interactive flashcard decks (Q&A format)
* Formula and definition sheets
* Practice problem sets with pedagogical hints
* Full mock examinations with grading keys

### 3. Adaptive Quiz Assessment & Bayesian Mastery
* Automatically synthesizes multiple-choice and short-answer quizzes from uploaded documents.
* Answer keys remain strictly protected on the backend to prevent cheating.
* Automatic grading engine analyzes student answers, returns diagnostic feedback, and adjusts the student's Bayesian Topic Mastery score.

### 4. Multimodal AI Integration (Google Gemini)
* Integrates `gemini-2.5-flash` for low-latency Socratic conversational tutoring.
* Structured prompt injection defenses and strict academic topic boundary enforcement.
* Educational diagram and media generation endpoints via Gemini Image & Video storyboarding APIs.

### 5. Multi-Tenant User Isolation & Security
* JWT Bearer authentication with token expiration handling.
* Password hashing using `bcrypt` with PBKDF2 HMAC-SHA256 fallback.
* Auto-seeds a demo student user for instant zero-configuration testing.

---

## How to Access & Run

### Prerequisites
* **Python 3.10+** (Tested on Python 3.11, 3.12, and 3.14 on macOS, Linux, and Windows).
* A modern web browser supporting **WebGL** (Google Chrome, Apple Safari, Microsoft Edge, or Mozilla Firefox).

---

### Step 1: Clone the Repository & Create Virtual Environment

```bash
# Clone the repository
git clone https://github.com/Root-Wolf-07/GenshinLeaner.git
cd GenshinLeaner

# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
# On macOS / Linux:
source .venv/bin/activate

# On Windows:
# .venv\Scripts\activate
```

---

### Step 2: Install Dependencies

Install all core dependencies for the FastAPI server, document parsers, vector store, and AI modules:

```bash
pip install -r backend-for-3d-ai-tutor-genshin-impact--main/backend/requirements.txt
```

---

### Step 3: Configure Environment Variables

Copy the provided `.env.example` file to create your active `.env`:

```bash
cp .env.example .env
```

*(Optional)* To enable live AI reasoning with Google Gemini, open `.env` and set your API key:
```ini
GEMINI_API_KEY="your-gemini-api-key-here"
```
> **Note:** If no API key is set, the server runs in built-in **Socratic Knowledge Base Mode**, delivering authentic pre-calibrated dialogues and speech synthesis for all 9 characters without requiring an external API.

---

### Step 4: Launch the Application

You can launch the system in one of two modes:

#### Mode A: Unified Full-Stack Server (Recommended)
This mode launches both the **3D WebUI frontend** and all **backend API endpoints** together on port `3033`:

```bash
python3 server.py
```

Once running, access the application in your browser:
* **Interactive 3D WebUI:** [http://localhost:3033](http://localhost:3033)
* **Interactive Swagger API Docs:** [http://localhost:3033/docs](http://localhost:3033/docs)
* **ReDoc API Documentation:** [http://localhost:3033/redoc](http://localhost:3033/redoc)
* **Health Check Endpoint:** [http://localhost:3033/api/health](http://localhost:3033/api/health)

#### Mode B: Dedicated Standalone Backend Server
For backend-only development, automated testing, or microservice deployments:

```bash
cd backend-for-3d-ai-tutor-genshin-impact--main
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

* **Backend Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Backend OpenAPI Specification:** [http://localhost:8000/api/v1/openapi.json](http://localhost:8000/api/v1/openapi.json)

---

## How to Use the Web Interface

1. **Select an Academic Tutor:**
   * Click on any of the 9 character cards at the top of the interface (e.g., *Lady Furina*, *Raiden Shogun*, *Zhongli*, *Barbara*, etc.).
   * The 3D viewport instantly transitions to the selected character's 3D model, element, and voice profile.

2. **Interact with the 3D Character:**
   * **Left-Click + Drag:** Rotate and orbit around the character.
   * **Scroll Wheel:** Zoom in and out.
   * **Right-Click + Drag:** Pan the camera viewport.

3. **Engage in Socratic Tutoring:**
   * Type your question into the chat bar (e.g., *"How does Le Chatelier's principle work?"* or *"Explain the fundamental theorem of calculus"*).
   * Press **Enter** or click **Send**. The tutor will transition to `thinking` state, synthesize an explanation, update their facial visemes, and speak the answer.

4. **Enable Voice Audio:**
   * Browsers require a user gesture before playing sound. Click the **"Voice Audio: Active"** button in the header bar to test or unlock audio playback.

5. **Student Portal & Authentication:**
   * Click the **"Sign In / Register"** pill in the top right to access student profiles, review progress history, or test document uploads.

---

## Core API Endpoints Reference

### Unified Tutor & Real-Time Endpoints (`server.py`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status and list of all 9 active character tutors |
| `GET` | `/api/tutors` | Retrieves metadata, subject, element, and default dialogues for all tutors |
| `POST` | `/api/tutor/chat` | Main dialogue endpoint: routes subject queries, generates response & visemes |
| `GET` | `/api/tutor/tts` | Generates on-demand playable character speech WAV |
| `GET` | `/api/tutor/events/{session_id}` | Server-Sent Events (SSE) stream for real-time state and speech updates |

### Production Study Companion Endpoints (`/api/v1`)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Register new student account |
| `POST` | `/api/v1/auth/login` | Authenticate and obtain JWT bearer token |
| `GET` | `/api/v1/dashboard` | Aggregated student overview, study time & topic mastery |
| `POST` | `/api/v1/documents` | Upload PDF, DOCX, PPTX or TXT course documents |
| `GET` | `/api/v1/documents` | List uploaded course documents and chunking status |
| `POST` | `/api/v1/materials` | Generate study notes, summaries, flashcards, or mock exams |
| `POST` | `/api/v1/quizzes` | Generate adaptive quiz based on document knowledge base |
| `POST` | `/api/v1/quizzes/{id}/submit` | Grade student quiz submission and update topic mastery |
| `GET` | `/api/v1/progress` | Bayesian topic mastery radar and weak-topic detection |

---

## Running Automated Tests

To run the automated test suite across all services, routers, and citation engines:

```bash
# Make sure your virtual environment is active
source .venv/bin/activate

# Run backend test suite
pytest backend-for-3d-ai-tutor-genshin-impact--main/backend/tests -v
```

---

## License

This project is open-source under the [MIT License](LICENSE). 3D character models and intellectual property of Genshin Impact are copyright © [COGNOSPHERE / miHoYo](https://genshin.hoyoverse.com/).
