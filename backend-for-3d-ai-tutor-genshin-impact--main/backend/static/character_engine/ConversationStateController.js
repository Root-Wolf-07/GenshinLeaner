/**
 * ConversationStateController.js
 * Turn-taking state machine: idle -> listening -> processing -> speaking -> waiting.
 */

export const ConversationState = {
  IDLE: 'idle',
  LISTENING: 'listening',
  PROCESSING: 'processing',
  PREPARING_RESPONSE: 'preparing_response',
  SPEAKING: 'speaking',
  INTERRUPTED: 'interrupted',
  WAITING_FOR_STUDENT: 'waiting_for_student',
  RECOVERING_FROM_ERROR: 'recovering_from_error',
};

export class ConversationStateController {
  constructor(engine) {
    this.engine = engine;
    this.currentState = ConversationState.IDLE;
    this.stateTimeout = null;
  }

  transitionTo(newState, durationMs = 0) {
    if (this.stateTimeout) {
      clearTimeout(this.stateTimeout);
      this.stateTimeout = null;
    }

    const previousState = this.currentState;
    this.currentState = newState;
    console.log(`[ConversationStateController] ${previousState} -> ${newState}`);

    // Update child controllers
    if (newState === ConversationState.LISTENING) {
      this.engine.eyeGaze.setMode('attentive');
      this.engine.idle.triggerNod();
      this.engine.facial.setExpression({ Brow_Smily_L: 0.3, Brow_Smily_R: 0.3, なごみ: 0.3 });
    } else if (newState === ConversationState.PROCESSING) {
      this.engine.eyeGaze.setMode('thinking');
      this.engine.idle.setHeadTarget(-0.05, 0.06, -0.04);
      this.engine.facial.setExpression({ Brow_Squeeze_L: 0.5, Brow_Squeeze_R: 0.5, じと目: 0.4 });
    } else if (newState === ConversationState.SPEAKING) {
      this.engine.eyeGaze.setMode('attentive');
      this.engine.idle.setHeadTarget(0.0, 0.0, 0.0);
    } else if (newState === ConversationState.INTERRUPTED) {
      this.engine.lipSync.stopSpeech();
      this.engine.eyeGaze.setMode('attentive');
      this.engine.facial.resetToNeutral(150);
      this.engine.idle.setHeadTarget(0.0, 0.0, 0.0);
    } else if (newState === ConversationState.IDLE) {
      this.engine.eyeGaze.setMode('resting');
      this.engine.facial.resetToNeutral(400);
      this.engine.idle.setHeadTarget(0.0, 0.0, 0.0);
    }

    if (durationMs > 0) {
      this.stateTimeout = setTimeout(() => {
        this.transitionTo(ConversationState.IDLE);
      }, durationMs);
    }
  }

  getState() {
    return this.currentState;
  }
}
