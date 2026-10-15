/**
 * Genshin Cognitive Academy • Tutor Conversation Panel
 * Renders conversation messages, thinking indicators, speech waveform visualizer,
 * and handles user input submission through TutorDialogueController.
 */

export class TutorConversationPanel {
  constructor(options = {}) {
    this.transcriptContainer = typeof options.transcriptContainer === 'string'
      ? document.getElementById(options.transcriptContainer)
      : options.transcriptContainer;
    this.canvasVisualizer = typeof options.canvasVisualizer === 'string'
      ? document.getElementById(options.canvasVisualizer)
      : options.canvasVisualizer;
    this.micBtn = typeof options.micBtn === 'string'
      ? document.getElementById(options.micBtn)
      : options.micBtn;
    this.dialogueController = options.dialogueController;

    this.isRecording = false;
    this.initVisualizer();
    this.initEvents();
  }

  initEvents() {
    if (!this.dialogueController) return;

    this.dialogueController.on('user_message_received', (data) => {
      this.appendMessage('student', data.text);
      this.showThinkingIndicator(data.tutor_id);
    });

    this.dialogueController.on('tutor_response_ready', (data) => {
      this.hideThinkingIndicator();
      this.appendMessage('tutor', data.text, {
        name: data.tutor_name || 'Virtual Tutor',
        color: data.accent_color || '#38bdf8'
      });
    });

    this.dialogueController.on('tutor_error', (data) => {
      this.hideThinkingIndicator();
      this.appendErrorMessage(data.error);
    });
  }

  appendMessage(sender, text, meta = {}) {
    if (!this.transcriptContainer) return;

    const bubble = document.createElement('div');
    const isTutor = (sender !== 'student' && sender !== 'user');
    bubble.className = `chat-bubble ${isTutor ? 'tutor' : 'user'}`;

    const header = document.createElement('div');
    header.className = 'text-[11px] font-semibold mb-1 opacity-90';
    if (isTutor) {
      header.textContent = `${meta.name || 'Virtual Tutor'} ✦`;
      header.style.color = meta.color || '#38bdf8';
    } else {
      header.textContent = 'Traveler';
      header.style.color = '#7dd3fc';
    }

    const body = document.createElement('div');
    body.textContent = text;

    bubble.appendChild(header);
    bubble.appendChild(body);
    this.transcriptContainer.appendChild(bubble);
    this.transcriptContainer.scrollTop = this.transcriptContainer.scrollHeight;
  }

  showThinkingIndicator(tutorId) {
    this.hideThinkingIndicator();
    if (!this.transcriptContainer) return;

    const indicator = document.createElement('div');
    indicator.id = 'thinking-indicator-bubble';
    indicator.className = 'chat-bubble tutor flex items-center gap-2 py-2';
    indicator.innerHTML = `
      <span class="text-xs text-amber-300 font-semibold font-genshin">Tutor is contemplating Socratic guidance...</span>
      <div class="flex items-center gap-1">
        <span class="w-1.5 h-1.5 rounded-full bg-amber-400 animate-bounce"></span>
        <span class="w-1.5 h-1.5 rounded-full bg-amber-400 animate-bounce [animation-delay:0.15s]"></span>
        <span class="w-1.5 h-1.5 rounded-full bg-amber-400 animate-bounce [animation-delay:0.3s]"></span>
      </div>
    `;
    this.transcriptContainer.appendChild(indicator);
    this.transcriptContainer.scrollTop = this.transcriptContainer.scrollHeight;
  }

  hideThinkingIndicator() {
    const el = document.getElementById('thinking-indicator-bubble');
    if (el) el.remove();
  }

  appendErrorMessage(errorText) {
    if (!this.transcriptContainer) return;
    const errDiv = document.createElement('div');
    errDiv.className = 'chat-bubble tutor border-red-500/50 bg-red-950/40 text-red-200 text-xs';
    errDiv.innerHTML = `<strong>Notice:</strong> ${errorText || 'Connection error. Please try again.'}`;
    this.transcriptContainer.appendChild(errDiv);
    this.transcriptContainer.scrollTop = this.transcriptContainer.scrollHeight;
  }

  initVisualizer() {
    if (!this.canvasVisualizer) return;
    const ctx = this.canvasVisualizer.getContext('2d');
    let phase = 0;

    const render = () => {
      requestAnimationFrame(render);
      const width = this.canvasVisualizer.width = this.canvasVisualizer.clientWidth;
      const height = this.canvasVisualizer.height = this.canvasVisualizer.clientHeight;

      ctx.clearRect(0, 0, width, height);

      const isSpeaking = this.dialogueController?.audioPlayer?.isPlaying;
      const amplitude = isSpeaking ? 18 : 5;
      phase += isSpeaking ? 0.08 : 0.025;

      // Draw multi-harmonic Hydro cyan waves
      const waves = [
        { color: '#4fc3f7', alpha: 0.85, width: 2.0, freq: 0.025, speed: 1.0 },
        { color: '#ffffff', alpha: 0.5, width: 1.2, freq: 0.04, speed: 1.4 },
        { color: '#38bdf8', alpha: 0.35, width: 3.5, freq: 0.018, speed: 0.8 }
      ];

      waves.forEach(w => {
        ctx.beginPath();
        ctx.lineWidth = w.width;
        ctx.strokeStyle = w.color;
        ctx.globalAlpha = w.alpha;

        for (let x = 0; x < width; x++) {
          const envelope = Math.sin((x / width) * Math.PI);
          const y = (height / 2) + Math.sin(x * w.freq + phase * w.speed) * amplitude * envelope;
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
      });

      ctx.globalAlpha = 1.0;
    };
    render();
  }
}
