/**
 * Genshin Cognitive Academy • Furina Animation Controller
 * Centralized State Machine & Verified Skeletal Bone Rig Manipulation
 * Supported States: idle, listening, thinking, speaking, explaining, questioning, encouraging, celebrating, error
 */

export class FurinaAnimationController {
  constructor(model, options = {}) {
    this.model = model;
    this.state = 'idle';
    this.previousState = 'idle';

    // Verified Skeleton Bone Map
    this.bones = {
      head: null,          // 'Head'
      neck: null,          // 'Neck'
      spine: null,         // 'Spine'
      jaw: null,           // '齿Lower'
      hat: null,           // '帽'
      ahoge: null,         // 'DM_0_1'
      hairLeft: null,      // 'F_0_1_L'
      hairRight: null,     // 'F_0_1_R'
      leftShoulder: null,  // 'Left shoulder'
      leftArm: null,       // 'Left arm'
      leftElbow: null,     // 'Left elbow'
      leftWrist: null,     // 'Left wrist'
      rightShoulder: null, // 'Right shoulder'
      rightArm: null,      // 'Right arm'
      rightElbow: null,    // 'Right elbow'
      rightWrist: null     // 'Right wrist'
    };

    // Store base (rest) transforms so deltas don't drift or explode
    this.baseTransforms = new Map();

    this.basePosition = options.basePosition || { x: 0, y: 0, z: 0 };
    this.baseScale = options.baseScale || 1.0;
    this.audioVolume = 0; // 0.0 to 1.0
    this.pointerOffset = { x: 0, y: 0 };

    this.inspectAndMapBones();
  }

  inspectAndMapBones() {
    if (!this.model) return;

    this.model.traverse((child) => {
      const name = child.name || '';
      if (name === 'Head') this.bones.head = child;
      else if (name === 'Neck') this.bones.neck = child;
      else if (name === 'Spine') this.bones.spine = child;
      else if (name === '齿Lower') this.bones.jaw = child;
      else if (name === '帽') this.bones.hat = child;
      else if (name === 'DM_0_1') this.bones.ahoge = child;
      else if (name === 'F_0_1_L') this.bones.hairLeft = child;
      else if (name === 'F_0_1_R') this.bones.hairRight = child;
      else if (name === 'Left shoulder') this.bones.leftShoulder = child;
      else if (name === 'Left arm') this.bones.leftArm = child;
      else if (name === 'Left elbow') this.bones.leftElbow = child;
      else if (name === 'Left wrist') this.bones.leftWrist = child;
      else if (name === 'Right shoulder') this.bones.rightShoulder = child;
      else if (name === 'Right arm') this.bones.rightArm = child;
      else if (name === 'Right elbow') this.bones.rightElbow = child;
      else if (name === 'Right wrist') this.bones.rightWrist = child;

      // Cache resting rotation/position for mapped bones
      if (child.isBone || child.type === 'Bone' || child.type === 'Object3D') {
        this.baseTransforms.set(child, {
          rotX: child.rotation.x,
          rotY: child.rotation.y,
          rotZ: child.rotation.z,
          posX: child.position.x,
          posY: child.position.y,
          posZ: child.position.z
        });
      }
    });

    console.log('Furina Verified Bone Rig Mapping Complete:', {
      head: !!this.bones.head,
      neck: !!this.bones.neck,
      spine: !!this.bones.spine,
      jaw: !!this.bones.jaw,
      hat: !!this.bones.hat,
      ahoge: !!this.bones.ahoge,
      leftArm: !!this.bones.leftArm,
      rightArm: !!this.bones.rightArm
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

  // Smoothly blend bone rotations relative to rest pose
  applyBoneDelta(bone, dx, dy, dz, factor = 0.15) {
    if (!bone) return;
    const base = this.baseTransforms.get(bone) || { rotX: 0, rotY: 0, rotZ: 0 };
    const targetX = base.rotX + dx;
    const targetY = base.rotY + dy;
    const targetZ = base.rotZ + dz;

    bone.rotation.x += (targetX - bone.rotation.x) * factor;
    bone.rotation.y += (targetY - bone.rotation.y) * factor;
    bone.rotation.z += (targetZ - bone.rotation.z) * factor;
  }

  update(time, delta) {
    if (!this.model) return;

    // Common ambient wave frequencies
    const breathing = Math.sin(time * 2.0);
    const hairSway = Math.sin(time * 2.5);
    const ahogeBounce = Math.sin(time * 3.5);

    let modelPosY = this.basePosition.y;
    let modelRotY = this.pointerOffset.x * 0.15; // subtle interactive orientation

    // Target bone rotation offsets
    let headX = 0, headY = this.pointerOffset.x * 0.35, headZ = 0;
    let neckX = 0, neckY = this.pointerOffset.x * 0.15, neckZ = 0;
    let spineX = breathing * 0.015, spineY = 0, spineZ = 0;
    let hatX = 0, hatZ = 0;
    let ahogeZ = ahogeBounce * 0.05;
    let hairLeftZ = hairSway * 0.04;
    let hairRightZ = -hairSway * 0.04;

    // Arm gestures (Fontaine theatrical poses)
    let leftArmX = 0, leftArmY = 0, leftArmZ = 0;
    let rightArmX = 0, rightArmY = 0, rightArmZ = 0;
    let rightElbowY = 0, rightWristZ = 0;
    let leftElbowY = 0;

    switch (this.state) {
      case 'listening':
        // Attentive opera director posture: leaning forward, gaze focused on student
        headX = -0.04 + this.pointerOffset.y * 0.25;
        headY = this.pointerOffset.x * 0.45;
        headZ = Math.sin(time * 1.5) * 0.02; // attentive tilt
        spineX = 0.035; // lean in
        rightArmZ = -0.15;
        leftArmZ = 0.15;
        ahogeZ = 0.08 + Math.sin(time * 4.0) * 0.03;
        break;

      case 'thinking':
        // Contemplative Fontaine reflection: gaze raised toward opera ceiling, hand near chin
        headX = -0.12; // look slightly up
        headY = 0.15;
        headZ = 0.10 + Math.sin(time * 1.2) * 0.03;
        neckX = -0.05;
        spineX = -0.02; // slight lean back
        hatZ = 0.05;

        // Right hand positioned toward chin
        rightArmX = -0.45;
        rightArmY = 0.35;
        rightArmZ = -0.4;
        rightElbowY = 0.6;
        rightWristZ = 0.3;
        ahogeZ = 0.12 + Math.sin(time * 2.0) * 0.04;
        break;

      case 'speaking':
        // Dynamic orator: rhythmic speech nodding modulated by audio volume
        const speechCadence = Math.sin(time * 5.0) * (0.03 + this.audioVolume * 0.06);
        headX = speechCadence;
        headY = this.pointerOffset.x * 0.25 + Math.sin(time * 2.2) * 0.04;
        spineX = breathing * 0.02 + Math.sin(time * 3.0) * (0.01 + this.audioVolume * 0.02);
        
        // Expressive right arm gesturing with speech rhythm
        rightArmX = -0.25 + Math.sin(time * 3.5) * 0.1;
        rightArmZ = -0.2 - (this.audioVolume * 0.2);
        rightElbowY = 0.35 + (this.audioVolume * 0.25);
        ahogeZ = ahogeBounce * (0.06 + this.audioVolume * 0.1);
        break;

      case 'explaining':
        // Grand pedagogical theatre: broad open-palm declamation
        headX = Math.sin(time * 3.0) * 0.04;
        headY = this.pointerOffset.x * 0.3;
        headZ = Math.sin(time * 1.8) * 0.04;
        spineX = 0.025 + Math.sin(time * 2.5) * 0.02;

        // Both arms gesturing dramatically in classic Fontaine style
        rightArmX = -0.45 + Math.sin(time * 2.0) * 0.12;
        rightArmY = 0.3;
        rightArmZ = -0.45;
        rightElbowY = 0.55;

        leftArmX = -0.3 + Math.sin(time * 2.0 + 1.0) * 0.1;
        leftArmZ = 0.35;
        leftElbowY = -0.3;

        hatX = Math.sin(time * 2.0) * 0.03;
        ahogeZ = Math.sin(time * 4.0) * 0.12;
        break;

      case 'questioning':
        // Inquisitive arch: head tilted curiously, one hand gesturing forward
        headZ = -0.16 + Math.sin(time * 1.5) * 0.03;
        headY = 0.1 + this.pointerOffset.x * 0.3;
        headX = 0.04;
        hatZ = -0.06;

        // Right hand reaches forward inquisitively
        rightArmX = -0.4;
        rightArmZ = -0.25;
        rightElbowY = 0.45;
        rightWristZ = -0.2;
        ahogeZ = 0.15; // perked up ahoge
        break;

      case 'encouraging':
        // Warm supportive nods and friendly open posture
        headX = Math.sin(time * 4.0) * 0.06 - 0.02; // encouraging nods
        spineX = 0.02;
        rightArmZ = -0.25;
        leftArmZ = 0.25;
        rightElbowY = 0.3;
        leftElbowY = -0.3;
        ahogeZ = Math.sin(time * 5.0) * 0.08;
        break;

      case 'celebrating':
        // Theatrical triumph! Opera applause, joyful hop, flourish
        const hop = Math.abs(Math.sin(time * 5.5)) * 0.08;
        modelPosY = this.basePosition.y + hop;
        headX = -0.12 + Math.sin(time * 6.0) * 0.05; // head held high
        headZ = Math.sin(time * 4.0) * 0.08;
        hatX = -0.08 + Math.sin(time * 6.0) * 0.05;
        hatZ = Math.sin(time * 5.5) * 0.08;

        // Both arms raised high in triumphant Fontaine finale
        rightArmX = -0.8;
        rightArmZ = -0.65;
        rightElbowY = 0.7;

        leftArmX = -0.8;
        leftArmZ = 0.65;
        leftElbowY = -0.7;

        ahogeZ = Math.sin(time * 8.0) * 0.2;
        hairLeftZ = Math.sin(time * 6.0) * 0.12;
        hairRightZ = -Math.sin(time * 6.0) * 0.12;
        break;

      case 'error':
        // Safe neutral posture with gentle downcast recovery
        headX = 0.08;
        spineX = 0.03;
        hatX = 0.04;
        rightArmZ = -0.05;
        leftArmZ = 0.05;
        break;

      case 'idle':
      default:
        // Natural relaxed breathing & Fontaine poise
        modelPosY = this.basePosition.y + Math.sin(time * 1.8) * 0.008;
        headX = Math.sin(time * 1.5) * 0.015 + this.pointerOffset.y * 0.15;
        headY = this.pointerOffset.x * 0.25;
        headZ = Math.sin(time * 1.0) * 0.015;
        rightArmZ = -0.08 + Math.sin(time * 2.0) * 0.02;
        leftArmZ = 0.08 - Math.sin(time * 2.0) * 0.02;
        break;
    }

    // Apply model translation and rotation
    this.model.position.y += (modelPosY - this.model.position.y) * 0.15;
    this.model.rotation.y += (modelRotY - this.model.rotation.y) * 0.15;

    // Apply bone rotations smoothly with verify protection
    this.applyBoneDelta(this.bones.head, headX, headY, headZ, 0.18);
    this.applyBoneDelta(this.bones.neck, neckX, neckY, neckZ, 0.15);
    this.applyBoneDelta(this.bones.spine, spineX, spineY, spineZ, 0.12);
    this.applyBoneDelta(this.bones.hat, hatX, 0, hatZ, 0.2);
    this.applyBoneDelta(this.bones.ahoge, 0, 0, ahogeZ, 0.25);
    this.applyBoneDelta(this.bones.hairLeft, 0, 0, hairLeftZ, 0.15);
    this.applyBoneDelta(this.bones.hairRight, 0, 0, hairRightZ, 0.15);

    this.applyBoneDelta(this.bones.leftArm, leftArmX, leftArmY, leftArmZ, 0.15);
    this.applyBoneDelta(this.bones.rightArm, rightArmX, rightArmY, rightArmZ, 0.15);
    this.applyBoneDelta(this.bones.leftElbow, 0, leftElbowY, 0, 0.18);
    this.applyBoneDelta(this.bones.rightElbow, 0, rightElbowY, 0, 0.18);
    this.applyBoneDelta(this.bones.rightWrist, 0, 0, rightWristZ, 0.2);
  }
}
