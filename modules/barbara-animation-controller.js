/**
 * Genshin Cognitive Academy • Barbara Animation Controller
 * Centralized State Machine & Procedural Mesh/Node Manipulation
 * Supported States: idle, listening, thinking, speaking, explaining, questioning, encouraging, celebrating, error
 */

export class BarbaraAnimationController {
  constructor(model, options = {}) {
    this.model = model;
    this.state = 'idle';
    this.previousState = 'idle';
    
    // Configurable Node Map (verifies actual mesh nodes)
    this.nodes = {
      mouth: null,      // 口舌 (Mouth / tongue)
      teeth: null,      // 齿 (Teeth)
      hair: null,       // 发 (Pigtails)
      ribbons: null,    // 发饰 (Ribbons)
      skirt: null,      // 裙子 (Skirt)
      book: null,       // 魔法书 (Catalyst magic book at hip)
      blouse: null,     // 上衣 (Torso)
      face: null        // 面1 / 面2 / 肌
    };

    this.basePosition = options.basePosition || { x: 0, y: -0.05, z: 0 };
    this.baseScale = options.baseScale || 1.0;
    this.audioVolume = 0; // 0.0 to 1.0
    this.pointerOffset = { x: 0, y: 0 };
    this.rotations = { x: 0, y: 0, z: 0 };
    this.targetRotations = { x: 0, y: 0, z: 0 };

    this.inspectAndMapNodes();
  }

  inspectAndMapNodes() {
    if (!this.model) return;
    this.model.traverse((child) => {
      const name = child.name ? child.name.toLowerCase() : '';
      if (name.includes('口舌') || name.includes('mouth')) this.nodes.mouth = child;
      if (name.includes('齿') || name.includes('teeth')) this.nodes.teeth = child;
      if (name.includes('发') && !name.includes('饰')) this.nodes.hair = child;
      if (name.includes('发饰') || name.includes('二重')) this.nodes.ribbons = child;
      if (name.includes('裙子') || name.includes('skirt')) this.nodes.skirt = child;
      if (name.includes('魔法书') || name.includes('书') || name.includes('book')) this.nodes.book = child;
      if (name.includes('上衣') || name.includes('blouse')) this.nodes.blouse = child;
      if (name.includes('面') || name.includes('face')) this.nodes.face = child;
    });
  }

  setState(newState) {
    const validStates = [
      'idle', 'listening', 'thinking', 'speaking', 
      'explaining', 'questioning', 'encouraging', 'celebrating', 'error'
    ];
    if (!validStates.includes(newState)) {
      console.warn(`Unknown state: ${newState}, falling back to idle`);
      newState = 'idle';
    }
    this.previousState = this.state;
    this.state = newState;
  }

  getState() {
    return this.state;
  }

  setAudioVolume(vol) {
    this.audioVolume = Math.min(1.0, Math.max(0, vol));
  }

  setPointerOffset(x, y) {
    this.pointerOffset.x = x;
    this.pointerOffset.y = y;
  }

  update(time, delta) {
    if (!this.model) return;

    let hoverSpeed = 1.6;
    let hoverAmp = 0.012;
    let targetX = 0;
    let targetY = this.pointerOffset.x * 0.35; // interactive gaze
    let targetZ = 0;
    let bounceY = 0;

    // 1. Centralized State Reaction Engine
    switch (this.state) {
      case 'listening':
        // Attentive posture, leaning slightly forward, gentle breathing
        targetX = 0.035;
        targetY = this.pointerOffset.x * 0.45;
        hoverSpeed = 2.0;
        hoverAmp = 0.015;
        targetZ = Math.sin(time * 1.0) * 0.015;
        break;

      case 'thinking':
        // Head tilted to the side, slight upward gaze, contemplative rhythm
        targetZ = 0.09 + Math.sin(time * 1.2) * 0.02; // cute head tilt
        targetX = -0.025; // gaze shifted slightly upwards
        targetY = 0.06;
        hoverSpeed = 1.2;
        hoverAmp = 0.01;
        break;

      case 'speaking':
        // Teaching animation: rhythmic nodding aligned with voice volume
        const speechNod = Math.sin(time * 4.2) * (0.02 + this.audioVolume * 0.035);
        targetX = speechNod + 0.015;
        targetY = Math.sin(time * 2.2) * 0.06 + (this.pointerOffset.x * 0.2);
        targetZ = Math.sin(time * 2.5) * 0.02;
        hoverSpeed = 3.2;
        hoverAmp = 0.018 + this.audioVolume * 0.025;
        break;

      case 'explaining':
        // Authoritative yet gentle teaching posture, forward leaning explanation
        targetX = 0.04 + Math.sin(time * 3.0) * 0.02;
        targetY = Math.sin(time * 1.8) * 0.08 + (this.pointerOffset.x * 0.2);
        targetZ = -0.02;
        hoverSpeed = 2.4;
        hoverAmp = 0.02;
        break;

      case 'questioning':
        // Inquisitive head tilt, curious posture
        targetZ = -0.08 + Math.sin(time * 1.5) * 0.02;
        targetX = 0.025;
        targetY = this.pointerOffset.x * 0.4;
        hoverSpeed = 1.8;
        hoverAmp = 0.014;
        break;

      case 'encouraging':
        // Warm encouraging nod, smiling posture
        targetX = Math.abs(Math.sin(time * 3.0)) * 0.03;
        targetZ = Math.sin(time * 2.0) * 0.03;
        targetY = Math.sin(time * 1.5) * 0.05;
        hoverSpeed = 2.8;
        hoverAmp = 0.022;
        break;

      case 'celebrating':
        // Energetic happy hop with twirl bounce
        hoverSpeed = 4.8;
        bounceY = 0.12 + Math.abs(Math.sin(time * 4.8)) * 0.09;
        targetZ = Math.sin(time * 3.8) * 0.04;
        targetY = Math.sin(time * 2.5) * 0.12;
        break;

      case 'error':
        // Safe neutral fallback pose
        targetX = 0;
        targetY = 0;
        targetZ = 0;
        hoverSpeed = 1.0;
        hoverAmp = 0.005;
        break;

      default: // idle
        hoverSpeed = 1.5;
        hoverAmp = 0.012;
        targetX = 0;
        targetZ = 0;
        break;
    }

    // Smooth rotation interpolation
    this.rotations.x += (targetX - this.rotations.x) * 0.08;
    this.rotations.y += (targetY - this.rotations.y) * 0.08;
    this.rotations.z += (targetZ - this.rotations.z) * 0.08;

    this.model.rotation.set(this.rotations.x, this.rotations.y, this.rotations.z);

    // Subtle breathing hovering
    const hoverY = Math.sin(time * hoverSpeed) * hoverAmp;
    this.model.position.y = this.basePosition.y + hoverY + bounceY;

    // 2. Soft Sinusoidal Secondary Physics on Pigtails, Ribbons & Book
    if (this.nodes.hair) {
      this.nodes.hair.rotation.z = Math.sin(time * 2.8) * 0.05 + (this.state === 'speaking' ? Math.sin(time * 4.5) * 0.03 : 0);
      this.nodes.hair.rotation.x = Math.cos(time * 2.2) * 0.025;
    }
    if (this.nodes.ribbons) {
      this.nodes.ribbons.rotation.z = Math.sin(time * 3.2 + 0.5) * 0.06;
    }
    if (this.nodes.skirt) {
      this.nodes.skirt.rotation.y = Math.sin(time * 1.8) * 0.025;
    }
    if (this.nodes.book) {
      this.nodes.book.position.y += Math.sin(time * 2.2) * 0.001;
      this.nodes.book.rotation.y = Math.sin(time * 1.5) * 0.06;
    }
  }
}
