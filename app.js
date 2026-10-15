/**
 * Genshin Impact AI Tutor WebUI Engine
 * State Management, AudioContext Viseme Lip-Sync, Canvas Particle & Waveform Visualizers
 */

// --- Character Persona Registry ---
const CHARACTERS = {
  barbara: {
    name: 'Barbara Page',
    title: 'Deaconess of the Church of Favonius • Mondstadt Idol',
    element: 'Hydro',
    color: '#4fc3f7',
    glow: 'rgba(79, 195, 247, 0.5)',
    avatar: 'assets/models/barbara.fbx',
    defaultLine: "Ready for some practice? Let's take it step by step, and remember: Barbara will always be cheering for you! ♪",
    hints: [
      'Listen closely to the melody of nature! Like notes in a harmony, elements respond to each other.',
      'Hydro washes away impurities and spreads gentle ripples. When combined with other elements, wonderous reactions take place!',
      'Vaporize, Electro-Charged, and Bloom all create harmonious resonances. Try matching the right catalyst!',
      'Solution: Hydro cleanses and creates elemental reactions like Electro-Charged and Bloom.'
    ],
    praise: 'Yay! You did it! That was an amazing answer—music to my ears! ♪'
  },
  raiden: {
    name: 'Raiden Shogun',
    title: 'Plane of Euthymia • Electro Archon',
    element: 'Electro',
    color: '#a259ff',
    glow: 'rgba(162, 89, 255, 0.5)',
    avatar: 'assets/raiden.jpg',
    defaultLine: 'Inactivity serves no purpose. Show me the fruits of your discipline.',
    hints: [
      'Focus your intention. An elemental reaction requires two opposing charges.',
      'Consider the reaction between Electro and Hydro. What state of electrification occurs?',
      'Electro-Charged deals continuous electro damage over time and jumps to nearby wet targets.',
      'Solution: Electro + Hydro = Electro-Charged (Continuous AoE DoT).'
    ],
    praise: 'Decisive and resolute. Your comprehension has reached a higher tier of mastery.'
  },
  furina: {
    name: 'Furina de Fontaine',
    title: 'Regina of All Waters • Theatrical Virtuoso',
    element: 'Hydro',
    color: '#4fc3f7',
    glow: 'rgba(79, 195, 247, 0.5)',
    avatar: 'assets/furina.jpg',
    defaultLine: 'Splendid! The stage is set, the spotlight is warm—let our dialogue begin!',
    hints: [
      'Every grand drama has a protagonist and an antagonist! Who sets the stage first?',
      'Hydro soothes and cleanses, while Pyro burns with fierce passion. What dramatic climax ensues?',
      'Vaporize amplifies damage based on which element triggers the reaction!',
      'Solution: Hydro triggered by Pyro grants a 2x Vaporize multiplier!'
    ],
    praise: 'Bravo! A performance worthy of Fontaine’s grand opera house! Encore!'
  },
  zhongli: {
    name: 'Zhongli (Morax)',
    title: 'Vago Mundo • Geo Archon',
    element: 'Geo',
    color: '#e5b042',
    glow: 'rgba(229, 176, 66, 0.5)',
    avatar: 'assets/zhongli.jpg',
    defaultLine: 'To rush through the foundations is to build a pavilion on shifting sand. Let us inspect the bedrock.',
    hints: [
      'Gold and stone endure through time. What foundational rule governs this equilibrium?',
      'Observe the crystal structure. When Geo meets other elements, it crystallizes into defensive shields.',
      'Crystallize generates shards that confer elemental shields to withstand external perturbations.',
      'Solution: Geo + [Pyro/Hydro/Cryo/Electro] = Crystallize Shield Shard.'
    ],
    praise: 'Solid as bedrock. A contract fulfilled with impeccable precision.'
  },
  nahida: {
    name: 'Nahida',
    title: 'Lesser Lord Kusanali • Dendro Archon',
    element: 'Dendro',
    color: '#5cb85c',
    glow: 'rgba(92, 184, 92, 0.5)',
    avatar: 'assets/nahida.jpg',
    defaultLine: 'Curiosity is the seed of all wisdom! Let’s water it together with new questions.',
    hints: [
      'Seeds need moisture to sprout. What happens when Dendro meets Hydro?',
      'A Dendro core blooms upon contact! But wait—can that core react with another element?',
      'Burgeon occurs when Pyro ignites the core; Hyperbloom occurs when Electro energizes it.',
      'Solution: Dendro + Hydro = Bloom Core. Add Electro for homing Hyperbloom!'
    ],
    praise: 'Wonderful! You just nurtured another knowledge blossom into full fruit!'
  },
  ganyu: {
    name: 'Ganyu',
    title: 'Plenilune Gaze • General Secretary',
    element: 'Cryo',
    color: '#99ffff',
    glow: 'rgba(153, 255, 255, 0.5)',
    avatar: 'assets/ganyu.jpg',
    defaultLine: 'Overtime or revision, every step logged brings us closer to flawless execution.',
    hints: [
      'Precision is key. Double check your initial assumptions and timing.',
      'Cryo lowers temperature, freezing moisture in place.',
      'Hydro + Cryo immobilizes targets completely in the Frozen state.',
      'Solution: Hydro + Cryo = Frozen (Complete CC status).'
    ],
    praise: 'Log complete. Your accuracy percentage is 100%. Meticulous work as always!'
  },
  keqing: {
    name: 'Keqing',
    title: 'Yuheng of the Liyue Qixing • Speed Specialist',
    element: 'Electro',
    color: '#a855f7',
    glow: 'rgba(168, 85, 247, 0.5)',
    avatar: 'assets/keqing.jpg',
    defaultLine: 'Don’t delay today’s work until tomorrow! Speed, clarity, and decisive execution!',
    hints: [
      'Time is running! Eliminate redundant hypotheses immediately.',
      'Look at the kinetic velocity and elemental resonance.',
      'Superconduct shreds physical resistance by 40% for 12 seconds.',
      'Solution: Cryo + Electro = Superconduct (-40% Physical RES).'
    ],
    praise: 'Flawless execution! Under time limit and perfectly accurate!'
  }
};

// --- Application State Store ---
const AppState = {
  characterState: 'idle', // 'idle' | 'listening' | 'thinking' | 'speaking' | 'celebrating'
  activeCharacterKey: 'furina',
  primogems: 1600,
  unlockedHintIndex: 0,
  isRecording: false,
  audioContext: null,
  analyser: null,
  audioDataArray: null,
  visemeInterval: null,
  mouthScale: 0.1,
  targetMouthScale: 0.1,
  particles: []
};

// --- Web Audio & Viseme Rigging Engine ---
function initAudioEngine() {
  if (AppState.audioContext) return;
  try {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    AppState.audioContext = new AudioContextClass();
    AppState.analyser = AppState.audioContext.createAnalyser();
    AppState.analyser.fftSize = 256;
    AppState.analyser.smoothingTimeConstant = 0.8;
    AppState.audioDataArray = new Uint8Array(AppState.analyser.frequencyBinCount);
  } catch (err) {
    console.warn('Web Audio API not supported or blocked:', err);
  }
}

// Set Avatar State and Trigger Visual / Rig Reactions
function setCharacterState(newState) {
  const prev = AppState.characterState;
  AppState.characterState = newState;

  const stage = document.getElementById('avatar-stage');
  if (stage) {
    stage.className = `avatar-stage-container state-${newState}`;
  }

  // Update State Badge
  const stateLabel = document.getElementById('current-state-label');
  if (stateLabel) {
    stateLabel.textContent = newState.toUpperCase();
  }

  // Update State Radio buttons in dashboard
  const radio = document.querySelector(`input[name="state-override"][value="${newState}"]`);
  if (radio) radio.checked = true;

  // Update 3D WebGL Engine if active
  if (window.barbara3D) {
    window.barbara3D.setState(newState);
  }
  if (window.raiden3D) {
    window.raiden3D.setState(newState);
  }

  // State-specific hooks
  if (newState === 'celebrating') {
    triggerCelebrationParticles();
  } else if (newState === 'speaking') {
    startVisemeLoop();
  } else {
    stopVisemeLoop();
  }
}

// Viseme Mouth Scale Animator (Smooth 60fps interpolation based on 15fps audio sampling)
let visemeAnimId = null;
function startVisemeLoop() {
  if (visemeAnimId) return;

  function renderVisemeFrame() {
    if (AppState.characterState === 'speaking') {
      // Sample audio amplitude if analyzer is running
      if (AppState.analyser && AppState.audioDataArray) {
        AppState.analyser.getByteFrequencyData(AppState.audioDataArray);
        let sum = 0;
        // Focus on mid vocal frequencies (bins 4 to 32)
        const sampleCount = 28;
        for (let i = 4; i < 32; i++) {
          sum += AppState.audioDataArray[i] || 0;
        }
        const avg = sum / sampleCount;
        // Normalize 0..255 to 0.1..1.0
        AppState.targetMouthScale = Math.min(1.0, Math.max(0.12, (avg / 110)));
      } else {
        // Fallback procedural oscillation
        const t = performance.now() / 90;
        AppState.targetMouthScale = 0.2 + (Math.sin(t) * 0.4 + Math.cos(t * 1.7) * 0.3 + 0.35);
      }

      // Feed amplitude to 3D Barbara & Raiden models
      if (window.barbara3D) {
        window.barbara3D.setAudioVolume(AppState.targetMouthScale);
      }
      if (window.raiden3D) {
        window.raiden3D.setAudioAmplitude(AppState.targetMouthScale);
      }

      // Smooth interpolation (lerp)
      AppState.mouthScale += (AppState.targetMouthScale - AppState.mouthScale) * 0.35;
      
      const mouthSvg = document.getElementById('viseme-mouth');
      if (mouthSvg) {
        mouthSvg.style.transform = `scaleY(${AppState.mouthScale.toFixed(2)})`;
      }

      visemeAnimId = requestAnimationFrame(renderVisemeFrame);
    } else {
      // Revert mouth smoothly
      AppState.mouthScale += (0.1 - AppState.mouthScale) * 0.4;
      if (window.barbara3D) {
        window.barbara3D.setAudioVolume(0);
      }
      if (window.raiden3D) {
        window.raiden3D.setAudioAmplitude(0);
      }
      const mouthSvg = document.getElementById('viseme-mouth');
      if (mouthSvg) {
        mouthSvg.style.transform = `scaleY(${AppState.mouthScale.toFixed(2)})`;
      }
      visemeAnimId = null;
    }
  }
  visemeAnimId = requestAnimationFrame(renderVisemeFrame);
}

function stopVisemeLoop() {
  if (visemeAnimId) {
    cancelAnimationFrame(visemeAnimId);
    visemeAnimId = null;
  }
  if (window.barbara3D) {
    window.barbara3D.setAudioVolume(0);
  }
  if (window.raiden3D) {
    window.raiden3D.setAudioVolume(0);
  }
  const mouthSvg = document.getElementById('viseme-mouth');
  if (mouthSvg) {
    mouthSvg.style.transform = 'scaleY(0.12)';
  }
}


// Procedural / TTS Voice Synthesis with Web Audio Hook
function playTutorSpeech(text, callback) {
  initAudioEngine();
  setCharacterState('speaking');

  // Add chat bubble to transcript
  addTranscriptMessage(text, 'tutor');

  if (window.audioPlayer) {
    const prevEnd = window.audioPlayer.onEnd;
    window.audioPlayer.onEnd = () => {
      if (prevEnd) prevEnd();
      setCharacterState('idle');
      if (callback) callback();
    };
    window.audioPlayer.speakText(text);
    return;
  }

  // Check if speech synthesis is available
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = AppState.activeCharacterKey === 'nahida' ? 1.3 : (AppState.activeCharacterKey === 'zhongli' ? 0.75 : 1.05);

    // Also route through procedural oscillator if audioContext is open to drive frequency visualizer
    playProceduralVoiceAudio(utterance.text.length * 55);

    utterance.onend = () => {
      setCharacterState('idle');
      if (callback) callback();
    };
    utterance.onerror = () => {
      setCharacterState('idle');
      if (callback) callback();
    };
    window.speechSynthesis.speak(utterance);
  } else {
    // Fallback procedural sound
    const duration = Math.min(5000, Math.max(1800, text.length * 60));
    playProceduralVoiceAudio(duration);
    setTimeout(() => {
      setCharacterState('idle');
      if (callback) callback();
    }, duration);
  }
}

// Procedural audio oscillator feeding AnalyserNode
function playProceduralVoiceAudio(durationMs) {
  if (!AppState.audioContext) return;
  if (AppState.audioContext.state === 'suspended') {
    AppState.audioContext.resume();
  }

  const osc = AppState.audioContext.createOscillator();
  const gain = AppState.audioContext.createGain();

  const baseFreq = AppState.activeCharacterKey === 'zhongli' ? 120 : (AppState.activeCharacterKey === 'nahida' ? 380 : 220);
  osc.type = 'triangle';
  osc.frequency.setValueAtTime(baseFreq, AppState.audioContext.currentTime);

  // Subtle vibrato/mod
  gain.gain.setValueAtTime(0.08, AppState.audioContext.currentTime);
  gain.gain.linearRampToValueAtTime(0.01, AppState.audioContext.currentTime + (durationMs / 1000));

  osc.connect(gain);
  gain.connect(AppState.analyser);
  gain.connect(AppState.audioContext.destination);

  osc.start();
  osc.stop(AppState.audioContext.currentTime + (durationMs / 1000));
}

// --- Speech Waveform Canvas Visualizer ---
function initSpeechVisualizer() {
  const canvas = document.getElementById('waveform-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  function resizeCanvas() {
    canvas.width = canvas.parentElement.clientWidth * window.devicePixelRatio;
    canvas.height = canvas.parentElement.clientHeight * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
  }
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);

  let phase = 0;
  function drawWaveform() {
    const width = canvas.width / window.devicePixelRatio;
    const height = canvas.height / window.devicePixelRatio;

    ctx.clearRect(0, 0, width, height);

    const activeChar = CHARACTERS[AppState.activeCharacterKey];
    const isSpeakingOrListening = AppState.characterState === 'speaking' || AppState.characterState === 'listening';
    
    // Wave parameters
    const amplitude = isSpeakingOrListening ? 22 : 6;
    phase += isSpeakingOrListening ? 0.08 : 0.025;

    // Draw multi-layered glowing sine waves
    const waves = [
      { color: activeChar.color, alpha: 0.85, width: 2.5, speed: 1.0, freq: 0.02 },
      { color: '#ffffff', alpha: 0.5, width: 1.5, speed: 1.3, freq: 0.035 },
      { color: activeChar.color, alpha: 0.35, width: 4.0, speed: 0.7, freq: 0.015 }
    ];

    waves.forEach(w => {
      ctx.beginPath();
      ctx.lineWidth = w.width;
      ctx.strokeStyle = w.color;
      ctx.globalAlpha = w.alpha;

      for (let x = 0; x < width; x++) {
        // Window function (taper at both ends)
        const envelope = Math.sin((x / width) * Math.PI);
        const y = (height / 2) + Math.sin(x * w.freq + phase * w.speed) * amplitude * envelope;
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    });

    ctx.globalAlpha = 1.0;
    requestAnimationFrame(drawWaveform);
  }
  requestAnimationFrame(drawWaveform);
}

// --- Celebration Star / Primogem Particle Burst System ---
function initCelebrationCanvas() {
  const canvas = document.getElementById('celebration-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  function resize() {
    canvas.width = canvas.parentElement.clientWidth * window.devicePixelRatio;
    canvas.height = canvas.parentElement.clientHeight * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
  }
  resize();
  window.addEventListener('resize', resize);

  function renderParticles() {
    const width = canvas.width / window.devicePixelRatio;
    const height = canvas.height / window.devicePixelRatio;
    ctx.clearRect(0, 0, width, height);

    for (let i = AppState.particles.length - 1; i >= 0; i--) {
      const p = AppState.particles[i];
      p.x += p.vx;
      p.y += p.vy;
      p.vy += p.gravity;
      p.life -= p.decay;
      p.rotation += p.vRot;

      if (p.life <= 0) {
        AppState.particles.splice(i, 1);
        continue;
      }

      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(p.rotation);
      ctx.globalAlpha = p.life;
      ctx.fillStyle = p.color;

      // Draw diamond / 4-point Genshin star
      ctx.beginPath();
      const s = p.size;
      ctx.moveTo(0, -s * 1.5);
      ctx.lineTo(s * 0.4, -s * 0.4);
      ctx.lineTo(s * 1.5, 0);
      ctx.lineTo(s * 0.4, s * 0.4);
      ctx.lineTo(0, s * 1.5);
      ctx.lineTo(-s * 0.4, s * 0.4);
      ctx.lineTo(-s * 1.5, 0);
      ctx.lineTo(-s * 0.4, -s * 0.4);
      ctx.closePath();
      ctx.fill();

      ctx.restore();
    }

    requestAnimationFrame(renderParticles);
  }
  requestAnimationFrame(renderParticles);
}

function triggerCelebrationParticles() {
  const canvas = document.getElementById('celebration-canvas');
  if (!canvas) return;
  const width = canvas.width / window.devicePixelRatio;
  const height = canvas.height / window.devicePixelRatio;

  const colors = ['#f59e0b', '#fae4b5', '#a259ff', '#4fc3f7', '#ffffff', '#22c55e'];
  
  // Burst from avatar center
  const originX = width / 2;
  const originY = height / 2;

  for (let i = 0; i < 45; i++) {
    const angle = Math.random() * Math.PI * 2;
    const speed = 3 + Math.random() * 8;
    AppState.particles.push({
      x: originX,
      y: originY,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed - 2.5,
      gravity: 0.18,
      size: 4 + Math.random() * 6,
      color: colors[Math.floor(Math.random() * colors.length)],
      life: 1.0,
      decay: 0.015 + Math.random() * 0.02,
      rotation: Math.random() * Math.PI,
      vRot: (Math.random() - 0.5) * 0.2
    });
  }
}

// --- Chat Transcript Logger ---
function addTranscriptMessage(text, sender = 'tutor') {
  const container = document.getElementById('chat-transcript');
  if (!container) return;

  const activeChar = CHARACTERS[AppState.activeCharacterKey];
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${sender}`;

  const nameHeader = document.createElement('div');
  nameHeader.className = 'text-[11px] font-semibold mb-1 opacity-75';
  nameHeader.textContent = sender === 'tutor' ? activeChar.name : 'Traveler';
  nameHeader.style.color = sender === 'tutor' ? activeChar.color : '#7dd3fc';

  const body = document.createElement('div');
  body.textContent = text;

  bubble.appendChild(nameHeader);
  bubble.appendChild(body);
  container.appendChild(bubble);

  container.scrollTop = container.scrollHeight;
}

// --- Voice Recognition & Conversation Simulator ---
function toggleSpeechInput() {
  initAudioEngine();
  const micBtn = document.getElementById('mic-toggle-btn');
  const micStatus = document.getElementById('mic-status-text');

  if (AppState.isRecording) {
    // Stop recording
    AppState.isRecording = false;
    micBtn.classList.remove('bg-red-500/30', 'border-red-400');
    micBtn.classList.add('genshin-btn-outline');
    micStatus.textContent = 'Click mic to speak';
    
    // Switch to Thinking
    setCharacterState('thinking');

    // Simulate query processing
    setTimeout(() => {
      const activeChar = CHARACTERS[AppState.activeCharacterKey];
      const replies = [
        `Regarding your query on elemental reactions: ${activeChar.hints[1]}`,
        `Analyzing that rotation... remember that ${activeChar.name} prioritizes energy recharge and cadence.`,
        `An astute observation, Traveler! Let me explain the deeper resonance.`
      ];
      const reply = replies[Math.floor(Math.random() * replies.length)];
      playTutorSpeech(reply);
    }, 1400);

  } else {
    // Start recording
    AppState.isRecording = true;
    micBtn.classList.add('bg-red-500/30', 'border-red-400');
    micBtn.classList.remove('genshin-btn-outline');
    micStatus.textContent = 'Listening to speech... (Click to send)';
    setCharacterState('listening');

    // Add user question to transcript after brief delay
    setTimeout(() => {
      if (AppState.isRecording) {
        const sampleQueries = [
          'Can you explain how the Vaporize damage multiplier is calculated?',
          'What is the optimal artifact build for high elemental mastery?',
          'How does the Socratic hint structure help me master this problem?'
        ];
        const query = sampleQueries[Math.floor(Math.random() * sampleQueries.length)];
        addTranscriptMessage(query, 'user');
      }
    }, 1500);
  }
}

// --- Socratic Hint Accordion Controller ---
function unlockNextHint() {
  const activeChar = CHARACTERS[AppState.activeCharacterKey];
  if (AppState.unlockedHintIndex < activeChar.hints.length - 1) {
    AppState.unlockedHintIndex++;
    renderHints();
    setCharacterState('thinking');
    setTimeout(() => {
      playTutorSpeech(`Hint #${AppState.unlockedHintIndex + 1}: ${activeChar.hints[AppState.unlockedHintIndex]}`);
    }, 600);
  }
}

function renderHints() {
  const container = document.getElementById('hint-accordion-list');
  if (!container) return;
  container.innerHTML = '';

  const activeChar = CHARACTERS[AppState.activeCharacterKey];
  activeChar.hints.forEach((hintText, index) => {
    const isUnlocked = index <= AppState.unlockedHintIndex;
    const item = document.createElement('div');
    item.className = `hint-accordion-item ${isUnlocked ? 'active' : 'opacity-50'}`;

    const header = document.createElement('div');
    header.className = 'hint-accordion-header';
    header.innerHTML = `
      <span class="flex items-center gap-2">
        <span class="text-xs px-2 py-0.5 rounded ${isUnlocked ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-gray-800 text-gray-400'}">
          ${index === 3 ? 'SOLUTION' : `HINT ${index + 1}`}
        </span>
        <span>${index === 3 ? 'Full Socratic Resolution' : `Guiding Principle ${index + 1}`}</span>
      </span>
      <span>${isUnlocked ? '▼' : '🔒'}</span>
    `;

    const body = document.createElement('div');
    body.className = 'hint-accordion-body';
    body.textContent = isUnlocked ? hintText : 'Locked. Complete prerequisite thinking or request the next hint step.';

    header.addEventListener('click', () => {
      if (isUnlocked) {
        item.classList.toggle('active');
      }
    });

    item.appendChild(header);
    item.appendChild(body);
    container.appendChild(item);
  });
}

// --- Adaptive Practice Quiz Engine ---
function checkQuizAnswer(selectedOption, isCorrect) {
  const activeChar = CHARACTERS[AppState.activeCharacterKey];
  const feedbackEl = document.getElementById('quiz-feedback');
  const primogemEl = document.getElementById('primogem-val');

  // Clear previous styling
  document.querySelectorAll('.quiz-option').forEach(el => {
    el.classList.remove('correct', 'incorrect', 'selected');
  });

  selectedOption.classList.add(isCorrect ? 'correct' : 'incorrect');

  if (isCorrect) {
    // Reward primogems
    AppState.primogems += 60;
    if (primogemEl) primogemEl.textContent = AppState.primogems;

    feedbackEl.className = 'mt-3 p-3 rounded-lg border border-emerald-500/40 bg-emerald-950/40 text-emerald-200 text-xs flex items-center justify-between';
    feedbackEl.innerHTML = `
      <div>
        <strong class="font-bold">Correct Answer!</strong> ${activeChar.praise}
      </div>
      <span class="text-amber-400 font-bold">+60 ✦</span>
    `;

    // Transition to celebrating
    setCharacterState('celebrating');
    playTutorSpeech(activeChar.praise, () => {
      // Revert to idle after celebration
      setTimeout(() => {
        if (AppState.characterState === 'celebrating') {
          setCharacterState('idle');
        }
      }, 2500);
    });

  } else {
    feedbackEl.className = 'mt-3 p-3 rounded-lg border border-rose-500/40 bg-rose-950/40 text-rose-200 text-xs';
    feedbackEl.innerHTML = `
      <strong class="font-bold">Not quite.</strong> Let’s review the foundational principles. Try opening the next hint step!
    `;
    setCharacterState('thinking');
    setTimeout(() => {
      playTutorSpeech('Examine the premises once more. Do not be discouraged; every mistake reveals the path forward.');
    }, 400);
  }
}

// --- Character Persona Switcher ---
function selectCharacter(charKey) {
  if (!CHARACTERS[charKey]) return;
  AppState.activeCharacterKey = charKey;
  const c = CHARACTERS[charKey];

  // Update CSS Variables
  document.documentElement.style.setProperty('--active-accent', c.color);
  document.documentElement.style.setProperty('--active-accent-glow', c.glow);

  // Update Avatar Image
  const avatarImg = document.getElementById('main-avatar-img');
  if (avatarImg) {
    avatarImg.src = c.avatar;
    avatarImg.alt = c.name;
  }

  // Update Avatar Header Info
  const nameEl = document.getElementById('active-tutor-name');
  const titleEl = document.getElementById('active-tutor-title');
  const elementBadge = document.getElementById('active-element-badge');
  if (nameEl) nameEl.textContent = c.name;
  if (titleEl) titleEl.textContent = c.title;
  if (elementBadge) {
    elementBadge.textContent = c.element.toUpperCase();
    elementBadge.style.borderColor = c.color;
    elementBadge.style.color = c.color;
  }

  // Update Character selector pill active highlights
  document.querySelectorAll('.char-select-btn').forEach(btn => {
    if (btn.dataset.char === charKey) {
      btn.classList.add('border-amber-400', 'bg-amber-500/20');
    } else {
      btn.classList.remove('border-amber-400', 'bg-amber-500/20');
    }
  });

  // Re-render hints
  AppState.unlockedHintIndex = 0;
  renderHints();

  // Play introductory greeting
  playTutorSpeech(c.defaultLine);
}

// --- Initialization on Window Load ---
window.addEventListener('DOMContentLoaded', () => {
  initCelebrationCanvas();

  // If modern modular controller is active, let it control quiz, hints, prompts, and character switching
  if (window.dialogueController || window.universalTutor3D || document.querySelector('script[type="module"]')) {
    console.log('[app.js] Modular architecture active; legacy fallback event handlers bypassed.');
    return;
  }

  initSpeechVisualizer();
  renderHints();

  // Wire State Override Buttons in Test Dashboard
  document.querySelectorAll('input[name="state-override"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      setCharacterState(e.target.value);
    });
  });

  // Character Switcher Buttons
  document.querySelectorAll('.char-select-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      selectCharacter(btn.dataset.char);
    });
  });

  // Mic Toggle Button
  const micBtn = document.getElementById('mic-toggle-btn');
  if (micBtn) {
    micBtn.addEventListener('click', toggleSpeechInput);
  }

  // Quick Preset Prompt Buttons (fallback if modular dialogue controller not active)
  document.querySelectorAll('.preset-prompt-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const prompt = btn.textContent.trim();
      addTranscriptMessage(prompt, 'user');
      setCharacterState('thinking');
      setTimeout(() => {
        const c = CHARACTERS[AppState.activeCharacterKey];
        playTutorSpeech(`Regarding "${prompt}": ${c.hints[0]}`);
      }, 1000);
    });
  });

  // Unlock Hint Button
  const hintBtn = document.getElementById('request-hint-btn');
  if (hintBtn) {
    hintBtn.addEventListener('click', unlockNextHint);
  }

  // Quiz Options
  document.querySelectorAll('.quiz-option').forEach(option => {
    option.addEventListener('click', () => {
      const isCorrect = option.dataset.correct === 'true';
      checkQuizAnswer(option, isCorrect);
    });
  });

  // Reset Quiz Button
  const resetQuizBtn = document.getElementById('reset-quiz-btn');
  if (resetQuizBtn) {
    resetQuizBtn.addEventListener('click', () => {
      document.querySelectorAll('.quiz-option').forEach(el => {
        el.classList.remove('correct', 'incorrect', 'selected');
      });
      const feedbackEl = document.getElementById('quiz-feedback');
      if (feedbackEl) {
        feedbackEl.className = 'hidden';
        feedbackEl.innerHTML = '';
      }
      AppState.unlockedHintIndex = 0;
      renderHints();
      setCharacterState('idle');
    });
  }
});

  // Audio Context unlock on initial user interaction
  document.body.addEventListener('click', () => {
    initAudioEngine();
  }, { once: true });
});
