/**
 * EyeGazeController.js
 * Manages natural eye gaze, micro-saccades, and thinking gaze shifts.
 */

export class EyeGazeController {
  constructor(rigAdapter, characterId) {
    this.adapter = rigAdapter;
    this.characterId = characterId;

    this.currentGaze = { pitch: 0, yaw: 0 };
    this.targetGaze = { pitch: 0, yaw: 0 };

    this.saccadeTimer = 0;
    this.nextSaccadeInterval = 1.8;
    this.mode = 'attentive'; // 'attentive', 'thinking', 'resting'
  }

  setMode(mode) {
    this.mode = mode;
    if (mode === 'thinking') {
      // Look slightly up and away during thought
      this.targetGaze = { pitch: 0.12, yaw: 0.15 };
    } else if (mode === 'attentive') {
      // Look directly at conversational target / camera
      this.targetGaze = { pitch: 0.0, yaw: 0.0 };
    } else {
      this.targetGaze = { pitch: -0.05, yaw: 0.0 };
    }
  }

  update(deltaTime) {
    // 1. Natural micro-saccades (subtle eye twitches)
    this.saccadeTimer += deltaTime;
    if (this.saccadeTimer >= this.nextSaccadeInterval) {
      this.saccadeTimer = 0;
      this.nextSaccadeInterval = 1.2 + Math.random() * 2.0;

      if (this.mode === 'attentive') {
        // Very tiny jitter around center (-0.02 to +0.02 rad)
        this.targetGaze.pitch = (Math.random() - 0.5) * 0.04;
        this.targetGaze.yaw = (Math.random() - 0.5) * 0.04;
      }
    }

    // 2. Smoothly interpolate gaze
    const lerpSpeed = 6.0 * deltaTime;
    this.currentGaze.pitch += (this.targetGaze.pitch - this.currentGaze.pitch) * lerpSpeed;
    this.currentGaze.yaw += (this.targetGaze.yaw - this.currentGaze.yaw) * lerpSpeed;

    // 3. Apply to skeletal eye bones if present
    const leftEye = this.adapter.leftEyeBone;
    const rightEye = this.adapter.rightEyeBone;

    if (leftEye) {
      leftEye.rotation.x = this.currentGaze.pitch;
      leftEye.rotation.y = this.currentGaze.yaw;
    }
    if (rightEye) {
      rightEye.rotation.x = this.currentGaze.pitch;
      rightEye.rotation.y = this.currentGaze.yaw;
    }
  }
}
