/**
 * Genshin Cognitive Academy • Centralized Tutor Character Registry
 * Maps the 9 Academic Subjects to their assigned Genshin Impact 3D Tutors,
 * visual element styling, 3D model formats, camera framing, and pedagogical profiles.
 */

export const TUTOR_REGISTRY = {
  raiden_shogun: {
    id: 'raiden_shogun',
    name: 'Raiden Ei / Shogun',
    title: 'Archon of Electro • Master of Pure Logic & Mathematical Proof',
    subject: 'Mathematics',
    subjectAliases: ['math', 'mathematics', 'calculus', 'algebra', 'geometry', 'statistics'],
    element: 'Electro',
    elementIcon: '⚡',
    color: '#a259ff',
    glowColor: 'rgba(162, 89, 255, 0.45)',
    stageBg: 'radial-gradient(circle at 50% 30%, #1e0d38 0%, #0c061a 85%)',
    vignetteClass: 'electro-vignette-overlay',
    modelPath: '/assets/models/raiden_shogun/raiden_shogun.glb',
    modelFormat: 'glb',
    scale: 0.95,
    cameraOffset: { x: 0, y: 0.95, z: 3.10 },
    modelOffset: { x: 0, y: 0, z: 0 },
    voice: { name: 'Samantha', pitch: 0.85, rate: 1.0 },
    defaultLine: 'State your mathematical premise clearly. Through disciplined axioms and verified logic, all obscurities vanish.',
    suggestedInquiries: [
      'Derive the fundamental theorem of calculus step-by-step',
      'Explain eigenvalue decomposition and matrix transformations',
      'How does Bayes Theorem update conditional probabilities?'
    ],
    socraticChallenge: {
      question: 'In multivariable calculus, what does the gradient vector ∇f always point towards?',
      options: [
        { text: 'Direction of steepest ascent', correct: true },
        { text: 'Direction of minimum curvature', correct: false },
        { text: 'Parallel to the level surface contour', correct: false },
        { text: 'Towards the coordinate origin', correct: false }
      ],
      hints: [
        'Recall the definition of directional derivative D_u f = ∇f · u.',
        'Consider which unit vector u maximizes the dot product ∇f · u.',
        'When u is parallel to ∇f, cos(θ) = 1, achieving maximum rate of change.',
        'Solution: The gradient vector points directly in the direction of greatest spatial rate of increase.'
      ],
      praise: 'Flawless mathematical proof! Rigorous deduction is the foundation of eternity.'
    }
  },

  zhongli: {
    id: 'zhongli',
    name: 'Zhongli',
    title: 'The God of Contracts • Venerable Historian & Philosopher',
    subject: 'Humanities & Social Sciences',
    subjectAliases: ['humanities', 'social sciences', 'history', 'geography', 'civics', 'economics'],
    element: 'Geo',
    elementIcon: '🔶',
    color: '#e5b042',
    glowColor: 'rgba(229, 176, 66, 0.45)',
    stageBg: 'radial-gradient(circle at 50% 30%, #2b1f0d 0%, #120b04 85%)',
    vignetteClass: 'geo-vignette-overlay',
    modelPath: '/assets/models/zhongli/scene.gltf',
    modelFormat: 'gltf',
    scale: 0.92,
    cameraOffset: { x: 0, y: 0.95, z: 3.10 },
    modelOffset: { x: 0, y: 0, z: 0 },
    voice: { name: 'Alex', pitch: 0.80, rate: 0.94 },
    defaultLine: 'History is an enduring contract between past civilizations and modern reflection. What era or doctrine shall we examine?',
    suggestedInquiries: [
      'Analyze the economic causes of the Bronze Age collapse',
      'Explain how institutional checks and balances developed in ancient Rome',
      'How does physical geography shape geopolitical trade corridors?'
    ],
    socraticChallenge: {
      question: 'Which historical mechanism was most instrumental in stabilizing inter-city trade along maritime Silk Roads?',
      options: [
        { text: 'Standardized mercantile contracts & bill of exchange credit', correct: true },
        { text: 'Strict isolationist trade tariffs', correct: false },
        { text: 'Total naval conquest of all coastline settlements', correct: false },
        { text: 'Exclusive reliance on barter exchange', correct: false }
      ],
      hints: [
        'Consider how merchants mitigated the extreme risk of transporting bullion across oceans.',
        'Financial instruments allowed merchants to redeem value without physically shipping gold coins.',
        'Letters of credit and promissory contracts established reciprocal trust across jurisdictions.',
        'Solution: Standardized commercial contracts and credit bills enabled secure cross-border trade without physical gold risk.'
      ],
      praise: 'An astute historical deduction. Perspective, trust, and patience reveal all foundational truths.'
    }
  },

  barbara: {
    id: 'barbara',
    name: 'Barbara Pegg',
    title: 'Deaconess of Favonius • Mentor of Biological Wonders',
    subject: 'Biology & Zoology',
    subjectAliases: ['biology', 'zoology', 'anatomy', 'ecology', 'genetics', 'botany'],
    element: 'Hydro',
    elementIcon: '💧',
    color: '#4fc3f7',
    glowColor: 'rgba(79, 195, 247, 0.45)',
    stageBg: 'radial-gradient(circle at 50% 30%, #0d283d 0%, #05131f 85%)',
    vignetteClass: 'hydro-vignette-overlay',
    modelPath: '/assets/models/barbara/barbara.glb',
    modelFormat: 'glb',
    scale: 0.96,
    cameraOffset: { x: 0, y: 0.95, z: 3.10 },
    modelOffset: { x: 0, y: 0, z: 0 },
    voice: { name: 'Victoria', pitch: 1.25, rate: 1.05 },
    defaultLine: 'Let’s explore the miraculous wonders of life! From cellular ATP synthesis to ocean ecosystems, where shall we sing our first lesson?',
    suggestedInquiries: [
      'Explain the electron transport chain and chemiosmotic ATP synthesis',
      'How does CRISPR-Cas9 locate and edit specific genomic sequences?',
      'Describe trophic cascade dynamics in marine ecosystems'
    ],
    socraticChallenge: {
      question: 'During cellular respiration, where does the highest concentration of protons (H+) accumulate to drive ATP synthase?',
      options: [
        { text: 'Mitochondrial intermembrane space', correct: true },
        { text: 'Cytoplasmic cytosol', correct: false },
        { text: 'Inner mitochondrial matrix', correct: false },
        { text: 'Nuclear envelope lumen', correct: false }
      ],
      hints: [
        'Complexes I, III, and IV pump protons across the inner membrane.',
        'They pump them OUT of the matrix, creating an electrochemical proton gradient.',
        'The protons then rush back inward through ATP synthase rotor blades.',
        'Solution: Protons pool within the intermembrane space, powering rotational catalytic ATP phosphorylation.'
      ],
      praise: 'Magnificent! Every cell of your deduction is glowing with biological vitality! ✦'
    }
  },

  furina: {
    id: 'furina',
    name: 'Lady Furina ✦',
    title: 'Stage Director of Fontaine • Master of Oratory, Drama & Cadence',
    subject: 'Dance, Communication & Music',
    subjectAliases: ['dance', 'communication', 'music', 'drama', 'public speaking', 'creative writing'],
    element: 'Hydro (Ousia)',
    elementIcon: '🎭',
    color: '#38bdf8',
    glowColor: 'rgba(56, 189, 248, 0.45)',
    stageBg: 'radial-gradient(circle at 50% 30%, #0d213f 0%, #061124 85%)',
    vignetteClass: 'hydro-vignette-overlay',
    modelPath: '/assets/models/furina/furina.glb',
    modelFormat: 'glb',
    scale: 1.0,
    cameraOffset: { x: 0, y: 0.95, z: 3.10 },
    modelOffset: { x: 0, y: 0, z: 0 },
    voice: { name: 'Samantha', pitch: 1.15, rate: 1.02 },
    defaultLine: 'Welcome to the grand Opera of learning! The curtain is raised, the spotlights shine, and every word carries dramatic resonance.',
    suggestedInquiries: [
      'How does theatrical pacing and rhetorical pauses enhance speech persuasion?',
      'Explain harmonic polyphony vs homophony in musical composition',
      'What are the core principles of nonverbal staging and presence?'
    ],
    socraticChallenge: {
      question: 'When crafting an persuasive oration, which classical rhetorical appeal establishes credibility and ethical presence?',
      options: [
        { text: 'Ethos', correct: true },
        { text: 'Pathos', correct: false },
        { text: 'Logos', correct: false },
        { text: 'Kairos', correct: false }
      ],
      hints: [
        'Think of how a stage director establishes authentic authority before delivering lines.',
        'Pathos appeals to emotion; Logos appeals to rational syllogisms.',
        'The third pillar anchors the speaker’s character, integrity, and competence.',
        'Solution: Ethos is the projection of moral authority, expertise, and trustworthy character.'
      ],
      praise: 'Magnifique! Bravo, mon cher Traveler! A standing ovation for flawless theatrical rhetoric! ✦'
    }
  },

  tsaritsa: {
    id: 'tsaritsa',
    name: 'The Tsaritsa',
    title: 'Sovereign of Snezhnaya • Scholar of Global Languages & Etymology',
    subject: 'General Knowledge & Languages',
    subjectAliases: ['general knowledge', 'languages', 'linguistics', 'grammar', 'etymology', 'world literature'],
    element: 'Cryo',
    elementIcon: '❄️',
    color: '#93c5fd',
    glowColor: 'rgba(147, 197, 253, 0.45)',
    stageBg: 'radial-gradient(circle at 50% 30%, #152238 0%, #080f1a 85%)',
    vignetteClass: 'cryo-vignette-overlay',
    modelPath: '/assets/models/tsaritsa/RH9IC74KOYH64ZMLDFBR9M9J6.fbx',
    modelFormat: 'fbx',
    scale: 0.0105,
    cameraOffset: { x: 0, y: 0.95, z: 3.10 },
    modelOffset: { x: 0, y: 0, z: 0 },
    voice: { name: 'Samantha', pitch: 0.90, rate: 0.98 },
    defaultLine: 'Words construct the boundaries of empire and intellect. What linguistic root or global chronicle shall we master today?',
    suggestedInquiries: [
      'Trace Proto-Indo-European cognates across modern Germanic and Romance languages',
      'How does syntactic recursion differentiate human language from animal communication?',
      'Explain the grammatical function of grammatical aspect vs tense'
    ],
    socraticChallenge: {
      question: 'In historical linguistics, which phonological law explains systematic consonant shifts from Proto-Indo-European into Proto-Germanic?',
      options: [
        { text: 'Grimm’s Law', correct: true },
        { text: 'Moore’s Law', correct: false },
        { text: 'Zipf’s Law', correct: false },
        { text: 'Heisenberg Principle', correct: false }
      ],
      hints: [
        'Named after one of the famous Brothers who compiled folktales and philological works.',
        'Explains why Latin "pater" corresponds to English "father" (voiceless stop /p/ -> voiceless fricative /f/).',
        'Demonstrates predictable consonant mutations across millennia.',
        'Solution: Grimm’s Law proves genetic relationship and sound mutation across Indo-European branches.'
      ],
      praise: 'Poised, dignified, and linguistically precise. True sovereignty lies in mastery of knowledge.'
    }
  },

  nahida: {
    id: 'nahida',
    name: 'Lesser Lord Kusanali (Nahida)',
    title: 'Archon of Wisdom • Guide of Moral Studies & Ethical Philosophy',
    subject: 'Moral Studies',
    subjectAliases: ['moral studies', 'ethics', 'philosophy', 'critical thinking', 'empathy'],
    element: 'Dendro',
    elementIcon: '🌿',
    color: '#5cb85c',
    glowColor: 'rgba(92, 184, 92, 0.45)',
    stageBg: 'radial-gradient(circle at 50% 30%, #112e1a 0%, #06140b 85%)',
    vignetteClass: 'dendro-vignette-overlay',
    modelPath: '/assets/models/nahida/NPC_Avatar_YoungGirl_Catalyst_Nahida (merge).fbx',
    modelFormat: 'fbx',
    scale: 0.0125,
    cameraOffset: { x: 0, y: 0.95, z: 3.10 },
    modelOffset: { x: 0, y: 0, z: 0 },
    voice: { name: 'Samantha', pitch: 1.30, rate: 1.0 },
    defaultLine: 'Curiosity is the seed from which empathy and wisdom grow. What ethical puzzle or philosophical riddle shall we explore together?',
    suggestedInquiries: [
      'Compare Kantian deontology with rule utilitarianism in modern bioethics',
      'How does John Rawls’s "Veil of Ignorance" construct a just society?',
      'What constitutes moral responsibility in autonomous artificial intelligence?'
    ],
    socraticChallenge: {
      question: 'In John Rawls’s theory of justice, what thought experiment ensures fair foundational rules without bias toward personal privilege?',
      options: [
        { text: 'The Veil of Ignorance in the Original Position', correct: true },
        { text: 'The Ring of Gyges invisibility test', correct: false },
        { text: 'The Prisoner’s Dilemma matrix', correct: false },
        { text: 'The Tragedy of the Commons dilemma', correct: false }
      ],
      hints: [
        'Imagine designing the rules of society without knowing if you will be born rich, poor, healthy, or disadvantaged.',
        'Ignorance of one’s own social standing forces rational choice towards protecting the most vulnerable.',
        'This ensures no self-serving bias corrupts constitutional design.',
        'Solution: The Veil of Ignorance strips knowledge of personal circumstances to guarantee fairness for all.'
      ],
      praise: 'A profound reflection! Your understanding blooms like a radiant Padisarah in full bloom! ✦'
    }
  },

  ganyu: {
    id: 'ganyu',
    name: 'Ganyu',
    title: 'General Secretary of the Qixing • Natural Philosopher of Physics',
    subject: 'Physics',
    subjectAliases: ['physics', 'mechanics', 'thermodynamics', 'optics', 'electromagnetism', 'astronomy'],
    element: 'Cryo',
    elementIcon: '🏹',
    color: '#67e8f9',
    glowColor: 'rgba(103, 232, 249, 0.45)',
    stageBg: 'radial-gradient(circle at 50% 30%, #0d2738 0%, #05121c 85%)',
    vignetteClass: 'cryo-vignette-overlay',
    modelPath: '/assets/models/ganyu/SK预览最终.fbx',
    modelFormat: 'fbx',
    scale: 0.010,
    cameraOffset: { x: 0, y: 0.95, z: 3.10 },
    modelOffset: { x: 0, y: 0, z: 0 },
    voice: { name: 'Samantha', pitch: 1.0, rate: 0.96 },
    defaultLine: 'Every trajectory across the stars follows precise physical conservation laws. Let us balance our equations with care and patience.',
    suggestedInquiries: [
      'Derive Maxwell’s displacement current and wave propagation in vacuum',
      'Explain relativistic time dilation and Lorentz coordinate transformations',
      'How does Carnot efficiency define the theoretical limit of heat engines?'
    ],
    socraticChallenge: {
      question: 'In an isolated physical collision between two particles with no external forces, which quantity is strictly conserved regardless of whether the collision is elastic or inelastic?',
      options: [
        { text: 'Total linear momentum (p = mv)', correct: true },
        { text: 'Total kinetic energy (KE = 1/2 mv²)', correct: false },
        { text: 'Total mechanical potential energy', correct: false },
        { text: 'Velocity of the smaller particle', correct: false }
      ],
      hints: [
        'Newton’s third law states action and reaction forces are equal and opposite (dp/dt = 0).',
        'Inelastic collisions lose kinetic energy to thermal heat and sound deformation.',
        'However, internal interactions can never alter the center-of-mass momentum.',
        'Solution: Total linear momentum is unconditionally conserved in any isolated system.'
      ],
      praise: 'Remarkably calculated! The physical equilibrium and conservation of your solution is completely sound.'
    }
  },

  keqing: {
    id: 'keqing',
    name: 'Keqing',
    title: 'Yuheng of the Liyue Qixing • Systems & Software Engineer',
    subject: 'Computer Science',
    subjectAliases: ['computer science', 'algorithms', 'data structures', 'programming', 'architecture', 'software engineering'],
    element: 'Electro',
    elementIcon: '⚡',
    color: '#c084fc',
    glowColor: 'rgba(192, 132, 252, 0.45)',
    stageBg: 'radial-gradient(circle at 50% 30%, #200d3b 0%, #0b0417 85%)',
    vignetteClass: 'electro-vignette-overlay',
    modelPath: '/assets/models/keqing/Keqing.fbx',
    modelFormat: 'fbx',
    scale: 0.010,
    cameraOffset: { x: 0, y: 0.95, z: 3.10 },
    modelOffset: { x: 0, y: 0, z: 0 },
    voice: { name: 'Samantha', pitch: 1.08, rate: 1.05 },
    defaultLine: 'Efficiency, clean invariants, and optimal algorithms. Procrastination solves zero bugs—let us trace the code to its root cause!',
    suggestedInquiries: [
      'Compare Dijkstra vs A* graph search heuristic admissible conditions',
      'Explain how LSM-trees optimize write throughput compared to B+ trees',
      'What are memory memory barrier barriers and cache coherence protocols in multi-core CPU architectures?'
    ],
    socraticChallenge: {
      question: 'Which self-balancing binary search tree guarantees strictly logarithmic O(log n) worst-case time for search, insert, and delete with at most 2 tree rotations per insertion?',
      options: [
        { text: 'Red-Black Tree', correct: true },
        { text: 'Standard Binary Search Tree', correct: false },
        { text: 'Splay Tree', correct: false },
        { text: 'Trie', correct: false }
      ],
      hints: [
        'Enforces properties: root is black, no two adjacent red nodes, equal black-height.',
        'Used in the Linux kernel virtual memory subsystem and C++ std::map.',
        'AVL trees are more rigidly height-balanced, requiring more rotations on modification.',
        'Solution: Red-Black trees guarantee O(log n) bounds with maximum 2 rotations on insert and 3 on delete.'
      ],
      praise: 'Decisive, optimal, and elegant! Time complexity O(log n), zero edge-case regressions detected!'
    }
  },

  sucrose: {
    id: 'sucrose',
    name: 'Sucrose',
    title: 'Bio-Alchemist of Favonius • Experimental Chemist & Molecular Analyst',
    subject: 'Chemistry',
    subjectAliases: ['chemistry', 'organic chemistry', 'biochemistry', 'stoichiometry', 'inorganic chemistry'],
    element: 'Anemo',
    elementIcon: '🧪',
    color: '#34d399',
    glowColor: 'rgba(52, 211, 153, 0.45)',
    stageBg: 'radial-gradient(circle at 50% 30%, #0e2e25 0%, #041410 85%)',
    vignetteClass: 'anemo-vignette-overlay',
    modelPath: '/assets/models/sucrose/Sucrose.fbx',
    modelFormat: 'fbx',
    scale: 0.010,
    cameraOffset: { x: 0, y: 0.95, z: 3.10 },
    modelOffset: { x: 0, y: 0, z: 0 },
    voice: { name: 'Samantha', pitch: 1.20, rate: 1.02 },
    defaultLine: 'H-hello! I have carefully calibrated our glassware and reaction flasks. Let’s observe the wonders of chemical bonding together!',
    suggestedInquiries: [
      'Explain Le Chatelier’s principle during exothermic gas equilibria shifts',
      'How does SN1 vs SN2 nucleophilic substitution stereochemistry differ?',
      'Calculate theoretical molar yields and limiting reagents in stoichiometry'
    ],
    socraticChallenge: {
      question: 'During an SN2 nucleophilic substitution reaction at a chiral sp³ carbon center, what stereochemical transformation characteristically occurs?',
      options: [
        { text: 'Walden inversion (complete stereochemical inversion)', correct: true },
        { text: 'Complete retention of original optical configuration', correct: false },
        { text: '50:50 racemic mixture via planar carbocation intermediate', correct: false },
        { text: 'Loss of all chirality due to radical dimerization', correct: false }
      ],
      hints: [
        'SN2 is a concerted, single-step bimolecular reaction mechanism.',
        'The nucleophile attacks from the exact opposite side (backside attack) of the leaving group.',
        'Like an umbrella blowing inside-out in a sudden gust of wind.',
        'Solution: Backside nucleophilic attack forces complete stereochemical Walden inversion.'
      ],
      praise: 'E-excellent deduction! The reaction mechanism achieved 100% stereochemical yield! ✦'
    }
  }
};

/**
 * Returns the matching character tutor for any given subject string or alias.
 */
export function getTutorBySubject(subjectName) {
  if (!subjectName) return TUTOR_REGISTRY.furina;
  const clean = subjectName.trim().toLowerCase();

  for (const [key, tutor] of Object.entries(TUTOR_REGISTRY)) {
    if (tutor.subject.toLowerCase() === clean) return tutor;
    if (tutor.subjectAliases && tutor.subjectAliases.some(alias => clean.includes(alias) || alias.includes(clean))) {
      return tutor;
    }
  }
  return TUTOR_REGISTRY.furina;
}

/**
 * Returns the matching character tutor by ID.
 */
export function getTutorById(tutorId) {
  if (!tutorId) return TUTOR_REGISTRY.furina;
  const clean = tutorId.trim().toLowerCase();
  return TUTOR_REGISTRY[clean] || TUTOR_REGISTRY.furina;
}
