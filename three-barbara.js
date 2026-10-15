import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

export class Barbara3DTutor {
  constructor(container, modelPath = 'assets/models/barbara.glb') {
    this.container = typeof container === 'string'
      ? document.getElementById(container)
      : container;
    this.modelPath = modelPath;
    this.state = 'idle'; // 'listening' | 'thinking' | 'speaking' | 'celebrating'
    this.model = null;
    this.mixer = null;
    this.audioVolume = 0;

    if (!this.container) {
      console.error('Container element not found for Barbara3DTutor');
      return;
    }

    this.initScene();
    this.setupLighting();
    this.loadModel();
    this.setupMouseTracking();
    this.animate();
  }

  initScene() {
    this.scene = new THREE.Scene();

    const width = this.container.clientWidth || 400;
    const height = this.container.clientHeight || 450;

    this.camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
    // Position camera for a waist-up portrait shot
    this.camera.position.set(0, 1.15, 2.0);

    // Reuse existing canvas if present, or create renderer
    const existingCanvas = this.container.querySelector('#barbara-webgl-canvas') || this.container.querySelector('canvas');
    if (existingCanvas) {
      existingCanvas.id = 'barbara-webgl-canvas';
      existingCanvas.className = 'barbara-webgl-canvas w-full h-full block';
      this.renderer = new THREE.WebGLRenderer({
        canvas: existingCanvas,
        antialias: true,
        alpha: true,
        powerPreference: 'high-performance'
      });
    } else {
      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      this.renderer.domElement.id = 'barbara-webgl-canvas';
      this.renderer.domElement.className = 'barbara-webgl-canvas w-full h-full block';
      this.container.appendChild(this.renderer.domElement);
    }

    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;

    window.addEventListener('resize', () => this.onResize());
  }

  setupLighting() {
    // Soft Mondstadt church ambient light
    const ambientLight = new THREE.AmbientLight(0xfff8f0, 1.8);
    this.scene.add(ambientLight);

    // Key front light
    const keyLight = new THREE.DirectionalLight(0xffffff, 2.2);
    keyLight.position.set(1.5, 3, 2.5);
    this.scene.add(keyLight);

    // Hydro-themed soft cyan rim light from behind
    const hydroRim = new THREE.DirectionalLight(0x56ccf2, 3.5);
    hydroRim.position.set(-2, 2.5, -2);
    this.scene.add(hydroRim);
  }

  loadModel() {
    const loadingIndicator = document.getElementById('model-loading-indicator');
    const loader = new GLTFLoader();
    loader.load(
      this.modelPath,
      (gltf) => {
        this.model = gltf.scene;

        // Auto-fit and center Barbara in frame
        const box = new THREE.Box3().setFromObject(this.model);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());

        const maxDim = Math.max(size.x, size.y, size.z);
        const scale = 1.6 / maxDim;
        this.model.scale.setScalar(scale);

        // Center on waist / chest level
        this.model.position.x = -center.x * scale;
        this.model.position.y = -center.y * scale - 0.05;
        this.model.position.z = -center.z * scale;

        // Ensure materials render cleanly
        this.model.traverse((child) => {
          if (child.isMesh && child.material) {
            child.material.side = THREE.DoubleSide;
          }
        });

        this.scene.add(this.model);

        // Smoothly dismiss loading indicator
        if (loadingIndicator) {
          loadingIndicator.style.opacity = '0';
          setTimeout(() => {
            loadingIndicator.style.display = 'none';
          }, 350);
        }
      },
      undefined,
      (error) => {
        console.error('Error loading Barbara 3D model:', error);
        if (loadingIndicator) {
          loadingIndicator.style.display = 'none';
        }
      }
    );
  }

  setupMouseTracking() {
    this.targetRotationY = 0;
    this.container.addEventListener('mousemove', (e) => {
      const rect = this.container.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      this.targetRotationY = x * 0.4; // subtle interactive head/torso turn
    });
  }

  setState(newState) {
    this.state = newState;
  }

  setAudioVolume(vol) {
    this.audioVolume = vol; // 0.0 to 1.0 from speech analyser
  }

  // Alias for backward compatibility
  setAudioAmplitude(vol) {
    this.setAudioVolume(vol);
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
    requestAnimationFrame(() => this.animate());
    const time = performance.now() * 0.001;

    if (this.model) {
      // Smooth mouse follow
      this.model.rotation.y += (this.targetRotationY - this.model.rotation.y) * 0.05;

      switch (this.state) {
        case 'listening':
          // Attentive forward posture with gentle breathing
          this.model.position.y = -0.05 + Math.sin(time * 2.0) * 0.015;
          this.model.rotation.x = 0.03;
          this.model.rotation.z = Math.sin(time * 1.0) * 0.015;
          break;

        case 'thinking':
          // Cute head tilt to the side
          this.model.position.y = -0.05 + Math.sin(time * 1.5) * 0.01;
          this.model.rotation.z = 0.08 + Math.sin(time * 1.2) * 0.02;
          this.model.rotation.x = -0.02;
          break;

        case 'speaking':
          // Teaching animation: rhythmic nodding, gesturing, and reacting to speech audio
          const speechPulse = this.audioVolume * 0.05;
          this.model.position.y = -0.05 + Math.sin(time * 3.5) * 0.02 + speechPulse;
          this.model.rotation.x = Math.sin(time * 4.0) * 0.03 + 0.02;
          this.model.rotation.z = Math.sin(time * 2.2) * 0.03;
          break;

        case 'celebrating':
          // Energetic, happy hop with twirl bounce
          this.model.position.y = -0.03 + Math.abs(Math.sin(time * 5.0)) * 0.06;
          this.model.rotation.z = Math.sin(time * 4.0) * 0.04;
          break;

        default: // idle
          this.model.position.y = -0.05 + Math.sin(time * 1.5) * 0.012;
          this.model.rotation.x = 0;
          this.model.rotation.z = 0;
      }
    }

    this.renderer.render(this.scene, this.camera);
  }
}
