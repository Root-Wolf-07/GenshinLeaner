/**
 * CharacterPerformanceEngine.js
 * Master coordinator for real-time 3D AI character performance.
 * Coordinates body, facial, and conversational layers with delta-time smoothing.
 */

import { CharacterRigAdapter } from './CharacterRigAdapter.js';
import { FacialExpressionController } from './FacialExpressionController.js';
import { EyeGazeController } from './EyeGazeController.js';
import { ProceduralIdleController } from './ProceduralIdleController.js';
import { LipSyncController } from './LipSyncController.js';
import { ConversationStateController, ConversationState } from './ConversationStateController.js';
import { AnimationPriorityManager, PerformancePriority } from './AnimationPriorityManager.js';

export class CharacterPerformanceEngine {
  /**
   * @param {THREE.Object3D} rootObject - Loaded Three.js model
   * @param {string} characterId - e.g. "nahida", "furina", "zhongli"
   * @param {object} capabilities - Rig capabilities from /api/v1/tutors/{id}/capabilities
   */
  constructor(rootObject, characterId, capabilities = {}) {
    this.characterId = characterId;
    this.capabilities = capabilities;

    // Sub-controllers
    this.rig = new CharacterRigAdapter(rootObject, characterId, capabilities);
    this.priority = new AnimationPriorityManager();
    this.facial = new FacialExpressionController(this.rig, characterId);
    this.eyeGaze = new EyeGazeController(this.rig, characterId);
    this.idle = new ProceduralIdleController(this.rig, characterId);
    this.lipSync = new LipSyncController(this.rig, characterId);
    this.conversation = new ConversationStateController(this);

    console.log(`[CharacterPerformanceEngine] Initialized for ${characterId}`);
  }

  /**
   * Execute an incoming CharacterPerformanceCommand from backend REST or WebSocket
   */
  executeCommand(command) {
    if (!command || !command.character_id) return;

    const requestedPriority = command.priority || PerformancePriority.CONVERSATION_ACTIVE;
    if (!this.priority.canExecute(requestedPriority, command.transition_duration_ms || 2500)) {
      console.log(`[CharacterPerformanceEngine] Command rejected by priority manager.`);
      return;
    }

    // 1. Conversation State Transition
    if (command.conversation_state) {
      this.conversation.transitionTo(command.conversation_state);
    }

    // 2. Target Morphs / Expressions
    if (command.target_morphs && Object.keys(command.target_morphs).length > 0) {
      this.facial.setExpression(command.target_morphs, command.transition_duration_ms || 350);
    }

    // 3. Skeletal Adjustments
    if (command.skeletal_adjustments) {
      if (command.skeletal_adjustments.head) {
        const { pitch = 0, yaw = 0, roll = 0 } = command.skeletal_adjustments.head;
        this.idle.setHeadTarget(pitch, yaw, roll);
      }
    }

    // 4. Gestures
    if (command.gesture_instruction === 'gentle_nod') {
      this.idle.triggerNod();
    } else if (command.gesture_instruction === 'curious_head_tilt') {
      this.idle.triggerHeadTilt();
    }
  }

  /**
   * Play speech with synchronized lip-sync
   */
  playSpeech(audioUrl, visemeTimeline = [], onEnded = null) {
    this.conversation.transitionTo(ConversationState.SPEAKING);
    this.lipSync.playSpeech(audioUrl, visemeTimeline, () => {
      this.conversation.transitionTo(ConversationState.IDLE);
      if (onEnded) onEnded();
    });
  }

  /**
   * Immediate interruption (e.g. user began speaking)
   */
  interrupt() {
    this.lipSync.stopSpeech();
    this.priority.releaseLock();
    this.conversation.transitionTo(ConversationState.INTERRUPTED);
  }

  /**
   * Primary frame loop - Call this from your Three.js requestAnimationFrame loop
   * @param {number} deltaTime - Delta time in seconds (clamped to prevent jumps)
   */
  update(deltaTime) {
    const clampedDelta = Math.min(deltaTime || 0.016, 0.1);

    this.idle.update(clampedDelta);
    this.eyeGaze.update(clampedDelta);
    this.facial.update(clampedDelta);
    this.lipSync.update(clampedDelta);
  }

  /**
   * Clean up resources upon switching tutors
   */
  dispose() {
    this.lipSync.stopSpeech();
    this.facial.resetToNeutral(0);
    console.log(`[CharacterPerformanceEngine] Disposed for ${this.characterId}`);
  }
}
