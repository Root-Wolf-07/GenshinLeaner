/**
 * Genshin Cognitive Academy • Barbara Lip-Sync Controller
 * Priority A (Phoneme/Viseme event interpolation) & Priority B (Web Audio AnalyserNode Amplitude Sync)
 * Directly targets mouth (口舌) and teeth (齿) nodes with smooth interpolation and neutral reset
 */

export class BarbaraLipSyncController {
  constructor(mouthNode, teethNode) {
    this.mouthNode = mouthNode;
    this.teethNode = teethNode;

    this.isPlaying = false;
    this.audioVolume = 0;          // Priority B: real-time amplitude 0.0..1.0
    this.currentViseme = 'closed'; // Priority A: current viseme shape
    this.visemeIntensity = 0;      // 0.0..1.0
    this.currentMouthScale = 0.12;
    this.targetMouthScale = 0.12;

    // Viseme shape mappings
    this.visemeScaleMap = {
      'closed': 0.12,
      'aa': 0.95,
      'oh': 0.82,
      'ee': 0.65,
      'ou': 0.70
    };
  }

  setNodes(mouthNode, teethNode) {
    this.mouthNode = mouthNode;
    this.teethNode = teethNode;
  }

  startSpeech() {
    this.isPlaying = true;
  }

  stopSpeech() {
    this.isPlaying = false;
    this.audioVolume = 0;
    this.visemeIntensity = 0;
    this.targetMouthScale = 0.12;
    this.resetNeutral();
  }

  setAudioVolume(volume) {
    if (!this.isPlaying) return;
    this.audioVolume = Math.min(1.0, Math.max(0, volume));
  }

  setViseme(viseme, intensity = 1.0) {
    if (!this.isPlaying) return;
    this.currentViseme = viseme || 'closed';
    this.visemeIntensity = Math.min(1.0, Math.max(0, intensity));
  }

  resetNeutral() {
    this.targetMouthScale = 0.12;
    this.currentMouthScale = 0.12;
    if (this.mouthNode) {
      this.mouthNode.scale.set(1.0, 0.12, 1.0);
    }
    if (this.teethNode) {
      this.teethNode.scale.set(1.0, 0.12, 1.0);
    }
  }

  update(delta) {
    if (!this.isPlaying) {
      // Smoothly return to closed position if not already closed
      if (Math.abs(this.currentMouthScale - 0.12) > 0.01) {
        this.currentMouthScale += (0.12 - this.currentMouthScale) * 0.25;
        this.applyScale(this.currentMouthScale);
      }
      return;
    }

    // Blend Priority A (Viseme metadata) with Priority B (Audio Analyser Amplitude)
    const visemeTarget = this.visemeScaleMap[this.currentViseme] || 0.12;
    const baseTarget = Math.max(visemeTarget * this.visemeIntensity, this.audioVolume * 0.9);

    // Apply speech dynamics
    this.targetMouthScale = Math.min(1.0, Math.max(0.12, baseTarget));

    // Smooth lerp interpolation (eliminates jitter)
    this.currentMouthScale += (this.targetMouthScale - this.currentMouthScale) * 0.35;
    this.applyScale(this.currentMouthScale);
  }

  applyScale(scale) {
    if (this.mouthNode) {
      this.mouthNode.scale.set(1.0, scale, 1.0);
    }
    if (this.teethNode) {
      this.teethNode.scale.set(1.0, Math.max(0.2, scale * 0.85), 1.0);
    }
  }
}
