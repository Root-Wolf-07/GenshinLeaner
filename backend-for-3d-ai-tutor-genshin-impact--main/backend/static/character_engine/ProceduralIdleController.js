/**
 * ProceduralIdleController.js
 * Controls subtle anatomical breathing, micro-weight adjustments, and gentle head nods/tilts.
 */

export class ProceduralIdleController {
  constructor(rigAdapter, characterId) {
    this.adapter = rigAdapter;
    this.characterId = characterId;

    this.elapsedTime = 0;
    this.breathSpeed = 1.4; // ~14 breaths per minute
    this.breathAmplitude = 0.012;

    this.headOffset = { pitch: 0, yaw: 0, roll: 0 };
    this.targetHeadOffset = { pitch: 0, yaw: 0, roll: 0 };

    this.reducedMotion = false;
  }

  setReducedMotion(enabled) {
    this.reducedMotion = !!enabled;
  }

  setHeadTarget(pitch, yaw, roll) {
    this.targetHeadOffset.pitch = pitch;
    this.targetHeadOffset.yaw = yaw;
    this.targetHeadOffset.roll = roll;
  }

  triggerNod() {
    this.targetHeadOffset.pitch = 0.08;
    setTimeout(() => {
      this.targetHeadOffset.pitch = 0.0;
    }, 450);
  }

  triggerHeadTilt() {
    this.targetHeadOffset.roll = 0.07;
    setTimeout(() => {
      this.targetHeadOffset.roll = 0.0;
    }, 600);
  }

  update(deltaTime) {
    if (this.reducedMotion) return;

    this.elapsedTime += deltaTime;

    // 1. Natural Breathing Sine Wave
    const breathCycle = Math.sin(this.elapsedTime * this.breathSpeed);
    const chestExpansion = breathCycle * this.breathAmplitude;

    if (this.adapter.chestBone) {
      this.adapter.chestBone.rotation.x = chestExpansion * 0.5;
    } else if (this.adapter.spineBone) {
      this.adapter.spineBone.rotation.x = chestExpansion * 0.4;
    } else {
      // Static mesh / unskinned fallback: gentle vertical floating breathing
      this.adapter.root.position.y += Math.cos(this.elapsedTime * this.breathSpeed) * 0.0003;
    }

    // 2. Head Tilt & Orientation Smoothing
    const lerpSpeed = Math.min(1.0, deltaTime * 4.0);
    this.headOffset.pitch += (this.targetHeadOffset.pitch - this.headOffset.pitch) * lerpSpeed;
    this.headOffset.yaw += (this.targetHeadOffset.yaw - this.headOffset.yaw) * lerpSpeed;
    this.headOffset.roll += (this.targetHeadOffset.roll - this.headOffset.roll) * lerpSpeed;

    if (this.adapter.headBone) {
      this.adapter.headBone.rotation.x = this.headOffset.pitch + (breathCycle * 0.005);
      this.adapter.headBone.rotation.y = this.headOffset.yaw;
      this.adapter.headBone.rotation.z = this.headOffset.roll;
    }
  }
}
