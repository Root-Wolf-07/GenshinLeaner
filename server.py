"""
Genshin Cognitive Academy • Backend Multi-Character Dialogue & Adaptive Learning Server
FastAPI Server providing real-time AI tutor conversation across 9 academic subjects,
session management, typed dialogue event contracts, speech synthesis metadata,
and static file delivery for 3D Three.js characters.
"""

import os
import sys
import time
import uuid
import asyncio
import subprocess
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

# Setup sys.path for imported backend services
backend_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend-for-3d-ai-tutor-genshin-impact--main")
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

# Try importing backend routers and services
try:
    from backend.api import api_router
    from backend.services.tutor_profiles import tutor_registry
    HAS_BACKEND_SERVICES = True
except Exception as e:
    print(f"Notice: backend module import: {e}")
    HAS_BACKEND_SERVICES = False
    tutor_registry = None

# --- Initialize FastAPI Application ---
app = FastAPI(
    title="Genshin Cognitive Academy • Multi-Character 3D AI Tutor Service",
    description="Full-stack AI tutoring platform with 9 academic subjects, 3D character viewers, and real-time speech synchronization",
    version="4.0.0"
)

# Enable CORS for local development and IDE previews
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount /api/v1 router if available
if HAS_BACKEND_SERVICES:
    try:
        app.include_router(api_router, prefix="/api/v1")
        print("✓ Successfully mounted /api/v1 backend routes")
    except Exception as e:
        print(f"Notice mounting /api/v1 router: {e}")

# --- Data Models & Typed Event Contracts ---
class ChatRequest(BaseModel):
    session_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str
    subject: Optional[str] = None
    tutor_id: Optional[str] = None
    user_id: Optional[str] = "traveler_student"
    api_key: Optional[str] = None

class VisemeEvent(BaseModel):
    time_ms: int
    viseme: str # 'closed', 'aa', 'oh', 'ee', 'ou'
    intensity: float

class SpeechSegment(BaseModel):
    text: str
    start_ms: int
    end_ms: int
    state: str # 'speaking' | 'explaining' | 'questioning' | 'encouraging' | 'celebrating'
    visemes: List[VisemeEvent] = []

class DialogueResponse(BaseModel):
    session_id: str
    message_id: str
    event: str = "tutor_response_ready"
    tutor_id: str
    tutor_name: str
    subject: str
    element: str
    accent_color: str
    text: str
    audio_url: Optional[str] = None
    state: str
    segments: List[SpeechSegment]
    created_at: float

class StateUpdate(BaseModel):
    session_id: str
    state: str

# In-memory session store & SSE queues
sessions: Dict[str, Dict[str, Any]] = {}
active_sse_queues: Dict[str, asyncio.Queue] = {}

# --- Canonical 9-Character Subject Curriculum Database ---
SUBJECT_TUTOR_PROFILES = {
    "raiden_shogun": {
        "id": "raiden_shogun",
        "name": "Raiden Ei / Shogun",
        "subject": "Mathematics",
        "element": "Electro",
        "color": "#a259ff",
        "voice": "Samantha",
        "pitch": "-2",
        "rate": "175",
        "dialogues": {
            "default": "In the realm of mathematics, truth is invariant across eternity. Break down the variables and define each axiom step by step.",
            "calculus": "The fundamental theorem of calculus establishes that differentiation and integration are inverse operations. Notice how the derivative tracks infinitesimal tangents!",
            "algebra": "Balance the linear constraints. When solving for the unknown, perform equivalent operations symmetrically to preserve mathematical equilibrium.",
            "correct": "Exemplary precision! A rigorous derivation worthy of praise. You have mastered the mathematical principle with complete logical fidelity."
        }
    },
    "zhongli": {
        "id": "zhongli",
        "name": "Zhongli",
        "subject": "Humanities & Social Sciences",
        "element": "Geo",
        "color": "#e5b042",
        "voice": "Alex",
        "pitch": "-4",
        "rate": "165",
        "dialogues": {
            "default": "Every society is built upon foundational contracts and historical memory. What epoch or economic structure shall we dissect?",
            "history": "To understand historical shifts, examine the economic incentives and institutional pressures that guided leaders beyond simplistic narratives.",
            "geography": "Topography dictates trade corridors. Mountain ranges and maritime straits historically formed natural economic monopolies and cultural boundaries.",
            "correct": "An astute deduction. Understanding history requires patience, perspective, and a deep appreciation for the human contract."
        }
    },
    "barbara": {
        "id": "barbara",
        "name": "Barbara Pegg",
        "subject": "Biology & Zoology",
        "element": "Hydro",
        "color": "#4fc3f7",
        "voice": "Victoria",
        "pitch": "+3",
        "rate": "185",
        "dialogues": {
            "default": "Life is full of wonderful miracles, from microscopic cellular membranes to giant blue whales! Where shall we sing our lesson today?",
            "cell": "Mitochondria are the powerhouses of the cell! By pumping protons across their inner membrane, they spin ATP synthase like a tiny waterwheel!",
            "genetics": "DNA strands twist in a double helix! Adenine pairs with Thymine, while Cytosine pairs with Guanine, encoding the symphony of life.",
            "correct": "Wonderful job! Every cell in your deduction is full of vitality and sparkling joy! ✦"
        }
    },
    "furina": {
        "id": "furina",
        "name": "Lady Furina ✦",
        "subject": "Dance, Communication & Music",
        "element": "Hydro (Ousia)",
        "color": "#38bdf8",
        "voice": "Samantha",
        "pitch": "+2",
        "rate": "180",
        "dialogues": {
            "default": "Welcome to our grand theatrical seminar! Do not fear missteps on this stage—every question reveals a path to rhetorical mastery!",
            "reaction": "Behold the stage of Fontaine! When Hydro encounters Electro, Electro-Charged cascades through the tides like a dramatic opera chorus! Mon cher student, can you deduce which fiery element triggers the theatrical crescendo of Vaporize?",
            "oratory": "In persuasive speech, ethos establishes your authentic presence, logos provides structural foundation, and pathos captivates the audience heart!",
            "correct": "Magnifique! Bravo, mon cher Traveler! A flawless deduction worthy of the grandest applause in the Opera Epiclese! The stage is truly yours!"
        }
    },
    "tsaritsa": {
        "id": "tsaritsa",
        "name": "The Tsaritsa",
        "subject": "General Knowledge & Languages",
        "element": "Cryo",
        "color": "#93c5fd",
        "voice": "Samantha",
        "pitch": "-1",
        "rate": "170",
        "dialogues": {
            "default": "Language is the architecture of civilization. Master its syntax and etymological roots, and no knowledge will remain closed to you.",
            "linguistics": "Systematic sound shifts explain why Latin and Germanic languages share ancient Proto-Indo-European cognates across thousands of miles.",
            "literature": "Classic literature explores universal conflicts between personal volition and collective destiny. Read deeply beneath the literal text.",
            "correct": "Dignified and precise. You possess the intellectual fortitude demanded of true linguistic mastery."
        }
    },
    "nahida": {
        "id": "nahida",
        "name": "Lesser Lord Kusanali (Nahida)",
        "subject": "Moral Studies",
        "element": "Dendro",
        "color": "#5cb85c",
        "voice": "Samantha",
        "pitch": "+3",
        "rate": "180",
        "dialogues": {
            "default": "Curiosity is the seed from which wisdom grows! What moral riddle or philosophical dilemma shall we water together?",
            "ethics": "When facing a dilemma, ask yourself: what would happen if everyone made this choice? Look at the problem from the smallest perspective to the whole.",
            "philosophy": "Rawls’s Veil of Ignorance reminds us to design rules for society as though we might be born into the most vulnerable position.",
            "correct": "A beautiful reflection! Your understanding blooms like a blossoming Padisarah in full morning sunlight! ✦"
        }
    },
    "ganyu": {
        "id": "ganyu",
        "name": "Ganyu",
        "subject": "Physics",
        "element": "Cryo",
        "color": "#67e8f9",
        "voice": "Samantha",
        "pitch": "0",
        "rate": "172",
        "dialogues": {
            "default": "Physical laws govern every trajectory in nature. Let us balance our forces and examine the conservation laws step by step.",
            "mechanics": "Newton's laws tell us that acceleration is directly proportional to net force and inversely proportional to mass. Always draw your free-body diagram first!",
            "energy": "Energy cannot be created or destroyed, only transformed. In isolated systems, total mechanical energy remains rigorously conserved.",
            "correct": "Remarkably calculated! The physical equilibrium and conservation of your solution is completely sound."
        }
    },
    "keqing": {
        "id": "keqing",
        "name": "Keqing",
        "subject": "Computer Science",
        "element": "Electro",
        "color": "#c084fc",
        "voice": "Samantha",
        "pitch": "+1",
        "rate": "182",
        "dialogues": {
            "default": "Efficiency, clean invariants, and optimal algorithms. Procrastination solves zero bugs—let us trace the code to its root cause!",
            "algorithms": "When analyzing time complexity, identify the dominant operation. A hash table offers average O(1) lookups, but watch out for hash collision degradation!",
            "trees": "Self-balancing binary trees like Red-Black trees guarantee O(log n) worst-case search by enforcing strict color balancing invariants.",
            "correct": "Decisive, optimal, and elegant! Time complexity O(1), zero edge-case regressions detected!"
        }
    },
    "sucrose": {
        "id": "sucrose",
        "name": "Sucrose",
        "subject": "Chemistry",
        "element": "Anemo",
        "color": "#34d399",
        "voice": "Samantha",
        "pitch": "+2",
        "rate": "180",
        "dialogues": {
            "default": "H-hello! I have carefully calibrated our glassware and reaction flasks. Let’s observe the wonders of chemical bonding together!",
            "reaction": "Chemical equilibrium shifts to relieve applied stress according to Le Chatelier’s principle. Observe how exothermic reactions shift left when heated!",
            "molecules": "Covalent bonds share electron pairs to fill valence octets. Electronegativity differences determine whether a molecular bond is polar or non-polar.",
            "correct": "E-excellent deduction! The reaction mechanism achieved 100% stoichiometric yield! ✦"
        }
    }
}

# --- Subject Normalization Helper ---
def resolve_tutor(tutor_id: Optional[str], subject: Optional[str], query: str) -> Dict[str, Any]:
    if tutor_id and tutor_id.lower() in SUBJECT_TUTOR_PROFILES:
        return SUBJECT_TUTOR_PROFILES[tutor_id.lower()]
    
    clean_sub = (subject or "").lower()
    clean_query = query.lower()
    
    if "math" in clean_sub or "calculus" in clean_query or "algebra" in clean_query or "matrix" in clean_query or "derivative" in clean_query:
        return SUBJECT_TUTOR_PROFILES["raiden_shogun"]
    elif "humanities" in clean_sub or "history" in clean_sub or "civics" in clean_query or "rome" in clean_query or "trade" in clean_query:
        return SUBJECT_TUTOR_PROFILES["zhongli"]
    elif "biology" in clean_sub or "zoology" in clean_sub or "cell" in clean_query or "dna" in clean_query or "organism" in clean_query:
        return SUBJECT_TUTOR_PROFILES["barbara"]
    elif "general knowledge" in clean_sub or "language" in clean_sub or "linguistic" in clean_query or "grammar" in clean_query:
        return SUBJECT_TUTOR_PROFILES["tsaritsa"]
    elif "moral" in clean_sub or "ethics" in clean_query or "philosophy" in clean_query or "justice" in clean_query:
        return SUBJECT_TUTOR_PROFILES["nahida"]
    elif "physics" in clean_sub or "force" in clean_query or "momentum" in clean_query or "velocity" in clean_query:
        return SUBJECT_TUTOR_PROFILES["ganyu"]
    elif "computer" in clean_sub or "algorithm" in clean_query or "code" in clean_query or "data structure" in clean_query or "binary" in clean_query:
        return SUBJECT_TUTOR_PROFILES["keqing"]
    elif "chemistry" in clean_sub or "molecule" in clean_query or "stoichiometry" in clean_query or "reaction" in clean_query:
        return SUBJECT_TUTOR_PROFILES["sucrose"]
    elif "dance" in clean_sub or "music" in clean_sub or "theater" in clean_query or "hydro" in clean_query or "opera" in clean_query:
        return SUBJECT_TUTOR_PROFILES["furina"]

    return SUBJECT_TUTOR_PROFILES["furina"]

# --- API Endpoints ---

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Genshin Cognitive Academy • 3D AI Tutor Engine",
        "tutors_available": list(SUBJECT_TUTOR_PROFILES.keys()),
        "version": "4.0.0"
    }

@app.get("/api/tutors")
@app.get("/api/v1/tutors")
async def list_tutors_endpoint():
    """List all 9 canonical academic character tutors."""
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "subject": t["subject"],
            "element": t["element"],
            "color": t["color"],
            "voice": t["voice"],
            "default_line": t["dialogues"]["default"]
        }
        for t in SUBJECT_TUTOR_PROFILES.values()
    ]

@app.post("/api/tutor/chat", response_model=DialogueResponse)
@app.post("/api/v1/chat")
async def tutor_chat(req: ChatRequest):
    """
    Main dialogue endpoint: dynamically routes questions across all 9 subjects,
    synthesizes authentic character persona answers, generates speech audio WAV,
    and returns timestamped viseme speech segments.
    """
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    session_id = req.session_id or f"session_{uuid.uuid4().hex[:8]}"
    message_id = f"msg_{uuid.uuid4().hex[:10]}"
    query_lower = req.message.lower().strip()

    # Track session state
    if session_id not in sessions:
        sessions[session_id] = {
            "created_at": time.time(),
            "history": [],
            "current_message_id": message_id
        }
    sessions[session_id]["current_message_id"] = message_id
    sessions[session_id]["history"].append({"sender": "student", "text": req.message})

    # Resolve assigned character tutor
    tutor = resolve_tutor(req.tutor_id, req.subject, req.message)

    # Notify SSE queue if connected
    if session_id in active_sse_queues:
        await active_sse_queues[session_id].put({
            "session_id": session_id,
            "message_id": message_id,
            "event": "user_message_received",
            "tutor_id": tutor["id"],
            "state": "thinking"
        })

    # Select or synthesize pedagogical response
    responseText = None
    state = "speaking"
    dialogues = tutor["dialogues"]

    # 1. Check if LLM API Key is provided (Gemini or OpenAI)
    api_key = req.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if api_key:
        system_instruction = (
            f"You are {tutor['name']}, the virtual 3D AI Tutor for {tutor['subject']} in the Genshin Cognitive Academy. "
            f"Elemental affinity: {tutor['element']}. "
            f"Answer the student's question thoughtfully in character with {tutor['name']}'s tone, wisdom, and personality. "
            f"Adopt a Socratic pedagogical approach: clarify the foundational mechanism, provide an illuminating analogy, "
            f"and pose an encouraging follow-up thought. Keep your spoken output concise and clear (2 to 4 sentences max)."
        )
        try:
            if api_key.startswith("AIza") or "gemini" in api_key.lower():
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system_instruction)
                resp = model.generate_content(req.message)
                if resp and resp.text:
                    responseText = resp.text.strip()
                    state = "explaining"
            elif api_key.startswith("sk-") or "openai" in api_key.lower():
                import openai
                client = openai.OpenAI(api_key=api_key)
                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": req.message}
                    ],
                    max_tokens=220
                )
                if completion.choices:
                    responseText = completion.choices[0].message.content.strip()
                    state = "explaining"
        except Exception as e:
            print(f"Notice during LLM query: {e}")

    # 2. Dynamic Discipline & Socratic Engine Fallback
    if not responseText:
        if "correct" in query_lower or "bravo" in query_lower or "right answer" in query_lower:
            responseText = dialogues.get("correct", f"Magnificent deduction! Your grasp of {tutor['subject']} shines with brilliant clarity.")
            state = "celebrating"
        else:
            matchedKey = None
            for key in dialogues:
                if key != "default" and key != "correct" and key in query_lower:
                    matchedKey = key
                    break
            
            if matchedKey:
                responseText = dialogues[matchedKey]
                state = "explaining"
            elif len(req.message.strip().split()) > 3:
                # Dynamic response for custom typed student inquiries
                prefix = {
                    "raiden_shogun": "An intriguing mathematical premise.",
                    "zhongli": "Reflecting upon historical records and bedrock principles,",
                    "barbara": "What a wonderful question about living organisms!",
                    "furina": "A dramatic inquiry presented to the Grand Court of Fontaine!",
                    "tsaritsa": "Through rigorous intellectual inquiry across all domains,",
                    "nahida": "Knowledge is a sprawling tree, and your curiosity waters its roots!",
                    "ganyu": "Checking the fundamental principles of physical matter and motion,",
                    "keqing": "Speed, precision, and structural efficiency are paramount in computational logic.",
                    "sucrose": "According to bio-alchemical transformation records,"
                }.get(tutor["id"], "An insightful inquiry.")

                responseText = f"{prefix} When analyzing '{req.message.strip()}', we must examine the governing axioms of {tutor['subject']}. Notice how the core principles establish equilibrium, leading to predictable and verifiable conclusions."
                state = "explaining"
            else:
                responseText = dialogues["default"]
                state = "speaking"

    # Construct typed speech segments with millisecond offsets and visemes
    words = responseText.split()
    midpoint = len(words) // 2
    seg1_text = " ".join(words[:midpoint])
    seg2_text = " ".join(words[midpoint:])

    seg1_duration = max(2000, len(seg1_text) * 60)
    seg2_duration = max(2000, len(seg2_text) * 60)

    segments = [
        SpeechSegment(
            text=seg1_text,
            start_ms=0,
            end_ms=seg1_duration,
            state=state if state == "celebrating" else "explaining",
            visemes=[
                VisemeEvent(time_ms=200, viseme="aa", intensity=0.9),
                VisemeEvent(time_ms=int(seg1_duration * 0.4), viseme="oh", intensity=0.95),
                VisemeEvent(time_ms=int(seg1_duration * 0.7), viseme="ee", intensity=0.8),
                VisemeEvent(time_ms=seg1_duration - 100, viseme="closed", intensity=0.0)
            ]
        ),
        SpeechSegment(
            text=seg2_text,
            start_ms=seg1_duration + 100,
            end_ms=seg1_duration + 100 + seg2_duration,
            state="speaking" if state != "celebrating" else "celebrating",
            visemes=[
                VisemeEvent(time_ms=seg1_duration + 300, viseme="oh", intensity=0.85),
                VisemeEvent(time_ms=seg1_duration + int(seg2_duration * 0.5), viseme="aa", intensity=0.9),
                VisemeEvent(time_ms=seg1_duration + int(seg2_duration * 0.8), viseme="ee", intensity=0.85),
                VisemeEvent(time_ms=seg1_duration + seg2_duration, viseme="closed", intensity=0.0)
            ]
        )
    ]

    # Generate real audible speech audio file (WAV) on localhost
    audio_url = None
    try:
        audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "audio")
        os.makedirs(audio_dir, exist_ok=True)
        audio_filename = f"{message_id}.wav"
        audio_filepath = os.path.join(audio_dir, audio_filename)

        clean_text = responseText.replace('"', '').replace("'", "")
        cmd = ["say", "-v", tutor["voice"], "-r", tutor["rate"], "-o", audio_filepath, "--data-format=LEI16@22050", clean_text]
        subprocess.run(cmd, check=True, timeout=8)
        if os.path.exists(audio_filepath):
            audio_url = f"/assets/audio/{audio_filename}"
    except Exception as e:
        print(f"Speech synthesis notice: {e}")
        audio_url = None

    response_payload = DialogueResponse(
        session_id=session_id,
        message_id=message_id,
        event="tutor_response_ready",
        tutor_id=tutor["id"],
        tutor_name=tutor["name"],
        subject=tutor["subject"],
        element=tutor["element"],
        accent_color=tutor["color"],
        text=responseText,
        audio_url=audio_url,
        state=state,
        segments=segments,
        created_at=time.time()
    )

    sessions[session_id]["history"].append({"sender": tutor["id"], "text": responseText})
    return response_payload

@app.post("/api/tutor/state")
async def update_tutor_state(update: StateUpdate):
    valid_states = {"idle", "listening", "thinking", "speaking", "explaining", "questioning", "encouraging", "celebrating", "error"}
    if update.state not in valid_states:
        raise HTTPException(status_code=400, detail=f"Invalid state: {update.state}")

    if update.session_id in active_sse_queues:
        await active_sse_queues[update.session_id].put({
            "session_id": update.session_id,
            "event": "state_updated",
            "state": update.state
        })
    return {"status": "updated", "session_id": update.session_id, "state": update.state}

@app.get("/api/tutor/tts")
async def tts_endpoint(text: str, voice: Optional[str] = "Samantha", rate: Optional[str] = "180"):
    """On-demand Text-to-Speech audio generator returning playable WAV URL."""
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Text required")
    msg_id = f"tts_{uuid.uuid4().hex[:8]}"
    audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "audio")
    os.makedirs(audio_dir, exist_ok=True)
    audio_filename = f"{msg_id}.wav"
    audio_filepath = os.path.join(audio_dir, audio_filename)
    try:
        clean_text = text.replace('"', '').replace("'", "")
        cmd = ["say", "-v", voice, "-r", rate, "-o", audio_filepath, "--data-format=LEI16@22050", clean_text]
        subprocess.run(cmd, check=True, timeout=8)
        if os.path.exists(audio_filepath):
            return {"audio_url": f"/assets/audio/{audio_filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    raise HTTPException(status_code=500, detail="Synthesis failed")

@app.get("/api/tutor/events/{session_id}")
async def sse_dialogue_events(session_id: str, request: Request):
    """Server-Sent Events (SSE) stream for real-time speech and state event updates."""
    queue = asyncio.Queue()
    active_sse_queues[session_id] = queue

    async def event_generator():
        try:
            yield f"data: {{\"event\": \"connected\", \"session_id\": \"{session_id}\"}}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event_data = await asyncio.wait_for(queue.get(), timeout=20.0)
                    import json
                    yield f"data: {json.dumps(event_data)}\n\n"
                except asyncio.TimeoutError:
                    yield f": ping\n\n"
        finally:
            active_sse_queues.pop(session_id, None)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Mount Static Files
static_dir = os.path.dirname(os.path.abspath(__file__))
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3033)
