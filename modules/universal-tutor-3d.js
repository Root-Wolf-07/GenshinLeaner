/**
 * Genshin Cognitive Academy • Universal 3D Tutor Component
 * High-performance Three.js WebGL Scene supporting all 9 Genshin Impact characters,
 * dual GLTF/FBX model loading, automated texture binding, full-body head-to-toe framing,
 * OrbitControls 360° inspection, glowing elemental runic pedestal,
 * 9-state living game character animations, and synchronized jaw viseme lip-sync.
 */

import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { FBXLoader } from 'three/examples/jsm/loaders/FBXLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { TUTOR_REGISTRY, getTutorById } from './tutor-character-registry.js';

window.THREE = THREE;

export class UniversalTutor3D {
  constructor(container, options = {}) {
    this.container = typeof container === 'string'
      ? document.getElementById(container)
      : container;
    
    this.initialCharacter = options.character || 'raiden_shogun';
    this.activeTutor = getTutorById(this.initialCharacter);

    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;
    this.model = null;
    this.clock = new THREE.Clock();
    this.isLoaded = false;
    this.isDestroyed = false;
    this.loadRequestId = 0;

    // Controllers
    this.animationController = null;
    this.lipSyncController = null;

    // Dynamic Lights & Stage Elements
    this.rimLight = null;
    this.keyLight = null;
    this.fillLight = null;
    this.groundLight = null;
    this.pedestalGroup = null;
    this.pedestalRingMat = null;

    // Loaders
    this.gltfLoader = new GLTFLoader();
    this.fbxLoader = new FBXLoader();
    this.textureLoader = new THREE.TextureLoader();

    this.initScene();
    this.setupLighting();
    this.setupPedestal();
    this.setupControls();
    this.setupMouseTracking();
    this.loadTutor(this.activeTutor.id);
    this.animate();
  }

  initScene() {
    this.scene = new THREE.Scene();

    const width = this.container.clientWidth || 400;
    const height = this.container.clientHeight || 520;

    // Perspective camera calibrated for majestic FULL-BODY head-to-toe shot
    this.camera = new THREE.PerspectiveCamera(34, width / height, 0.1, 100);
    this.camera.position.set(0, 0.88, 3.45);
    this.camera.lookAt(0, 0.80, 0);

    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.25;

    // Replace or insert canvas
    const oldCanvas = this.container.querySelector('canvas.furina-webgl-canvas, canvas.tutor-webgl-canvas');
    if (oldCanvas) {
      this.renderer.domElement.id = oldCanvas.id || 'tutor-webgl-canvas';
      this.renderer.domElement.className = 'tutor-webgl-canvas furina-webgl-canvas';
      this.container.replaceChild(this.renderer.domElement, oldCanvas);
    } else {
      this.renderer.domElement.className = 'tutor-webgl-canvas furina-webgl-canvas';
      this.container.appendChild(this.renderer.domElement);
    }

    this.resizeObserver = new ResizeObserver(() => this.onResize());
    this.resizeObserver.observe(this.container);
  }

  setupControls() {
    // Interactive OrbitControls for 360° inspection and full-body zoom
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.target.set(0, 0.80, 0);
    this.controls.minDistance = 1.3;  // Zoom in to head/torso
    this.controls.maxDistance = 4.8;  // Zoom out to view full stage
    this.controls.maxPolarAngle = Math.PI / 2 + 0.06; // Keep camera above floor
    this.controls.minPolarAngle = 0.15;
    this.controls.enablePan = false;
  }

  setupLighting() {
    // 1. Ambient stage illumination
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.35);
    this.scene.add(ambientLight);

    // 2. Warm Key Light (Front-Right, high angle)
    this.keyLight = new THREE.DirectionalLight(0xfff5ea, 1.8);
    this.keyLight.position.set(2.0, 3.0, 2.5);
    this.scene.add(this.keyLight);

    // 3. Soft Fill Light (Front-Left)
    this.fillLight = new THREE.DirectionalLight(0xe0f2fe, 1.2);
    this.fillLight.position.set(-2.0, 1.8, 2.0);
    this.scene.add(this.fillLight);

    // 4. Element-Tinted Rim / Vision Light (Behind character)
    const elementColor = new THREE.Color(this.activeTutor.color);
    this.rimLight = new THREE.PointLight(elementColor, 2.6, 6.0);
    this.rimLight.position.set(0, 1.9, -1.0);
    this.scene.add(this.rimLight);

    // 5. Stage Foot / Ground Up-Light (Illuminates shoes, legs, and pedestal)
    this.groundLight = new THREE.PointLight(0xffecd1, 0.9, 3.2);
    this.groundLight.position.set(0, 0.25, 1.2);
    this.scene.add(this.groundLight);
  }

  setupPedestal() {
    // 3D Genshin Elemental Stage Platform (Anchors character feet to stage)
    this.pedestalGroup = new THREE.Group();
    this.pedestalGroup.name = 'stage-pedestal';

    // Pedestal base disc
    const baseGeo = new THREE.CylinderGeometry(0.85, 0.92, 0.05, 64);
    const baseMat = new THREE.MeshStandardMaterial({
      color: 0x0e1424,
      metalness: 0.85,
      roughness: 0.25,
      side: THREE.DoubleSide
    });
    const baseMesh = new THREE.Mesh(baseGeo, baseMat);
    baseMesh.position.y = -0.025;
    baseMesh.receiveShadow = true;
    this.pedestalGroup.add(baseMesh);

    // Golden metallic filigree trim ring
    const trimGeo = new THREE.RingGeometry(0.84, 0.89, 64);
    const trimMat = new THREE.MeshStandardMaterial({
      color: 0xd3bc8e,
      metalness: 0.9,
      roughness: 0.3,
      side: THREE.DoubleSide
    });
    const trimMesh = new THREE.Mesh(trimGeo, trimMat);
    trimMesh.rotation.x = -Math.PI / 2;
    trimMesh.position.y = 0.003;
    this.pedestalGroup.add(trimMesh);

    // Elemental Glowing Runes Ring
    const ringGeo = new THREE.RingGeometry(0.68, 0.77, 64);
    this.pedestalRingMat = new THREE.MeshBasicMaterial({
      color: new THREE.Color(this.activeTutor.color),
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.85
    });
    const ringMesh = new THREE.Mesh(ringGeo, this.pedestalRingMat);
    ringMesh.rotation.x = -Math.PI / 2;
    ringMesh.position.y = 0.006;
    this.pedestalGroup.add(ringMesh);

    // Soft Ambient Contact Shadow Disc beneath shoes
    const shadowGeo = new THREE.PlaneGeometry(1.4, 1.4);
    const shadowMat = new THREE.MeshBasicMaterial({
      color: 0x000000,
      transparent: true,
      opacity: 0.45
    });
    const shadowMesh = new THREE.Mesh(shadowGeo, shadowMat);
    shadowMesh.rotation.x = -Math.PI / 2;
    shadowMesh.position.y = 0.002;
    this.pedestalGroup.add(shadowMesh);

    this.scene.add(this.pedestalGroup);
  }

  updateElementLighting(hexColor) {
    if (this.rimLight) {
      this.rimLight.color.set(hexColor);
    }
    if (this.pedestalRingMat) {
      this.pedestalRingMat.color.set(hexColor);
    }
  }

  async loadTutor(tutorId) {
    const currentReq = ++this.loadRequestId;
    const tutor = getTutorById(tutorId);
    this.activeTutor = tutor;
    this.isLoaded = false;

    this.updateElementLighting(tutor.color);

    // Update UI Stage loading indicator
    const loadingEl = document.getElementById('model-loading-indicator');
    const progressEl = document.getElementById('model-loading-progress');
    if (loadingEl) {
      loadingEl.style.display = 'flex';
      loadingEl.style.opacity = '1';
      if (progressEl) {
        progressEl.textContent = `Streaming Full-Body 3D Tutor: ${tutor.name}...`;
      }
    }

    // Exhaustive cleanup of any existing tutor models in the scene
    const existingModels = [];
    this.scene.children.forEach((child) => {
      if (child.name !== 'stage-pedestal' && (child.type === 'Group' || child.type === 'Object3D' || (child.userData && child.userData.isTutorModel))) {
        existingModels.push(child);
      }
    });
    existingModels.forEach((obj) => {
      this.scene.remove(obj);
      obj.traverse((node) => {
        if (node.geometry) node.geometry.dispose();
        if (node.material) {
          const mats = Array.isArray(node.material) ? node.material : [node.material];
          mats.forEach(m => m.dispose());
        }
      });
    });
    this.model = null;
    this.animationController = null;
    this.lipSyncController = null;

    try {
      let object3D;
      if (tutor.modelFormat === 'fbx') {
        object3D = await new Promise((resolve, reject) => {
          this.fbxLoader.load(
            tutor.modelPath,
            (fbx) => resolve(fbx),
            (xhr) => {
              if (progressEl && xhr.total) {
                const pct = Math.round((xhr.loaded / xhr.total) * 100);
                progressEl.textContent = `Streaming ${tutor.name}: ${pct}%`;
              }
            },
            (err) => reject(err)
          );
        });
      } else {
        const gltf = await new Promise((resolve, reject) => {
          this.gltfLoader.load(
            tutor.modelPath,
            (res) => resolve(res),
            (xhr) => {
              if (progressEl && xhr.total) {
                const pct = Math.round((xhr.loaded / xhr.total) * 100);
                progressEl.textContent = `Streaming ${tutor.name}: ${pct}%`;
              }
            },
            (err) => reject(err)
          );
        });
        object3D = gltf.scene || gltf.scenes[0];
      }

      // Check if a newer request superseded this one while loading
      if (currentReq !== this.loadRequestId) {
        console.log(`[UniversalTutor3D] Discarding superseded load request for ${tutor.name}`);
        return;
      }

      // Secondary purge to ensure no overlapping models exist
      const purgeAgain = [];
      this.scene.children.forEach((child) => {
        if (child.name !== 'stage-pedestal' && (child.type === 'Group' || child.type === 'Object3D')) {
          purgeAgain.push(child);
        }
      });
      purgeAgain.forEach(obj => this.scene.remove(obj));

      object3D.name = `tutor-model-${tutor.id}`;
      object3D.userData.isTutorModel = true;
      this.model = object3D;

      // Normalize model orientation, full-body head-to-toe scale, and materials
      this.normalizeModel(object3D, tutor);

      this.scene.add(this.model);

      // Initialize Controllers
      this.animationController = new UniversalAnimationController(this.model, tutor);
      this.lipSyncController = new UniversalLipSyncController(this.animationController.bones.jaw);

      // Reset camera to standard full-body view
      this.camera.position.set(0, 0.88, 3.45);
      this.camera.lookAt(0, 0.80, 0);
      if (this.controls) {
        this.controls.target.set(0, 0.80, 0);
        this.controls.update();
      }

      this.isLoaded = true;

      // Hide loading indicator smoothly
      if (loadingEl) {
        loadingEl.style.opacity = '0';
        setTimeout(() => { loadingEl.style.display = 'none'; }, 350);
      }

      console.log(`[UniversalTutor3D] Full-body model ready: ${tutor.name} (${tutor.id})`);
    } catch (err) {
      console.error(`Failed to load tutor model for ${tutor.name}:`, err);
      if (loadingEl && progressEl) {
        progressEl.textContent = `Error loading ${tutor.name}`;
      }
    }
  }

  normalizeModel(object, tutor) {
    // 1. Material and Texture Enhancements (Ensures anime cel-shading looks gorgeous)
    object.traverse((node) => {
      if (node.isMesh) {
        node.castShadow = true;
        node.receiveShadow = true;
        if (node.material) {
          const mats = Array.isArray(node.material) ? node.material : [node.material];
          mats.forEach((m) => {
            m.side = THREE.DoubleSide; // Render both sides of capes, skirts, hair
            if (m.transparent) {
              m.alphaTest = 0.45; // Eliminates alpha-sorting glitches on bangs
              m.depthWrite = true;
            }
            if (m.map) {
              m.map.colorSpace = THREE.SRGBColorSpace;
              m.map.generateMipmaps = true;
            }
            if (m.roughness !== undefined) m.roughness = Math.max(0.45, m.roughness);
            if (m.metalness !== undefined) m.metalness = Math.min(0.2, m.metalness);
          });
        }
      }
    });

    // 2. Measure raw dimensions
    const bbox = new THREE.Box3().setFromObject(object);
    const size = new THREE.Vector3();
    bbox.getSize(size);

    // Standardize character height to 1.70 meters (full human proportion from head to toe)
    const targetHeight = 1.70;
    const currentHeight = size.y || 1.0;
    const scaleFactor = targetHeight / currentHeight;
    object.scale.set(scaleFactor, scaleFactor, scaleFactor);

    // 3. Re-calculate bounding box after scaling
    const scaledBbox = new THREE.Box3().setFromObject(object);
    const scaledCenter = new THREE.Vector3();
    scaledBbox.getCenter(scaledCenter);

    // Center horizontally on (0, 0)
    object.position.x = -scaledCenter.x;
    object.position.z = -scaledCenter.z;
    // Set feet directly on ground level (y = 0.0) so full-body stands majestically on the pedestal
    object.position.y = -scaledBbox.min.y;

    // Apply any fine-tuned manual adjustments from registry if specified
    if (tutor.modelOffset) {
      object.position.x += tutor.modelOffset.x || 0;
      object.position.z += tutor.modelOffset.z || 0;
    }
  }

  setupMouseTracking() {
    this.container.addEventListener('mousemove', (e) => {
      const rect = this.container.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      if (this.animationController) {
        this.animationController.setPointerOffset(x, y);
      }
    });

    this.container.addEventListener('mouseleave', () => {
      if (this.animationController) {
        this.animationController.setPointerOffset(0, 0);
      }
    });
  }

  setState(newState) {
    if (this.animationController) {
      this.animationController.setState(newState);
    }
  }

  getState() {
    return this.animationController ? this.animationController.getState() : 'idle';
  }

  setAudioVolume(vol) {
    if (this.animationController) {
      this.animationController.setAudioVolume(vol);
    }
    if (this.lipSyncController) {
      this.lipSyncController.setAudioVolume(vol);
    }
  }

  onResize() {
    if (!this.container || !this.renderer || !this.camera) return;
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  animate() {
    if (this.isDestroyed) return;
    requestAnimationFrame(() => this.animate());

    const delta = this.clock.getDelta();
    const time = performance.now() * 0.001;

    if (this.controls) {
      this.controls.update();
    }

    if (this.animationController) {
      this.animationController.update(time, delta);
    }

    if (this.lipSyncController) {
      this.lipSyncController.update(delta);
    }

    // Dynamic elemental vision aura pulse
    if (this.rimLight && this.animationController) {
      this.rimLight.intensity = 2.2 + Math.sin(time * 3.0) * 0.5 + (this.animationController.audioVolume * 1.8);
    }

    // Pedestal ring pulse
    if (this.pedestalRingMat) {
      this.pedestalRingMat.opacity = 0.70 + Math.sin(time * 2.5) * 0.20;
    }

    if (this.renderer && this.scene && this.camera) {
      this.renderer.render(this.scene, this.camera);
    }
  }

  destroy() {
    this.isDestroyed = true;
    if (this.resizeObserver) this.resizeObserver.disconnect();
    if (this.controls) this.controls.dispose();
    if (this.renderer) this.renderer.dispose();
  }
}

/**
 * Universal Animation Controller
 * Implements living game character behavior across all 9 teaching states,
 * natural breathing, eye/head cursor tracking, expressive gesture inflections,
 * and arm/spine dynamics.
 */
class UniversalAnimationController {
  constructor(model, tutorConfig) {
    this.model = model;
    this.tutor = tutorConfig;
    this.state = 'idle';
    this.audioVolume = 0;
    this.pointer = { x: 0, y: 0 };
    this.targetPointer = { x: 0, y: 0 };

    this.basePosition = new THREE.Vector3().copy(model.position);
    this.baseRotation = new THREE.Euler().copy(model.rotation);

    this.bones = {
      head: null,
      neck: null,
      spine: null,
      chest: null,
      jaw: null,
      leftArm: null,
      rightArm: null,
      leftForeArm: null,
      rightForeArm: null
    };

    this.initialBoneRotations = new Map();
    this.indexBones();
  }

  indexBones() {
    this.model.traverse((node) => {
      if (node.isBone) {
        const name = node.name.toLowerCase();
        this.initialBoneRotations.set(node, node.rotation.clone());

        if (!this.bones.jaw && (node.name.includes('齿Lower') || name.includes('jaw') || name.includes('mouth_lower') || name.includes('chin'))) {
          this.bones.jaw = node;
        } else if (!this.bones.head && (name.includes('head') || node.name.includes('头'))) {
          this.bones.head = node;
        } else if (!this.bones.neck && (name.includes('neck') || node.name.includes('颈'))) {
          this.bones.neck = node;
        } else if (!this.bones.spine && (name.includes('spine') || node.name.includes('脊椎'))) {
          this.bones.spine = node;
        } else if (!this.bones.chest && (name.includes('chest') || node.name.includes('胸'))) {
          this.bones.chest = node;
        } else if (!this.bones.leftArm && (name.includes('upperarm') || name.includes('arm')) && (name.includes('l') || name.includes('left') || node.name.includes('左腕'))) {
          this.bones.leftArm = node;
        } else if (!this.bones.rightArm && (name.includes('upperarm') || name.includes('arm')) && (name.includes('r') || name.includes('right') || node.name.includes('右腕'))) {
          this.bones.rightArm = node;
        }
      }
    });

    console.log(`[AnimationController] ${this.tutor.name} bones indexed:`, {
      head: Boolean(this.bones.head),
      jaw: Boolean(this.bones.jaw),
      spine: Boolean(this.bones.spine),
      arms: Boolean(this.bones.leftArm || this.bones.rightArm)
    });
  }

  setState(newState) {
    this.state = newState;
  }

  getState() {
    return this.state;
  }

  setAudioVolume(vol) {
    this.audioVolume = Math.max(0, Math.min(1, vol));
  }

  setPointerOffset(x, y) {
    this.targetPointer.x = Math.max(-0.5, Math.min(0.5, x));
    this.targetPointer.y = Math.max(-0.5, Math.min(0.5, y));
  }

  update(time, delta) {
    // Smooth pointer lerp
    this.pointer.x += (this.targetPointer.x - this.pointer.x) * 0.1;
    this.pointer.y += (this.targetPointer.y - this.pointer.y) * 0.1;

    // 1. Posture & Full-Body Idle Breathing Oscillation
    const breathFreq = this.state === 'speaking' || this.state === 'explaining' ? 2.6 : 1.3;
    const breathAmp = this.state === 'celebrating' ? 0.022 : 0.010;
    const hoverOffset = Math.sin(time * breathFreq) * breathAmp;
    this.model.position.y = this.basePosition.y + hoverOffset;

    // 2. Head tracking towards user cursor with expressive state reactions
    if (this.bones.head) {
      const initHead = this.initialBoneRotations.get(this.bones.head);
      if (initHead) {
        let headTargetY = initHead.y + (this.pointer.x * 0.35);
        let headTargetX = initHead.x - (this.pointer.y * 0.25);
        let headTargetZ = initHead.z;

        // State-specific procedural gestures
        if (this.state === 'thinking') {
          headTargetZ += 0.14; // Inquisitive tilt
          headTargetX += 0.10;
        } else if (this.state === 'questioning') {
          headTargetZ -= 0.16;
          headTargetY += 0.10;
        } else if (this.state === 'celebrating') {
          headTargetX -= 0.14; // Happy looking up
          headTargetY += Math.sin(time * 6.0) * 0.10;
        } else if (this.state === 'speaking' || this.state === 'explaining') {
          headTargetX += Math.sin(time * 3.5) * 0.06 * (1 + this.audioVolume);
          headTargetY += Math.cos(time * 2.5) * 0.05 * (1 + this.audioVolume);
        }

        this.bones.head.rotation.x += (headTargetX - this.bones.head.rotation.x) * 0.15;
        this.bones.head.rotation.y += (headTargetY - this.bones.head.rotation.y) * 0.15;
        this.bones.head.rotation.z += (headTargetZ - this.bones.head.rotation.z) * 0.15;
      }
    }

    // 3. Spine & Chest Breathing Dynamics
    if (this.bones.spine) {
      const initSpine = this.initialBoneRotations.get(this.bones.spine);
      if (initSpine) {
        let spineTargetX = initSpine.x + (Math.sin(time * breathFreq) * 0.015);
        if (this.state === 'listening') spineTargetX += 0.06; // Attentive lean forward
        if (this.state === 'explaining') spineTargetX -= 0.04; // Confident upright posture
        this.bones.spine.rotation.x += (spineTargetX - this.bones.spine.rotation.x) * 0.1;
      }
    }

    // 4. Expressive Arm Gestures (Living Game Character Animation)
    if (this.bones.leftArm) {
      const initLArm = this.initialBoneRotations.get(this.bones.leftArm);
      if (initLArm) {
        let lTargetZ = initLArm.z;
        let lTargetX = initLArm.x;
        if (this.state === 'speaking' || this.state === 'explaining') {
          lTargetZ += Math.sin(time * 2.2) * 0.08 * (1 + this.audioVolume);
          lTargetX += Math.cos(time * 1.8) * 0.06;
        } else if (this.state === 'celebrating') {
          lTargetZ += 0.25; // Raised arm
          lTargetX -= 0.15;
        }
        this.bones.leftArm.rotation.z += (lTargetZ - this.bones.leftArm.rotation.z) * 0.1;
        this.bones.leftArm.rotation.x += (lTargetX - this.bones.leftArm.rotation.x) * 0.1;
      }
    }

    if (this.bones.rightArm) {
      const initRArm = this.initialBoneRotations.get(this.bones.rightArm);
      if (initRArm) {
        let rTargetZ = initRArm.z;
        let rTargetX = initRArm.x;
        if (this.state === 'speaking' || this.state === 'explaining') {
          rTargetZ -= Math.sin(time * 2.0) * 0.08 * (1 + this.audioVolume);
          rTargetX += Math.cos(time * 2.2) * 0.06;
        } else if (this.state === 'celebrating') {
          rTargetZ -= 0.25; // Raised arm
          rTargetX -= 0.15;
        }
        this.bones.rightArm.rotation.z += (rTargetZ - this.bones.rightArm.rotation.z) * 0.1;
        this.bones.rightArm.rotation.x += (rTargetX - this.bones.rightArm.rotation.x) * 0.1;
      }
    }
  }
}

/**
 * Universal Lip-Sync Controller
 * Drives verified jaw bone displacement and visemes with neutral resting return.
 */
class UniversalLipSyncController {
  constructor(jawBone) {
    this.jawBone = jawBone;
    this.audioVolume = 0;
    this.visemeWeight = 0;
    this.currentViseme = 'closed';
    this.initialJawRotation = jawBone ? jawBone.rotation.clone() : new THREE.Euler();
    this.initialJawPosition = jawBone ? jawBone.position.clone() : new THREE.Vector3();
  }

  setAudioVolume(vol) {
    this.audioVolume = Math.max(0, Math.min(1.0, vol));
  }

  setViseme(viseme, intensity = 1.0) {
    this.currentViseme = viseme;
    this.visemeWeight = Math.max(0, Math.min(1.0, intensity));
  }

  startSpeech() {
    this.visemeWeight = 0.5;
  }

  stopSpeech() {
    this.audioVolume = 0;
    this.visemeWeight = 0;
    this.currentViseme = 'closed';
  }

  update(delta) {
    if (!this.jawBone) return;

    // Blend acoustic amplitude + viseme target
    let targetDisplacement = 0;
    if (this.currentViseme === 'aa') targetDisplacement = 0.22 * this.visemeWeight;
    else if (this.currentViseme === 'oh') targetDisplacement = 0.26 * this.visemeWeight;
    else if (this.currentViseme === 'ee') targetDisplacement = 0.15 * this.visemeWeight;
    else if (this.currentViseme === 'ou') targetDisplacement = 0.18 * this.visemeWeight;
    else if (this.currentViseme === 'closed') targetDisplacement = 0.0;

    const blendedAmp = Math.max(this.audioVolume * 0.20, targetDisplacement);

    // Smoothly apply rotation around X axis (jaw opening)
    const targetRotX = this.initialJawRotation.x + blendedAmp;
    this.jawBone.rotation.x += (targetRotX - this.jawBone.rotation.x) * 0.45;

    // Slight vertical displacement if rig uses translation
    const targetPosY = this.initialJawPosition.y - (blendedAmp * 0.015);
    this.jawBone.position.y += (targetPosY - this.jawBone.position.y) * 0.45;
  }
}
