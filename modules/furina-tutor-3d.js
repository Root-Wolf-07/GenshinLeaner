/**
 * Genshin Cognitive Academy • Furina 3D Tutor Component
 * Three.js WebGL Scene, Fontaine Opera Stage Lighting, Waist-Up Framing,
 * Skinned Mesh Bone Extraction, and Animation & Lip-Sync Integration.
 */

import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { FurinaAnimationController } from './furina-animation-controller.js';
import { FurinaLipSyncController } from './furina-lipsync-controller.js';

export class FurinaTutor3D {
  constructor(container, options = {}) {
    this.container = typeof container === 'string'
      ? document.getElementById(container)
      : container;
    this.modelPath = options.modelPath || 'assets/models/furina.glb';

    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.model = null;

    // Sub-controllers
    this.animationController = null;
    this.lipSyncController = null;

    // Timing
    this.clock = new THREE.Clock();
    this.isDestroyed = false;

    if (!this.container) {
      console.error('Container element not found for FurinaTutor3D');
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

    // Camera: Waist-up portrait framing centered on Furina's chest, ruffled jabot, and top hat
    this.camera = new THREE.PerspectiveCamera(38, width / height, 0.1, 100);
    this.camera.position.set(0, 1.32, 1.85);
    this.camera.lookAt(0, 1.30, 0);

    // Renderer (reuse existing canvas if present)
    const existingCanvas = this.container.querySelector('#furina-webgl-canvas') || 
                           this.container.querySelector('#barbara-webgl-canvas') || 
                           this.container.querySelector('canvas');
    if (existingCanvas) {
      existingCanvas.id = 'furina-webgl-canvas';
      existingCanvas.className = 'furina-webgl-canvas w-full h-full block';
      this.renderer = new THREE.WebGLRenderer({
        canvas: existingCanvas,
        antialias: true,
        alpha: true,
        powerPreference: 'high-performance'
      });
    } else {
      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      this.renderer.domElement.id = 'furina-webgl-canvas';
      this.renderer.domElement.className = 'furina-webgl-canvas w-full h-full block';
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
    // 1. Soft Opera Stage Ambient Light
    const ambientLight = new THREE.AmbientLight(0xe8f4fc, 1.8);
    this.scene.add(ambientLight);

    // 2. Front Key Spotlight
    const keyLight = new THREE.DirectionalLight(0xffffff, 2.4);
    keyLight.position.set(1.5, 3.2, 2.5);
    this.scene.add(keyLight);

    // 3. Fontaine Hydro Rim Light (Luminous Cyan)
    const hydroRim = new THREE.DirectionalLight(0x38bdf8, 3.8);
    hydroRim.position.set(-2.2, 2.8, -2.0);
    this.scene.add(hydroRim);

    // 4. Opera Epiclese Golden Brass Chandelier Fill Light
    const goldFill = new THREE.DirectionalLight(0xf5d77f, 1.2);
    goldFill.position.set(0, -1.0, 2.0);
    this.scene.add(goldFill);

    // 5. Hydro Vision Stage Aura Point Light
    this.visionLight = new THREE.PointLight(0x06b6d4, 1.6, 2.5);
    this.visionLight.position.set(-0.25, 1.25, 0.4);
    this.scene.add(this.visionLight);
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

        // Auto-fit and center Furina in frame
        const box = new THREE.Box3().setFromObject(this.model);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());

        console.log('Furina Model Loaded Bounds:', {
          size: { x: size.x, y: size.y, z: size.z },
          center: { x: center.x, y: center.y, z: center.z }
        });

        // The model is 1.72m tall. Standard scale 1.0 positions it naturally.
        const scale = 1.0;
        this.model.scale.setScalar(scale);

        // Center X and Z so Furina is horizontally centered in the canvas
        this.basePosition = {
          x: -center.x,
          y: 0,
          z: -center.z
        };
        this.model.position.set(this.basePosition.x, this.basePosition.y, this.basePosition.z);

        // Traverse & optimize materials
        this.model.traverse((child) => {
          if (child.isMesh && child.material) {
            child.material.side = THREE.DoubleSide;
            // Ensure alpha testing for hair fringe / eyelashes
            if (child.material.transparent || child.material.alphaTest !== undefined) {
              child.material.alphaTest = 0.5;
            }
          }
        });

        this.scene.add(this.model);

        // Instantiate Animation & LipSync Controllers with verified bone rig
        this.animationController = new FurinaAnimationController(this.model, {
          basePosition: this.basePosition,
          baseScale: scale
        });

        this.lipSyncController = new FurinaLipSyncController(
          this.animationController.bones.jaw
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
          progressEl.textContent = `Streaming Lady Furina 3D Model: ${percent}%`;
        }
      },
      (error) => {
        console.error('Error loading Furina 3D model:', error);
        if (loadingIndicator) {
          loadingIndicator.innerHTML = `
            <div class="text-rose-400 font-genshin text-sm text-center px-4">
              <p class="font-bold mb-1">Failed to load Furina 3D Model</p>
              <p class="text-xs text-slate-300">Please verify WebGL and asset path</p>
            </div>
          `;
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

    if (this.animationController) {
      this.animationController.update(time, delta);
    }

    if (this.lipSyncController) {
      this.lipSyncController.update(delta);
    }

    if (this.visionLight && this.animationController) {
      this.visionLight.intensity = 1.6 + Math.sin(time * 3.0) * 0.4 + (this.animationController.audioVolume * 1.5);
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
