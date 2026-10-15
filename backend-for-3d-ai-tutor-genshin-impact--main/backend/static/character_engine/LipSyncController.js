/**
 * LipSyncController.js
 * Speech-synchronized lip articulation using viseme cues or Web Audio API amplitude fallback.
 */

export class LipSyncController {
  constructor(rigAdapter, characterId) {
    this.adapter = rigAdapter;
    this.characterId = characterId;

    this.isPlaying = false;
    this.audioElement = null;
    this.visemeTimeline = [];
    this.currentVisemeIndex = 0;

    this.activeMouthMorph = null;
    this.activeMouthWeight = 0;

    // Web Audio Fallback
    this.audioContext = null;
    this.analyser = null;
    this.amplitudeData = null;
  }

  playSpeech(audioUrl, visemeTimeline = [], onEnded = null) {
    this.stopSpeech(); // Clean up prior playback

    this.visemeTimeline = visemeTimeline || [];
    this.currentVisemeIndex = 0;
    this.isPlaying = true;

    this.audioElement = new Audio(audioUrl);
    this.audioElement.crossOrigin = 'anonymous';

    this.audioElement.onended = () => {
      this.stopSpeech();
      if (onEnded) onEnded();
    };

    this.audioElement.onerror = () => {
      console.warn('[LipSyncController] Audio playback failed; falling back to silent state.');
      this.stopSpeech();
      if (onEnded) onEnded();
    };

    // Setup Web Audio analyser if viseme timeline is not provided
    if (this.visemeTimeline.length === 0) {
      try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (AudioCtx) {
          this.audioContext = new AudioCtx();
          const source = this.audioContext.createMediaElementSource(this.audioElement);
          this.analyser = this.audioContext.createAnalyser();
          this.analyser.fftSize = 256;
          source.connect(this.analyser);
          this.analyser.connect(this.audioContext.destination);
          this.amplitudeData = new Uint8Array(this.analyser.frequencyBinCount);
        }
      } catch (e) {
        console.warn('[LipSyncController] Web Audio API setup skipped:', e);
      }
    }

    this.audioElement.play().catch((err) => {
      console.warn('[LipSyncController] Autoplay policy prevented immediate playback:', err);
      this.stopSpeech();
    });
  }

  stopSpeech() {
    this.isPlaying = false;
    if (this.audioElement) {
      this.audioElement.pause();
      this.audioElement.src = '';
      this.audioElement = null;
    }
    // Relax mouth shape immediately
    if (this.activeMouthMorph) {
      this.adapter.setMorphInfluence(this.activeMouthMorph, 0);
      this.activeMouthMorph = null;
    }
    const mouthMesh = this.adapter.getSubmesh('口舌');
    if (mouthMesh) mouthMesh.scale.y = 1.0;
  }

  update(deltaTime) {
    if (!this.isPlaying || !this.audioElement) {
      return;
    }

    const currentMs = this.audioElement.currentTime * 1000;

    // 1. Viseme Timeline Mode
    if (this.visemeTimeline.length > 0) {
      while (
        this.currentVisemeIndex < this.visemeTimeline.length - 1 &&
        currentMs >= this.visemeTimeline[this.currentVisemeIndex + 1].time_offset_ms
      ) {
        this.currentVisemeIndex++;
      }

      const cue = this.visemeTimeline[this.currentVisemeIndex];
      if (cue && cue.character_morph_target) {
        // Reset old morph if changed
        if (this.activeMouthMorph && this.activeMouthMorph !== cue.character_morph_target) {
          this.adapter.setMorphInfluence(this.activeMouthMorph, 0);
        }
        this.activeMouthMorph = cue.character_morph_target;
        this.adapter.setMorphInfluence(this.activeMouthMorph, cue.intensity);
      }
    } else if (this.analyser && this.amplitudeData) {
      // 2. Audio Amplitude Fallback
      this.analyser.getByteFrequencyData(this.amplitudeData);
      let sum = 0;
      for (let i = 0; i < this.amplitudeData.length; i++) sum += this.amplitudeData[i];
      const avg = sum / this.amplitudeData.length;
      const mouthOpen = Math.min(1.0, (avg / 128.0) * 1.4);

      // Apply to mouth morph if model supports it
      const defaultMouth = this.adapter.hasMorphTarget('あ') ? 'あ' : (
        this.adapter.hasMorphTarget('Mouth_Open01') ? 'Mouth_Open01' : null
      );
      if (defaultMouth) {
        this.adapter.setMorphInfluence(defaultMouth, mouthOpen);
      } else {
        // Submesh fallback for Barbara ('口舌' mouth mesh scale)
        const mouthMesh = this.adapter.getSubmesh('口舌');
        if (mouthMesh) {
          mouthMesh.scale.y = 1.0 + mouthOpen * 0.8;
        }
      }
    }
  }
}
