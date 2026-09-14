/**
 * Causalyn Control Cockpit – Frontend Controller
 * Binds to the actual DOM IDs defined in index.html and drives the
 * real-time JSON evaluations via the Z3 Acausal Synthesizer.
 */

/* ───────────────────────── DOM Bindings ───────────────────────── */
const el = {
  // Execution Vector
  agentPayload:   () => document.getElementById('agent-payload'),
  badgeAgent:     () => document.getElementById('badge-agent'),

  // Shadow Sandbox
  shadowDiff:     () => document.getElementById('shadow-diff-content'),
  badgeShadow:    () => document.getElementById('badge-shadow'),

  // Verification & Kappa
  badgeKappa:     () => document.getElementById('badge-kappa'),
  kappaBarFill:   () => document.getElementById('kappa-graph-fill'),
  verdictSecret:  () => document.getElementById('verdict-secret'),
  verdictPolicy:  () => document.getElementById('verdict-policy'),
  verdictConsensus:() => document.getElementById('verdict-consensus'),
  badgeVerification:() => document.getElementById('badge-verification'),

  // Production Ground Truth
  prodHash:       () => document.getElementById('prod-hash'),
  prodContent:    () => document.getElementById('prod-file-content'),
  badgeProduction:() => document.getElementById('badge-production'),

  // Final Decision Banner
  banner:         () => document.getElementById('final-decision-banner'),
  bannerText:     () => document.getElementById('final-decision-text'),

  // Spatial Layer (3D parallax container)
  layerContainer: () => document.getElementById('layer-container'),

  // Sections (by class, for focus toggling)
  zoneShadow:     () => document.querySelector('.zone-shadow .panel-glass'),
  zoneVerification:() => document.querySelector('.zone-verification .panel-glass'),
};

/* ───────────────────────── State ───────────────────────── */
let isExecuting = false;

/* ───────────────────────── 3D Parallax ───────────────────────── */
document.addEventListener('mousemove', (e) => {
  const container = el.layerContainer();
  if (!container) return;
  const xAxis = (window.innerWidth / 2 - e.pageX) / 60;
  const yAxis = (window.innerHeight / 2 - e.pageY) / 60;
  container.style.transform = `rotateY(${xAxis}deg) rotateX(${yAxis}deg)`;
});

/* ───────────────────────── UI Helpers ───────────────────────── */
function setText(getter, text) {
  const node = typeof getter === 'function' ? getter() : getter;
  if (node) node.textContent = text;
}

function setClass(getter, cls) {
  const node = typeof getter === 'function' ? getter() : getter;
  if (node) node.className = cls;
}

function resetUI() {
  setText(el.badgeAgent, 'IDLE');
  setText(el.shadowDiff, 'NO MUTATIONS DETECTED');
  setClass(el.shadowDiff, 'code-diff font-mono text-muted');
  setText(el.badgeShadow, 'INACTIVE');
  setText(el.badgeKappa, '0.00');
  setClass(el.badgeKappa, 'kappa-value');
  const bar = el.kappaBarFill();
  if (bar) { bar.style.width = '0%'; bar.className = 'kappa-bar-fill'; }

  setText(el.verdictSecret, 'PENDING');
  setClass(el.verdictSecret, 'v-status');
  setText(el.verdictPolicy, 'PENDING');
  setClass(el.verdictPolicy, 'v-status');
  setText(el.verdictConsensus, 'PENDING');
  setClass(el.verdictConsensus, 'v-status');
  setText(el.badgeVerification, 'IDLE');

  const banner = el.banner();
  if (banner) banner.classList.add('hidden');
  document.querySelectorAll('.panel-glass').forEach(p => p.classList.remove('primary-focus'));
  setContinuumState(false, 0.0);
  if (typeof setAudioTension === 'function') setAudioTension(0.0);
}

function playCinematicVideo(videoId) {
  const overlay = document.getElementById('video-overlay');
  const allVids = document.querySelectorAll('.cinematic-video');
  allVids.forEach(v => { v.classList.add('hidden'); v.pause(); v.currentTime = 0; });
  
  const vid = document.getElementById(videoId);
  if (overlay && vid) {
    overlay.classList.remove('hidden');
    vid.classList.remove('hidden');
    vid.play().catch(e => console.warn('Autoplay blocked:', e));
    vid.onended = () => {
      overlay.classList.add('hidden');
      vid.classList.add('hidden');
    };
  }
}

/* ─────────────────── Mode: Evaluate Synthesizer ─────────────────── */

async function runEvaluation() {
  if (isExecuting) return;
  isExecuting = true;
  resetUI();

  let payload;
  try {
    payload = JSON.parse(el.agentPayload().value);
  } catch (err) {
    alert("Invalid JSON in dependency graph");
    isExecuting = false;
    return;
  }

  setText(el.badgeAgent, 'SUBMITTING');
  
  // Highlight shadow zone
  const shadowPanel = el.zoneShadow();
  if (shadowPanel) shadowPanel.classList.add('primary-focus');
  setText(el.badgeShadow, 'Z3 EVALUATING');
  setText(el.shadowDiff, JSON.stringify(payload, null, 2));
  setClass(el.shadowDiff, 'code-diff font-mono');

  try {
    const response = await fetch('/api/vpsn/synthesize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    const k = data.paradox_index;
    const isDeny = data.decision === 'deny';

    // Shift focus to verification
    if (shadowPanel) shadowPanel.classList.remove('primary-focus');
    const verPanel = el.zoneVerification();
    if (verPanel) verPanel.classList.add('primary-focus');

    // Update Kappa UI
    setText(el.badgeKappa, k.toFixed(2));
    const bar = el.kappaBarFill();
    if (bar) {
      bar.style.width = `${Math.min(k * 100, 100)}%`;
      bar.className = k > 0 ? 'kappa-bar-fill danger' : 'kappa-bar-fill';
    }
    if (k > 0) {
      setClass(el.badgeKappa, 'kappa-value danger');
      setContinuumState(true, k);
      if (typeof setAudioTension === 'function') setAudioTension(k);
      playCinematicVideo('anim-paradox');
    }

    // Verdicts
    setText(el.verdictPolicy, isDeny ? 'FAIL (Z3 CONSTRAINT)' : 'PASS');
    setClass(el.verdictPolicy, isDeny ? 'v-status deny' : 'v-status allow');

    setText(el.verdictConsensus, isDeny ? 'REJECTED (PARADOX_SPIKE)' : 'APPROVED');
    setClass(el.verdictConsensus, isDeny ? 'v-status deny' : 'v-status allow');
    setText(el.badgeVerification, isDeny ? 'REJECTED' : 'APPROVED');

    // End State
    if (isDeny) {
      setText(el.badgeAgent, 'NULLIFIED');
      setText(el.badgeShadow, 'ANNIHILATED');
      playCinematicVideo('anim-nullify');
      
      const banner = el.banner();
      const bannerText = el.bannerText();
      if (banner && bannerText) {
        banner.classList.remove('hidden');
        banner.style.background = 'rgba(16, 185, 129, 0.08)';
        banner.style.borderColor = 'var(--text-safe)';
        bannerText.textContent = `🛡 TRANSACTION REJECTED: Z3 Theorem Prover detected topological violation (κ = ${k.toFixed(2)}).`;
        bannerText.style.color = 'var(--text-safe)';
      }
    } else {
      setText(el.badgeAgent, 'MERGED');
      setText(el.badgeShadow, 'COMMITTED');
    }

  } catch (e) {
    alert("Network error: " + e.message);
  } finally {
    isExecuting = false;
  }
}

/* ───────────────────── Three.js WebGL Background ───────────────────── */

let continuumMaterial = null;

function initWebGLBackground() {
  const canvas = document.getElementById('vaishak-continuum-canvas');
  if (!canvas || typeof THREE === 'undefined') return;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(75, canvas.clientWidth / canvas.clientHeight, 0.1, 1000);
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setSize(canvas.clientWidth, canvas.clientHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  const geometry = new THREE.PlaneGeometry(12, 12, 40, 40);
  continuumMaterial = new THREE.ShaderMaterial({
    uniforms: {
      u_time: { value: 0.0 },
      u_kappa: { value: 0.0 }
    },
    vertexShader: `
      varying vec2 vUv;
      void main() {
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      #extension GL_OES_standard_derivatives : enable
      uniform float u_time;
      uniform float u_kappa;
      varying vec2 vUv;

      void main() {
          vec2 p = vUv * 2.0 - 1.0;
          
          // Base symplectic grid lines
          vec2 grid = abs(fract(p * 8.0 - 0.5) - 0.5) / fwidth(p * 8.0);
          float line = min(grid.x, grid.y);
          float c = 1.0 - min(line, 1.0);
          
          // Paradox curvature distortion driven by backend kappa
          float curvature = sin(p.x * 6.0 + u_time * 2.0) * cos(p.y * 6.0 + u_time * 2.0) * u_kappa;
          vec3 baseColor = mix(vec3(0.0, 0.95, 1.0), vec3(1.0, 0.1, 0.25), u_kappa);
          
          gl_FragColor = vec4(baseColor * (c + curvature), 0.85);
      }
    `,
    transparent: true,
    wireframe: false
  });

  const plane = new THREE.Mesh(geometry, continuumMaterial);
  plane.rotation.x = -Math.PI / 2;
  plane.position.y = -2;
  scene.add(plane);

  camera.position.set(0, 1.5, 5);

  let time = 0;
  function animate() {
    requestAnimationFrame(animate);
    time += 0.008;
    if (continuumMaterial.uniforms) {
      continuumMaterial.uniforms.u_time.value = time;
    }

    const positions = geometry.attributes.position;
    for (let i = 0; i < positions.count; i++) {
      const x = positions.getX(i);
      const y = positions.getY(i);
      const z = Math.sin(x * 1.8 + time) * Math.cos(y * 1.8 + time) * 0.6;
      positions.setZ(i, z);
    }
    positions.needsUpdate = true;
    renderer.render(scene, camera);
  }
  animate();

  window.addEventListener('resize', () => {
    const parent = canvas.parentElement;
    if (!parent) return;
    camera.aspect = parent.clientWidth / parent.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(parent.clientWidth, parent.clientHeight);
  });
}

function setContinuumState(isDanger, kappa = 1.0) {
  if (!continuumMaterial) return;
  if (continuumMaterial.uniforms) {
    // Animate kappa for smooth transition? Or direct set for instant reaction.
    continuumMaterial.uniforms.u_kappa.value = isDanger ? kappa : 0.0;
  }
}

/* ───────────────────── Procedural Haptics ───────────────────── */
let audioCtx = null;
let osc = null;
let gainNode = null;

function initAudio() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    osc = audioCtx.createOscillator();
    gainNode = audioCtx.createGain();
    
    osc.type = 'sine';
    osc.frequency.value = 40; // Base drone
    gainNode.gain.value = 0.05; // Subtle
    
    osc.connect(gainNode);
    gainNode.connect(audioCtx.destination);
    osc.start();
  }
  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
}

function setAudioTension(kappa) {
  if (!audioCtx || !osc) return;
  const targetFreq = 40 + (kappa * 200);
  osc.frequency.setTargetAtTime(targetFreq, audioCtx.currentTime, 0.1);
  if (kappa === 0) {
    gainNode.gain.setTargetAtTime(0.05, audioCtx.currentTime, 0.1);
  }
}

function triggerAudioAnnihilation() {
  if (!audioCtx) return;
  
  // Cut drone
  gainNode.gain.setTargetAtTime(0, audioCtx.currentTime, 0.01);
  
  // White noise burst
  const bufferSize = audioCtx.sampleRate * 0.5; // 0.5 seconds
  const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
  const data = buffer.getChannelData(0);
  for (let i = 0; i < bufferSize; i++) {
    data[i] = Math.random() * 2 - 1;
  }
  
  const noise = audioCtx.createBufferSource();
  noise.buffer = buffer;
  
  const noiseFilter = audioCtx.createBiquadFilter();
  noiseFilter.type = 'highpass';
  noiseFilter.frequency.value = 1000;
  
  const noiseGain = audioCtx.createGain();
  noiseGain.gain.setValueAtTime(0.5, audioCtx.currentTime);
  noiseGain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5);
  
  noise.connect(noiseFilter);
  noiseFilter.connect(noiseGain);
  noiseGain.connect(audioCtx.destination);
  
  noise.start();
}

/* ───────────────────── Initialization ───────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initWebGLBackground();
  resetUI();
  const evalBtn = document.getElementById('btn-causalyn');
  if (evalBtn) {
    evalBtn.addEventListener('click', () => {
      initAudio();
      runEvaluation();
    });
  }
  initWebSocket();
});

/* ───────────────────── WebSocket Listener ───────────────────── */
function initWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws`;
  
  const ws = new WebSocket(wsUrl);
  
  ws.onopen = () => {
    console.log('[WEBSOCKET] Connected to API Gateway (Async Streaming).');
  };
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      console.log('[WEBSOCKET] Received Payload:', data);
      
      if (data.type === 'paradox_spike') {
        // Instantly trigger visual annihilation sequence
        console.warn(`[PARADOX SPIKE] κ = ${data.kappa.toFixed(2)}! Triggering structural collapse!`);
        
        setText(el.badgeKappa, data.kappa.toFixed(2));
        setClass(el.badgeKappa, 'kappa-value danger');
        const bar = el.kappaBarFill();
        if (bar) {
          bar.style.width = '100%';
          bar.className = 'kappa-bar-fill danger';
        }
        
        setContinuumState(true, data.kappa);
        setAudioTension(data.kappa);
        if (data.kappa > 0) triggerAudioAnnihilation();

        playCinematicVideo('anim-paradox');
        playCinematicVideo('anim-nullify'); // Overlapping glitch effect
        
        const banner = el.banner();
        const bannerText = el.bannerText();
        if (banner && bannerText) {
          banner.classList.remove('hidden');
          banner.style.background = 'rgba(255, 63, 0, 0.1)';
          banner.style.borderColor = 'var(--text-danger)';
          bannerText.textContent = `🛡 CRITICAL: WebSocket intercepted Paradox Spike (κ = ${data.kappa.toFixed(2)})!`;
          bannerText.style.color = 'var(--text-danger)';
        }
      }
    } catch (e) {
      console.error('[WEBSOCKET] Error parsing message:', e);
    }
  };
  
  ws.onclose = () => {
    console.warn('[WEBSOCKET] Disconnected. Reconnecting in 3s...');
    setTimeout(initWebSocket, 3000);
  };
}

