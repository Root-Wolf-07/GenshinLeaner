/**
 * Genshin Cognitive Academy • Tutor Dialogue Controller
 * Manages dialogue session lifecycle, backend API requests, SSE events,
 * typed event contracts, stale event rejection, and audio/animation synchronization.
 */

export class TutorDialogueController {
  constructor(options = {}) {
    this.apiBaseUrl = options.apiBaseUrl || window.location.origin;
    this.sessionId = options.sessionId || `session_${Math.random().toString(36).substring(2, 10)}`;
    this.currentMessageId = null;
    this.isProcessing = false;

    // Controllers
    this.audioPlayer = options.audioPlayer;
    this.animationController = options.animationController;
    this.lipSyncController = options.lipSyncController;

    // Subscribed Event Listeners
    this.listeners = new Map();

    this.initAudioHooks();
    this.connectSSE();
  }

  initAudioHooks() {
    if (!this.audioPlayer) return;

    this.audioPlayer.onStart = () => {
      this.emit('speech_started', {
        session_id: this.sessionId,
        message_id: this.currentMessageId
      });
      if (this.lipSyncController) {
        this.lipSyncController.startSpeech();
      }
    };

    this.audioPlayer.onAmplitude = (volume) => {
      if (this.lipSyncController) {
        this.lipSyncController.setAudioVolume(volume);
      }
      if (this.animationController) {
        this.animationController.setAudioVolume(volume);
      }
      this.emit('amplitude_update', { volume });
    };

    this.audioPlayer.onEnd = () => {
      this.emit('speech_completed', {
        session_id: this.sessionId,
        message_id: this.currentMessageId
      });
      if (this.lipSyncController) {
        this.lipSyncController.stopSpeech();
      }
      if (this.animationController) {
        this.animationController.setState('idle');
      }
      this.isProcessing = false;
    };

    this.audioPlayer.onPause = () => {
      this.emit('speech_paused', { session_id: this.sessionId });
      if (this.lipSyncController) this.lipSyncController.stopSpeech();
      if (this.animationController) this.animationController.setState('idle');
    };

    this.audioPlayer.onResume = () => {
      this.emit('speech_resumed', { session_id: this.sessionId });
      if (this.lipSyncController) this.lipSyncController.startSpeech();
      if (this.animationController) this.animationController.setState('speaking');
    };
  }

  connectSSE() {
    try {
      const sseUrl = `${this.apiBaseUrl}/api/tutor/events/${this.sessionId}`;
      const eventSource = new EventSource(sseUrl);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          // Reject stale messages from previous turns
          if (data.message_id && this.currentMessageId && data.message_id !== this.currentMessageId) {
            console.log('Rejecting stale SSE event:', data);
            return;
          }
          this.handleBackendEvent(data);
        } catch (err) {
          // Keep-alive or non-JSON comments
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
      };
    } catch (e) {
      console.warn('SSE not supported or unavailable, using direct HTTP response flow');
    }
  }

  on(eventName, callback) {
    if (!this.listeners.has(eventName)) {
      this.listeners.set(eventName, []);
    }
    this.listeners.get(eventName).push(callback);
  }

  emit(eventName, payload) {
    const handlers = this.listeners.get(eventName) || [];
    handlers.forEach(fn => fn(payload));
  }

  setSubjectAndTutor(subject, tutorId) {
    this.activeSubject = subject;
    this.activeTutorId = tutorId;
  }

  async sendStudentMessage(text, options = {}) {
    if (!text || !text.trim()) return;

    const subject = options.subject || this.activeSubject || 'Dance, Communication & Music';
    const tutorId = options.tutorId || this.activeTutorId || 'furina';

    // Synchronously unlock AudioContext within the user gesture event loop before any async await
    if (this.audioPlayer) {
      this.audioPlayer.unlockContext();
    }

    // Interrupt previous response cleanly
    if (this.audioPlayer && this.audioPlayer.isPlaying) {
      this.audioPlayer.stop();
      this.emit('speech_cancelled', { session_id: this.sessionId });
    }

    const messageId = `msg_${Date.now()}`;
    this.currentMessageId = messageId;
    this.isProcessing = true;

    // 1. Emit user_message_received
    this.emit('user_message_received', {
      session_id: this.sessionId,
      message_id: messageId,
      text: text,
      subject: subject,
      tutor_id: tutorId
    });

    // 2. Set tutor to 'thinking' state
    if (this.animationController) {
      this.animationController.setState('thinking');
    }
    this.emit('tutor_thinking', { session_id: this.sessionId, message_id: messageId });

    try {
      // 3. Request backend dialogue response
      const apiKey = options.apiKey || localStorage.getItem('ai_tutor_api_key') || null;
      const response = await fetch(`${this.apiBaseUrl}/api/tutor/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: this.sessionId,
          message: text,
          subject: subject,
          tutor_id: tutorId,
          api_key: apiKey
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const data = await response.json();

      // Check for stale response
      if (this.currentMessageId !== messageId) {
        console.warn('Stale HTTP dialogue response ignored');
        return;
      }

      // 4. Emit tutor_response_ready
      this.emit('tutor_response_ready', data);

      // 5. Update animation state & schedule speech segments
      const targetState = data.state || 'speaking';
      if (this.animationController) {
        this.animationController.setState(targetState);
      }

      // 6. Play speech audio through single controlled pipeline
      if (this.audioPlayer) {
        this.audioPlayer.speakText(data.text, {
          audioUrl: data.audio_url
        });
      }

      // 7. Schedule viseme / segment events if provided
      if (data.segments && data.segments.length > 0) {
        this.scheduleSegments(data.segments, messageId);
      }

    } catch (err) {
      console.error('Dialogue error:', err);
      if (this.currentMessageId === messageId) {
        if (this.animationController) {
          this.animationController.setState('error');
        }
        this.emit('tutor_error', {
          session_id: this.sessionId,
          message_id: messageId,
          error: err.message
        });
        this.isProcessing = false;
        setTimeout(() => {
          if (this.animationController && this.animationController.getState() === 'error') {
            this.animationController.setState('idle');
          }
        }, 3000);
      }
    }
  }

  scheduleSegments(segments, messageId) {
    segments.forEach((seg) => {
      // Schedule segment state transitions
      setTimeout(() => {
        if (this.currentMessageId !== messageId || !this.audioPlayer.isPlaying) return;
        if (this.animationController && seg.state) {
          this.animationController.setState(seg.state);
        }
        this.emit('speech_segment', { ...seg, message_id: messageId });
      }, seg.start_ms);

      // Schedule individual viseme events
      if (seg.visemes) {
        seg.visemes.forEach((v) => {
          setTimeout(() => {
            if (this.currentMessageId !== messageId || !this.audioPlayer.isPlaying) return;
            if (this.lipSyncController) {
              this.lipSyncController.setViseme(v.viseme, v.intensity);
            }
          }, seg.start_ms + v.time_ms);
        });
      }
    });
  }

  handleBackendEvent(data) {
    if (data.event === 'tutor_thinking') {
      if (this.animationController) this.animationController.setState('thinking');
    }
    this.emit(data.event, data);
  }
}
