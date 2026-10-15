import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

export class Raiden3DTutor {
  constructor(containerElement, modelUrl) {
    this.container = typeof containerElement === 'string' 
      ? document.getElementById(containerElement) 
      : containerElement;
    this.modelUrl = modelUrl;
    this.state = 'idle'; // 'listening' | 'thinking' | 'speaking' | 'celebrating'
    this.audioVolume = 0;
    this.model = null;

    if (!this.container) {
      console.error('Container element not found for Raiden3DTutor');
      return;
    }

    this.initScene();
    this.loadModel();
    this.setupAudioAnalyser();
    this.setupResizeHandler();
    this.animate();
  }

  initScene() {
    this.scene = new THREE.Scene();
    const width = this.container.clientWidth || 320;
    const height = this.container.clientHeight || 380;

    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    this.camera.position.set(0, 1.2, 2.5);

    // Reuse existing canvas or create domElement
    const existingCanvas = this.container.querySelector('#raiden-webgl-canvas');
    if (existingCanvas) {
      this.renderer = new THREE.WebGLRenderer({
        canvas: existingCanvas,
        antialias: true,
        alpha: true,
        powerPreference: 'high-performance'
      });
    } else {
      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      this.renderer.domElement.id = 'raiden-webgl-canvas';
      this.renderer.domElement.className = 'raiden-webgl-canvas';
      this.container.appendChild(this.renderer.domElement);
    }

    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;

    // Genshin Inazuma-style lighting
    const ambientLight = new THREE.AmbientLight(0x381f66, 1.5);
    this.scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xf1eaff, 2.2);
    keyLight.position.set(2, 4, 3);
    this.scene.add(keyLight);

    // Electro rim light
    this.rimLight = new THREE.DirectionalLight(0xbd66ff, 4.0);
    this.rimLight.position.set(-2, 2, -2);
    this.scene.add(this.rimLight);
  }

  loadModel() {
    const loadingIndicator = document.getElementById('model-loading-indicator');
    const progressEl = document.getElementById('model-loading-progress');

    const loader = new GLTFLoader();
    loader.load(
      this.modelUrl,
      (gltf) => {
        this.model = gltf.scene;

        // Center and normalize scale
        const box = new THREE.Box3().setFromObject(this.model);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        
        const maxDim = Math.max(size.x, size.y, size.z);
        const scale = 1.6 / maxDim;
        this.model.scale.setScalar(scale);
        this.model.position.sub(center.multiplyScalar(scale));
        this.model.position.y -= 0.1; // adjust to upper chest framing

        // Optimize materials
        this.model.traverse((child) => {
          if (child.isMesh && child.material) {
            child.material.side = THREE.DoubleSide;
          }
        });

        this.scene.add(this.model);

        // Hide loading indicator smoothly
        if (loadingIndicator) {
          loadingIndicator.style.opacity = '0';
          setTimeout(() => {
            loadingIndicator.style.display = 'none';
          }, 400);
        }
      },
      (xhr) => {
        if (progressEl && xhr.total) {
          const percent = Math.round((xhr.loaded / xhr.total) * 100);
          progressEl.textContent = `Streaming Binary Assets: ${percent}%`;
        }
      },
      (error) => {
        console.warn('Error loading GLTF model:', error);
        if (loadingIndicator) {
          loadingIndicator.style.display = 'none';
        }
      }
    );
  }

  setState(newState) {
    this.state = newState;
  }

  setupAudioAnalyser() {
    this.audioVolume = 0;
  }

  setAudioVolume(vol) {
    this.audioVolume = Math.min(1.0, Math.max(0, vol));
  }

  // Alias for backward compatibility
  setAudioAmplitude(vol) {
    this.setAudioVolume(vol);
  }

  setupResizeHandler() {
    const resizeObserver = new ResizeObserver(() => {
      if (!this.container || !this.renderer || !this.camera) return;
      const width = this.container.clientWidth;
      const height = this.container.clientHeight;
      this.camera.aspect = width / height;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(width, height);
    });
    resizeObserver.observe(this.container);
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    const time = performance.now() * 0.001;

    if (this.model) {
      switch (this.state) {
        case 'listening':
          // Subtle breathing + slight attentive tilt
          this.model.position.y = -0.1 + Math.sin(time * 1.8) * 0.02;
          this.model.rotation.y = Math.sin(time * 0.8) * 0.05;
          this.model.rotation.x = 0.04; 
          break;

        case 'thinking':
          // Head/torso tilt with slower floating cycle
          this.model.position.y = -0.1 + Math.sin(time * 1.2) * 0.015;
          this.model.rotation.z = Math.sin(time * 1.5) * 0.04 - 0.05;
          this.model.rotation.y = 0.12;
          break;

        case 'speaking':
          // Teaching gesture motion: rhythmically nodding and active posture
          const speechSway = Math.sin(time * 6.0) * (0.03 + this.audioVolume * 0.04);
          this.model.position.y = -0.1 + Math.sin(time * 2.5) * 0.025 + speechSway;
          this.model.rotation.y = Math.sin(time * 2.0) * 0.08;
          this.model.rotation.x = Math.sin(time * 4.0) * 0.02;
          break;

        case 'celebrating':
          // Joyful energetic bobbing with pulse
          this.model.position.y = -0.08 + Math.abs(Math.sin(time * 4.0)) * 0.06;
          this.model.rotation.z = Math.sin(time * 3.0) * 0.03;
          break;

        default: // idle
          this.model.position.y = -0.1 + Math.sin(time * 1.5) * 0.02;
          this.model.rotation.y = Math.sin(time * 0.5) * 0.03;
          this.model.rotation.x = 0;
          this.model.rotation.z = 0;
      }
    }

    this.renderer.render(this.scene, this.camera);
  }
}
