/**
 * Genshin Cognitive Academy • Barbara 3D Component
 * Three.js WebGL Renderer, Waist-Up Framing, Mondstadt Church Lighting,
 * and integration with BarbaraAnimationController and BarbaraLipSyncController.
 */

import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { BarbaraAnimationController } from './barbara-animation-controller.js';
import { BarbaraLipSyncController } from './barbara-lipsync-controller.js';

export class BarbaraTutor3D {
  constructor(container, options = {}) {
    this.container = typeof container === 'string'
      ? document.getElementById(container)
      : container;
    this.modelPath = options.modelPath || 'assets/models/barbara.glb';
    
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.model = null;

    // Sub-controllers
    this.animationController = null;
    this.lipSyncController = null;

    // Internal timing
    this.clock = new THREE.Clock();
    this.isDestroyed = false;

    if (!this.container) {
      console.error('Container element not found for BarbaraTutor3D');
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

    const width = this.container.clientWidth || 360;
    const height = this.container.clientHeight || 420;

    // Camera: Waist-up portrait framing
    this.camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
    this.camera.position.set(0, 1.15, 2.0);

    // Renderer (reuse existing canvas or create new)
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

    // Resize handling
    this.resizeObserver = new ResizeObserver(() => this.onResize());
    this.resizeObserver.observe(this.container);
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

    // Catalyst magic book point light
    this.bookLight = new THREE.PointLight(0x38bdf8, 1.8, 3.0);
    this.bookLight.position.set(0.4, 0.9, 0.5);
    this.scene.add(this.bookLight);
  }

  loadModel() {
    const loadingIndicator = document.getElementById('model-loading-indicator');
    const progressEl = document.getElementById('model-loading-progress');

    const loader = new GLTFLoader();
    loader.load(
      this.modelPath,
      (gltf) => {
        if (this.isDestroyed) return;
        this.model = gltf.scene;

        // Auto-fit and center Barbara in frame
        const box = new THREE.Box3().setFromObject(this.model);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());

        const maxDim = Math.max(size.x, size.y, size.z);
        const scale = 1.6 / maxDim;
        this.model.scale.setScalar(scale);

        // Center on waist / chest level
        this.basePosition = {
          x: -center.x * scale,
          y: -center.y * scale - 0.05,
          z: -center.z * scale
        };
        this.model.position.set(this.basePosition.x, this.basePosition.y, this.basePosition.z);

        // Traverse & optimize materials
        this.model.traverse((child) => {
          if (child.isMesh && child.material) {
            child.material.side = THREE.DoubleSide;
          }
        });

        this.scene.add(this.model);

        // Instantiate Animation & LipSync Controllers
        this.animationController = new BarbaraAnimationController(this.model, {
          basePosition: this.basePosition,
          baseScale: scale
        });

        this.lipSyncController = new BarbaraLipSyncController(
          this.animationController.nodes.mouth,
          this.animationController.nodes.teeth
        );

        // Hide loading indicator smoothly
        if (loadingIndicator) {
          loadingIndicator.style.opacity = '0';
          setTimeout(() => {
            loadingIndicator.style.display = 'none';
          }, 350);
        }
      },
      (xhr) => {
        if (progressEl && xhr.total) {
          const percent = Math.round((xhr.loaded / xhr.total) * 100);
          progressEl.textContent = `Streaming Barbara 3D Model: ${percent}%`;
        }
      },
      (error) => {
        console.error('Error loading Barbara 3D model:', error);
        if (loadingIndicator) {
          loadingIndicator.style.display = 'none';
        }
      }
    );
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

    if (this.animationController) {
      this.animationController.update(time, delta);
    }

    if (this.lipSyncController) {
      this.lipSyncController.update(delta);
    }

    if (this.bookLight && this.animationController) {
      this.bookLight.intensity = 1.8 + Math.sin(time * 3.0) * 0.5 + (this.animationController.audioVolume * 1.5);
    }

    if (this.renderer && this.scene && this.camera) {
      this.renderer.render(this.scene, this.camera);
    }
  }

  destroy() {
    this.isDestroyed = true;
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
    if (this.renderer) {
      this.renderer.dispose();
    }
  }
}
