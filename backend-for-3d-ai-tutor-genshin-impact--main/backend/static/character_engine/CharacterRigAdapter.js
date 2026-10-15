/**
 * CharacterRigAdapter.js
 * Inspects loaded Three.js Object3D/SkinnedMesh hierarchies, indexes bones, morph targets,
 * and submeshes, and routes commands according to actual model capabilities.
 */

export class CharacterRigAdapter {
  constructor(rootObject, characterId, capabilities) {
    this.root = rootObject;
    this.characterId = characterId;
    this.capabilities = capabilities || {};

    this.skinnedMeshes = [];
    this.morphMeshes = [];
    this.submeshes = new Map();
    this.bones = new Map();

    this.headBone = null;
    this.neckBone = null;
    this.spineBone = null;
    this.chestBone = null;
    this.leftEyeBone = null;
    this.rightEyeBone = null;
    this.tongueBone = null;

    this.morphTargetDictionary = new Map(); // name -> { meshIndex, targetIndex }

    this._indexHierarchy();
  }

  _indexHierarchy() {
    this.root.traverse((node) => {
      // 1. Index Bones
      if (node.isBone) {
        const cleanName = node.name.toLowerCase();
        this.bones.set(node.name, node);

        if (cleanName.includes('head') && !this.headBone) this.headBone = node;
        else if (cleanName.includes('neck') && !this.neckBone) this.neckBone = node;
        else if (cleanName.includes('spine') && !this.spineBone) this.spineBone = node;
        else if (cleanName.includes('chest') && !this.chestBone) this.chestBone = node;
        else if (cleanName.includes('eye') && cleanName.includes('l') && !this.leftEyeBone) this.leftEyeBone = node;
        else if (cleanName.includes('eye') && cleanName.includes('r') && !this.rightEyeBone) this.rightEyeBone = node;
        else if (cleanName.includes('tongue') && !this.tongueBone) this.tongueBone = node;
      }

      // 2. Index Meshes & Morph Targets
      if (node.isMesh) {
        this.submeshes.set(node.name, node);
        if (node.isSkinnedMesh) {
          this.skinnedMeshes.push(node);
        }
        if (node.morphTargetDictionary && node.morphTargetInfluences) {
          this.morphMeshes.push(node);
          for (const [name, idx] of Object.entries(node.morphTargetDictionary)) {
            if (!this.morphTargetDictionary.has(name)) {
              this.morphTargetDictionary.set(name, { mesh: node, index: idx });
            }
          }
        }
      }
    });

    console.log(`[CharacterRigAdapter] Indexed ${this.characterId}:`, {
      bonesCount: this.bones.size,
      morphTargetsCount: this.morphTargetDictionary.size,
      submeshesCount: this.submeshes.size,
      hasHeadBone: !!this.headBone,
      hasEyesBone: !!(this.leftEyeBone || this.rightEyeBone),
    });
  }

  hasMorphTarget(name) {
    return this.morphTargetDictionary.has(name);
  }

  setMorphInfluence(name, weight) {
    const entry = this.morphTargetDictionary.get(name);
    if (entry) {
      const clamped = Math.max(0, Math.min(1, weight));
      entry.mesh.morphTargetInfluences[entry.index] = clamped;
      return true;
    }
    return false;
  }

  getMorphInfluence(name) {
    const entry = this.morphTargetDictionary.get(name);
    return entry ? entry.mesh.morphTargetInfluences[entry.index] : 0;
  }

  resetAllMorphs() {
    for (const mesh of this.morphMeshes) {
      if (mesh.morphTargetInfluences) {
        for (let i = 0; i < mesh.morphTargetInfluences.length; i++) {
          mesh.morphTargetInfluences[i] = 0;
        }
      }
    }
  }

  getSubmesh(name) {
    return this.submeshes.get(name);
  }
}
