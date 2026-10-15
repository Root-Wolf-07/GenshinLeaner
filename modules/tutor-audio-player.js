/**
 * Genshin Cognitive Academy • Tutor Audio Player
 * Single authoritative audio pipeline managing Web Audio API, AnalyserNode,
 * real backend TTS audio buffer streaming, speech synthesis fallback,
 * amplitude analysis for lip-sync, and autoplay unlock.
 */

export class TutorAudioPlayer {
  constructor() {
    this.audioContext = null;
    this.analyser = null;
    this.dataArray = null;
    this.isPlaying = false;
    this.currentSource = null;
    this.currentUtterance = null;
    this.animFrameId = null;
    this.playToken = 0; // Incremented on every new speech request to avoid race conditions

    // Callbacks
    this.onStart = null;
    this.onEnd = null;
    this.onAmplitude = null;
    this.onPause = null;
    this.onResume = null;

    this.initAudioContext();
    this.attachAutoUnlockListeners();
  }

  initAudioContext() {
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass && !this.audioContext) {
        this.audioContext = new AudioContextClass();
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 256;
        this.analyser.smoothingTimeConstant = 0.75;
        this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
      }
    } catch (e) {
      console.warn('Web Audio API not supported in current context:', e);
    }
  }

  attachAutoUnlockListeners() {
    const unlock = () => {
      this.unlockContext();
    };
    window.addEventListener('click', unlock, { passive: true });
    window.addEventListener('touchstart', unlock, { passive: true });
    window.addEventListener('keydown', unlock, { passive: true });
  }

  unlockContext() {
    if (!this.audioContext) {
      this.initAudioContext();
    }
    if (this.audioContext && this.audioContext.state === 'suspended') {
      this.audioContext.resume().catch((e) => console.warn('AudioContext resume deferred:', e));
    }
  }

  /**
   * Main speech playback entry point.
   * Prioritizes high-fidelity server TTS audio URL, with fallback to on-demand TTS or SpeechSynthesis.
   */
  async speakText(text, options = {}) {
    const currentToken = ++this.playToken;
    this.stopAudioInternal(); // Stop any currently playing audio

    this.unlockContext();
    this.isPlaying = true;

    if (this.onStart) this.onStart();

    // 1. If audioUrl is provided directly, play it immediately
    if (options.audioUrl) {
      const success = await this.playAudioUrl(options.audioUrl, currentToken);
      if (success || currentToken !== this.playToken) return;
    }

    // 2. If no audioUrl provided, try requesting one from backend /api/tutor/tts
    try {
      const ttsResp = await fetch(`/api/tutor/tts?text=${encodeURIComponent(text)}`);
      if (currentToken !== this.playToken) return;
      if (ttsResp.ok) {
        const ttsData = await ttsResp.json();
        if (ttsData.audio_url) {
          const success = await this.playAudioUrl(ttsData.audio_url, currentToken);
          if (success || currentToken !== this.playToken) return;
        }
      }
    } catch (e) {
      console.log('Backend TTS generation fallback notice:', e);
    }

    if (currentToken !== this.playToken) return;

    // 3. Fallback to browser SpeechSynthesis
    this.fallbackSpeechSynthesis(text, options, currentToken);
  }

  /**
   * Plays a WAV/MP3 audio file through Web Audio API buffer node.
   * Feeds directly into this.analyser and this.audioContext.destination.
   */
  async playAudioUrl(audioUrl, token) {
    try {
      this.unlockContext();
      if (!this.audioContext) return false;

      const response = await fetch(audioUrl);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const arrayBuffer = await response.arrayBuffer();

      if (token !== this.playToken) return false;

      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
      }

      // decodeAudioData
      const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
      if (token !== this.playToken) return false;

      const source = this.audioContext.createBufferSource();
      source.buffer = audioBuffer;

      // Pipeline: Source -> Analyser -> Destination
      source.connect(this.analyser);
      this.analyser.connect(this.audioContext.destination);

      this.currentSource = source;

      source.onended = () => {
        if (this.currentSource === source && token === this.playToken) {
          this.currentSource = null;
          this.cleanup();
          if (this.onEnd) this.onEnd();
        }
      };

      source.start(0);
      this.startAmplitudeLoop();
      return true;
    } catch (err) {
      console.warn('AudioBuffer playback error, trying HTML Audio fallback:', err);
      try {
        const audio = new Audio(audioUrl);
        this.currentAudio = audio;
        audio.onended = () => {
          if (token === this.playToken) {
            this.currentAudio = null;
            this.cleanup();
            if (this.onEnd) this.onEnd();
          }
        };
        await audio.play();
        this.isPlaying = true;
        this.startAmplitudeLoop();
        return true;
      } catch (err2) {
        console.warn('HTML Audio fallback failed:', err2);
        return false;
      }
    }
  }

  /**
   * Fallback speech synthesis using Web Speech API or procedural oscillator.
   */
  fallbackSpeechSynthesis(text, options = {}, token) {
    if ('speechSynthesis' in window) {
      try {
        // Prevent Chrome's cancel-before-speak bug by ensuring paused is reset
        if (window.speechSynthesis.paused) {
          window.speechSynthesis.resume();
        }
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = options.rate || 1.0;
        utterance.pitch = options.pitch || 1.15;

        const voices = window.speechSynthesis.getVoices();
        const favVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Female') || v.name.includes('Samantha') || v.name.includes('Victoria')));
        if (favVoice) utterance.voice = favVoice;

        utterance.onstart = () => {
          if (token !== this.playToken) return;
          this.isPlaying = true;
          this.startAmplitudeLoop();
        };

        utterance.onend = () => {
          if (token !== this.playToken) return;
          this.cleanup();
          if (this.onEnd) this.onEnd();
        };

        utterance.onerror = (e) => {
          console.warn('SpeechSynthesis error:', e);
          if (token !== this.playToken) return;
          this.cleanup();
          if (this.onEnd) this.onEnd();
        };

        this.currentUtterance = utterance;
        window.speechSynthesis.speak(utterance);
        return;
      } catch (err) {
        console.warn('SpeechSynthesis exception:', err);
      }
    }

    // Procedural voice fallback
    const durationMs = Math.min(8000, Math.max(2000, text.length * 60));
    this.playProceduralVoice(durationMs);
    this.startAmplitudeLoop();
    setTimeout(() => {
      if (token === this.playToken) {
        this.cleanup();
        if (this.onEnd) this.onEnd();
      }
    }, durationMs);
  }

  playProceduralVoice(durationMs) {
    if (!this.audioContext || !this.analyser) return;
    this.unlockContext();

    try {
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(320, this.audioContext.currentTime);
      gain.gain.setValueAtTime(0.08, this.audioContext.currentTime);
      gain.gain.linearRampToValueAtTime(0.005, this.audioContext.currentTime + (durationMs / 1000));

      osc.connect(gain);
      gain.connect(this.analyser);
      this.analyser.connect(this.audioContext.destination);

      osc.start();
      osc.stop(this.audioContext.currentTime + (durationMs / 1000));
    } catch (e) {
      console.warn('Procedural voice error:', e);
    }
  }

  startAmplitudeLoop() {
    if (this.animFrameId) cancelAnimationFrame(this.animFrameId);
    const startTime = performance.now();

    const loop = () => {
      if (!this.isPlaying) return;

      let volume = 0;
      if (this.analyser && this.dataArray) {
        this.analyser.getByteFrequencyData(this.dataArray);
        let sum = 0;
        const count = 28;
        for (let i = 2; i < 30; i++) {
          sum += this.dataArray[i] || 0;
        }
        volume = Math.min(1.0, (sum / count) / 95);
      }

      // If audio has quiet moments or during vocal pauses, blend natural subtle syllable variation
      const elapsed = performance.now() - startTime;
      const naturalSyllable = 0.15 + (Math.sin(elapsed / 80) * 0.35 + Math.cos(elapsed / 140) * 0.25 + 0.25);
      const blendedVolume = volume > 0.05 ? Math.min(1.0, volume * 1.3) : Math.min(1.0, naturalSyllable * 0.6);

      if (this.onAmplitude) {
        this.onAmplitude(blendedVolume);
      }

      this.animFrameId = requestAnimationFrame(loop);
    };

    this.animFrameId = requestAnimationFrame(loop);
  }

  stopAudioInternal() {
    this.isPlaying = false;
    if (this.currentSource) {
      try {
        this.currentSource.stop();
        this.currentSource.disconnect();
      } catch (e) {}
      this.currentSource = null;
    }
    if (this.currentAudio) {
      try {
        this.currentAudio.pause();
        this.currentAudio.src = '';
      } catch (e) {}
      this.currentAudio = null;
    }
    if ('speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
      } catch (e) {}
    }
    if (this.animFrameId) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }
    if (this.onAmplitude) {
      this.onAmplitude(0);
    }
  }

  stop() {
    this.playToken++;
    this.stopAudioInternal();
    this.cleanup();
    if (this.onEnd) this.onEnd();
  }

  pause() {
    if (!this.isPlaying) return;
    this.isPlaying = false;
    if (this.audioContext && this.audioContext.state === 'running') {
      this.audioContext.suspend();
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.pause();
    }
    if (this.onPause) this.onPause();
  }

  resume() {
    this.isPlaying = true;
    if (this.audioContext && this.audioContext.state === 'suspended') {
      this.audioContext.resume();
    }
    if ('speechSynthesis' in window && window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
    }
    if (this.onResume) this.onResume();
    this.startAmplitudeLoop();
  }

  cleanup() {
    this.isPlaying = false;
    if (this.animFrameId) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }
    if (this.onAmplitude) {
      this.onAmplitude(0);
    }
  }
}
