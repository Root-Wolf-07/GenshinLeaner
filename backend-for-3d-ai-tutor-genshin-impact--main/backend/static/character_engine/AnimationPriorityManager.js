/**
 * AnimationPriorityManager.js
 * Enforces hierarchical priority levels (1 to 5) so that lower-priority or stale
 * events cannot lock bones or overwrite critical speech / feedback states.
 */

export const PerformancePriority = {
  IDLE: 1,
  CONVERSATION_ACTIVE: 2,
  COGNITIVE_STATE: 3,
  FEEDBACK: 4,
  IMMEDIATE_INTERRUPT: 5,
};

export class AnimationPriorityManager {
  constructor() {
    this.currentPriority = PerformancePriority.IDLE;
    this.currentReason = 'idle';
    this.stateLockExpiry = 0;
  }

  canExecute(requestedPriority, maxDurationMs = 3000) {
    const now = performance.now();
    if (now >= this.stateLockExpiry) {
      this.currentPriority = PerformancePriority.IDLE;
    }
    if (requestedPriority >= this.currentPriority) {
      this.currentPriority = requestedPriority;
      this.stateLockExpiry = now + maxDurationMs;
      return true;
    }
    return false;
  }

  releaseLock() {
    this.currentPriority = PerformancePriority.IDLE;
    this.stateLockExpiry = 0;
  }
}
