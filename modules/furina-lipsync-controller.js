/**
 * Genshin Cognitive Academy • Furina Lip Sync Controller
 * Synchronizes Furina's lower jaw bone ('齿Lower') and mouth controls
 * with real audio playback amplitude and timestamped viseme events.
 */

export class FurinaLipSyncController {
  constructor(jawBone, upperTeethBone = null) {
    this.jawBone = jawBone;
    this.upperTeethBone = upperTeethBone;

    // Cache base (resting closed-mouth) transforms
    this.baseJaw = {
      rotX: jawBone ? jawBone.rotation.x : 0,
      rotY: jawBone ? jawBone.rotation.y : 0,
      rotZ: jawBone ? jawBone.rotation.z : 0,
      posX: jawBone ? jawBone.position.x : 0,
      posY: jawBone ? jawBone.position.y : 0,
      posZ: jawBone ? jawBone.position.z : 0
    };

    this.isPlaying = false;
    this.audioVolume = 0;       // Raw volume from AnalyserNode (0.0 to 1.0)
    this.smoothedVolume = 0;   // Attack / decay smoothed volume
    this.currentViseme = 'closed';
    this.visemeWeight = 0;

    // Viseme configuration for Fontaine orator
    this.visemeMap = {
      closed: { jawDrop: 0.0, jawRot: 0.0, lateral: 0.0 },
      aa:     { jawDrop: 0.028, jawRot: 0.22, lateral: 0.0 },
      oh:     { jawDrop: 0.022, jawRot: 0.16, lateral: -0.005 },
      ee:     { jawDrop: 0.014, jawRot: 0.10, lateral: 0.008 },
      ou:     { jawDrop: 0.018, jawRot: 0.12, lateral: -0.008 }
    };

    console.log('FurinaLipSyncController Initialized with verified jaw bone:', !!this.jawBone);
  }

  startSpeech() {
    this.isPlaying = true;
  }

  stopSpeech() {
    this.isPlaying = false;
    this.audioVolume = 0;
    this.currentViseme = 'closed';
    this.visemeWeight = 0;
    this.resetNeutral();
  }

  setAudioVolume(vol) {
    if (!this.isPlaying) {
      this.audioVolume = 0;
      return;
    }
    this.audioVolume = Math.min(1.0, Math.max(0, vol));
  }

  setViseme(visemeName, intensity = 1.0) {
    if (!this.isPlaying) return;
    this.currentViseme = this.visemeMap[visemeName] ? visemeName : 'closed';
    this.visemeWeight = Math.min(1.0, Math.max(0, intensity));
  }

  resetNeutral() {
    if (this.jawBone) {
      this.jawBone.rotation.x = this.baseJaw.rotX;
      this.jawBone.rotation.y = this.baseJaw.rotY;
      this.jawBone.rotation.z = this.baseJaw.rotZ;
      this.jawBone.position.y = this.baseJaw.posY;
    }
    this.smoothedVolume = 0;
  }

  update(delta) {
    if (!this.jawBone) return;

    if (!this.isPlaying) {
      // Smooth return to neutral closed mouth
      this.smoothedVolume += (0 - this.smoothedVolume) * 0.25;
      if (this.smoothedVolume < 0.001) {
        this.resetNeutral();
        return;
      }
    } else {
      // Exponential attack (fast open) and decay (gentle close)
      const attackSpeed = 0.45;
      const decaySpeed = 0.22;
      const speed = this.audioVolume > this.smoothedVolume ? attackSpeed : decaySpeed;
      this.smoothedVolume += (this.audioVolume - this.smoothedVolume) * speed;
    }

    // Blend Priority B (Audio Analyser amplitude) and Priority A (Viseme target)
    const targetViseme = this.visemeMap[this.currentViseme] || this.visemeMap.closed;
    const dynamicAperture = Math.max(this.smoothedVolume, targetViseme.jawDrop * this.visemeWeight * 25.0);

    // Apply smoothed jaw opening (displacement along Y and slight X rotation)
    const jawYOffset = dynamicAperture * 0.024;
    const jawRotOffset = dynamicAperture * 0.18;

    this.jawBone.position.y = this.baseJaw.posY - jawYOffset;
    this.jawBone.rotation.x = this.baseJaw.rotX + jawRotOffset;
  }
}
