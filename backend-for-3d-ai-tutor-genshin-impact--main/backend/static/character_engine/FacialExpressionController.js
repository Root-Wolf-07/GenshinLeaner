/**
 * FacialExpressionController.js
 * Controls smooth emotional facial expression blending, natural non-mechanical blinking,
 * and morph target interpolation.
 */

export class FacialExpressionController {
  constructor(rigAdapter, characterId) {
    this.adapter = rigAdapter;
    this.characterId = characterId;

    this.currentMorphWeights = new Map(); // targetName -> currentWeight
    this.targetMorphWeights = new Map();  // targetName -> desiredWeight

    this.transitionSpeed = 5.0; // Lerp factor per second

    // Natural blinking state
    this.blinkEnabled = true;
    this.blinkTimer = 0;
    this.nextBlinkInterval = this._getRandomBlinkInterval();
    this.blinkPhase = 'idle'; // 'idle', 'closing', 'opening'
    this.blinkProgress = 0;
    this.isDoubleBlink = false;

    // Detect blink target names
    this.blinkTargetName = this._detectBlinkMorph();
  }

  _detectBlinkMorph() {
    if (this.adapter.hasMorphTarget('Eye_Lowereyelid')) return 'Eye_Lowereyelid';
    if (this.adapter.hasMorphTarget('まばたき')) return 'まばたき';
    if (this.adapter.hasMorphTarget('Eye_Default')) return 'Eye_Default';
    return null;
  }

  _getRandomBlinkInterval() {
    // Random interval between 2.5 and 5.5 seconds
    return 2.5 + Math.random() * 3.0;
  }

  setExpression(targetMap, transitionDurationMs = 350) {
    this.transitionSpeed = Math.max(1.0, 1000.0 / transitionDurationMs);
    // Mark target weights
    this.targetMorphWeights.clear();
    for (const [name, weight] of Object.entries(targetMap)) {
      if (this.adapter.hasMorphTarget(name)) {
        this.targetMorphWeights.set(name, Math.max(0, Math.min(1, weight)));
      }
    }
  }

  resetToNeutral(durationMs = 400) {
    this.transitionSpeed = 1000.0 / durationMs;
    this.targetMorphWeights.clear();
  }

  update(deltaTime) {
    // 1. Interpolate Expression Morphs
    const allKeys = new Set([...this.currentMorphWeights.keys(), ...this.targetMorphWeights.keys()]);
    for (const key of allKeys) {
      // Do not overwrite blink morph during blink phase
      if (key === this.blinkTargetName && this.blinkPhase !== 'idle') {
        continue;
      }
      const current = this.currentMorphWeights.get(key) || 0;
      const target = this.targetMorphWeights.get(key) || 0;
      const delta = target - current;
      const step = delta * Math.min(1.0, deltaTime * this.transitionSpeed);
      const updated = current + step;

      if (Math.abs(updated) < 0.005 && target === 0) {
        this.currentMorphWeights.delete(key);
        this.adapter.setMorphInfluence(key, 0);
      } else {
        this.currentMorphWeights.set(key, updated);
        this.adapter.setMorphInfluence(key, updated);
      }
    }

    // 2. Procedural Natural Blinking
    this._updateBlinking(deltaTime);
  }

  _updateBlinking(deltaTime) {
    if (!this.blinkEnabled) return;

    this.blinkTimer += deltaTime;

    if (this.blinkPhase === 'idle') {
      if (this.blinkTimer >= this.nextBlinkInterval) {
        this.blinkPhase = 'closing';
        this.blinkProgress = 0;
        this.blinkTimer = 0;
        this.isDoubleBlink = Math.random() < 0.22; // 22% chance of natural double-blink
      }
    } else if (this.blinkPhase === 'closing') {
      this.blinkProgress += deltaTime * 12.0; // Fast close ~80ms
      if (this.blinkProgress >= 1.0) {
        this.blinkProgress = 1.0;
        this.blinkPhase = 'opening';
      }
      this._applyBlinkWeight(this.blinkProgress);
    } else if (this.blinkPhase === 'opening') {
      this.blinkProgress -= deltaTime * 8.0; // Slightly slower open ~120ms
      if (this.blinkProgress <= 0.0) {
        this.blinkProgress = 0.0;
        this._applyBlinkWeight(0.0);
        if (this.isDoubleBlink) {
          this.isDoubleBlink = false;
          this.blinkPhase = 'closing'; // Trigger second immediate blink
        } else {
          this.blinkPhase = 'idle';
          this.nextBlinkInterval = this._getRandomBlinkInterval();
        }
      } else {
        this._applyBlinkWeight(this.blinkProgress);
      }
    }
  }

  _applyBlinkWeight(weight) {
    if (this.blinkTargetName) {
      this.adapter.setMorphInfluence(this.blinkTargetName, weight);
    } else {
      // Submesh fallback for Barbara ('目' eyes mesh scale)
      const eyeMesh = this.adapter.getSubmesh('目');
      if (eyeMesh) {
        eyeMesh.scale.y = Math.max(0.05, 1.0 - weight * 0.95);
      }
    }
  }
}
