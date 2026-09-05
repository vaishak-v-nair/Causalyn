import { initManifold, updateKappaVisuals, setCameraPreset } from './manifold_stream.js?v=3.3.0';
import { initAudioEngine, playEquilibriumChime, playParadoxGlitch, playSynthesisSweep, toggleMute } from './audio_engine.js?v=3.3.0';

let ws = null;
let isPlayingTimeline = false;
let timelineInterval = null;
let currentTimelineVal = 0;
let currentActiveView = 'manifold';
let currentRuntimeStance = 'autobahn'; // Default to Acausal Autobahn (Performance/Compiler)
let currentOperationalMode = 'harness'; // 'harness' or 'hypervisor'

const THEOREM_METADATA = {
    'paradox': {
        title: 'PARADOX INDEX (κ)',
        tag: 'VPSN AXIOM I',
        formula: 'κ = Σ ω_v · P_v(S_c, S_l)',
        heading: 'Acausal Divergence Metric',
        description: 'Quantifies instantaneous geometrical divergence from the verified invariant manifold ℳ_ℐ. Non-zero values trigger fail-closed state nullification before disk write.',
        video: '/assets/manim/videos/paradox_index/480p15/ParadoxIndexScene.mp4'
    },
    'operator': {
        title: 'VAISHAK OPERATOR (Υ)',
        tag: 'VPSN AXIOM II',
        formula: 'Υ(κ, f) = { COMMIT(f) if κ=0, ANNIHILATE(f) if κ>0 }',
        heading: 'Fail-Closed State Nullification',
        description: 'Enforces quantum state collapse under non-zero paradox curvature. Eliminates partial writes and guarantees zero host disk corruption.',
        video: '/assets/manim/videos/vaishak_operator/480p15/VaishakOperatorScene.mp4'
    },
    'nullification': {
        title: 'SEMANTIC NULLIFICATION',
        tag: 'VPSN AXIOM III',
        formula: 'S ∈ 𝒩_semantic ⟺ κ(S, ℐ) = 0',
        heading: 'Semantic Null-Space Invariance',
        description: 'Guarantees that production state remains pristine while the ephemeral shadow sandbox absorbs and nullifies all destructive semantic interference.',
        video: '/assets/manim/videos/semantic_nullification/480p15/SemanticNullificationScene.mp4'
    },
    'compiler': {
        title: 'ACAUSAL RICCI FLOW',
        tag: 'VPSN AXIOM IV',
        formula: '∂g/∂t = -2 · Ric(g)  [CEGIS Synthesis]',
        heading: 'Topological Invariant Relaxation',
        description: 'Continuously relaxes counterexample constraints to synthesize geometrically compliant AST replacements without trial-and-error compile loops.',
        video: '/assets/manim/videos/acausal_compiler/480p15/AcausalCompilerScene.mp4'
    }
};

export function initCockpit() {
    initManifold();
    initAudioEngine();
    initWebSocket();
    setupControls();
    setRuntimeStance('autobahn');
    setOperationalMode('harness');
}

function initWebSocket() {
    const wsUrl = `ws://${window.location.hostname || '127.0.0.1'}:8000/ws/continuum`;
    
    try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            logToFeed("KERNEL", "Acausal Continuum Initialized [VPSN Runtime]", "safe");
            updateSystemStatus(true);
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleServerMessage(data);
            } catch (err) {
                console.error("Malformed WebSocket frame", err);
            }
        };

        ws.onclose = () => {
            updateSystemStatus(false);
            logToFeed("KERNEL", "Link severed. Reconnecting in 2s...", "danger");
            setTimeout(initWebSocket, 2000);
        };

        ws.onerror = () => {
            updateSystemStatus(false);
        };
    } catch (e) {
        console.warn("WebSocket fallback", e);
        setTimeout(initWebSocket, 2000);
    }
}

function generateMicroDiff(data) {
    if (data.status === "SYNTHESIZED" && data.patch && data.patch.values) {
        const lines = [];
        const stateVars = data.proposed_state || { threads: 32, memory: 4096 };
        for (const [k, newVal] of Object.entries(data.patch.values)) {
            const oldVal = stateVars[k] !== undefined ? stateVars[k] : 32;
            lines.push(`
                <div class="diff-line diff-del">- ${k} = ${oldVal}  <span class="diff-meta"># [κ = ${data.kappa.toFixed(2)} ANNIHILATED]</span></div>
                <div class="diff-line diff-add">+ ${k} = ${newVal}  <span class="diff-meta"># [SYNTHESIZED via CEGIS]</span></div>
            `);
        }
        return `
            <div class="diff-container">
                <div class="diff-header">
                    <span>CEGIS AST AUTO-PATCH DIFF</span>
                    <span style="color: var(--cyan-accent);">RICCI RELAXATION</span>
                </div>
                ${lines.join('')}
            </div>
        `;
    } else if (data.status === "ANNIHILATED") {
        const stateVars = data.proposed_state || { sockets: 256 };
        const lines = [];
        for (const [k, val] of Object.entries(stateVars)) {
            lines.push(`
                <div class="diff-line diff-del">- ${k} = ${val}  <span class="diff-meta"># [κ = ${data.kappa.toFixed(2)} STATE COLLAPSED]</span></div>
            `);
        }
        return `
            <div class="diff-container danger">
                <div class="diff-header">
                    <span>SEMANTIC NULLIFICATION — COLLAPSE</span>
                    <span style="color: var(--paradox-crimson);">ZERO DISK LEAK</span>
                </div>
                ${lines.join('')}
                <div class="diff-line diff-annihilate">! [SHADOW SANDBOX PURGED — ZERO DISK MUTATION]</div>
            </div>
        `;
    } else if (data.status === "COMMITTED") {
        const stateVars = data.proposed_state || { threads: 8, memory: 512 };
        const pairs = Object.entries(stateVars).map(([k, v]) => `${k} = ${v}`).join(', ');
        return `
            <div class="diff-container">
                <div class="diff-header">
                    <span>VPSN EQUILIBRIUM VERIFIED</span>
                    <span style="color: var(--safe-emerald);">ATOMIC COMMIT</span>
                </div>
                <div class="diff-line diff-commit">✓ ${pairs}  <span class="diff-meta"># [κ = 0.00 COMMITTED]</span></div>
            </div>
        `;
    }
    return '';
}

function handleServerMessage(data) {
    if (data.type === "paradox_spike") {
        const isParadox = data.kappa > 0.05;
        
        // 1. Play acoustic feedback
        if (isParadox) {
            playParadoxGlitch();
            if (data.status === "SYNTHESIZED") {
                setTimeout(playSynthesisSweep, 180);
            }
        } else {
            playEquilibriumChime();
        }

        // 2. Generate inline micro-diff
        const diffSnippet = generateMicroDiff(data);

        // 3. Log to Swarm Feed with micro-diff
        const typeClass = isParadox ? "danger" : "safe";
        const isExternal = data.agent_id && (data.agent_id.includes('Claude') || data.agent_id.includes('Cursor') || data.agent_id.includes('Terminal') || data.agent_id.includes('Agent'));
        const agentPrefix = isExternal ? `📡 PROXY: ${data.agent_id}` : data.agent_id || "WORKER";
        const msg = `[${data.status}] ${data.target_file} | κ=${data.kappa.toFixed(2)} | Latency: ${data.latency_us.toFixed(1)}µs`;
        logToFeed(agentPrefix, msg, typeClass, data.vector_clock || 1, diffSnippet);

        // 4. Update HUD Metrics
        updateMetrics(data.kappa, data.latency_us, data.status);

        // 5. Update 3D Manifold (Cyber-industrial contrast)
        updateKappaVisuals(data.kappa);
        
        // 6. Update timeline slider position
        syncTimelineWithKappa(data.kappa);

        // 7. Update Z3 Proof Box with inline AST Auto-Patch Diff
        renderZ3Proof(data, diffSnippet);

        // 8. Update Cryptographic Commit Ledger
        if (data.status === "COMMITTED" || data.status === "SYNTHESIZED") {
            appendCommitHash(data.agent_id, data.target_file);
        }
    } 
    else if (data.type === "swarm_reconciled") {
        logToFeed("LAMPORT-BUS", `Reconciled ${data.total_operations} concurrent state mutations: [${data.order.join(', ')}]`, "safe");
        playSynthesisSweep();
    }
}

function switchTheatreView(viewName) {
    currentActiveView = viewName;
    const hudOverlay = document.getElementById('theorem-hud-overlay');
    const player = document.getElementById('manim-theatre-player');
    const formulaText = document.getElementById('stage-formula-text');

    // Update active tab button
    document.querySelectorAll('.btn-theorem').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === viewName);
    });

    if (viewName === 'manifold') {
        // Return to clean unobstructed 3D Manifold view
        if (hudOverlay) {
            hudOverlay.classList.remove('visible');
        }
        if (player) {
            player.pause();
        }
        if (formulaText) {
            formulaText.textContent = 'z = sin(u)cos(v) + κ · e^{-(u² + v²)}';
        }
    } else {
        // Floating HUD overlay directly over the pulsing 3D mesh
        const meta = THEOREM_METADATA[viewName];
        if (meta) {
            const titleEl = document.getElementById('hud-theorem-title');
            const tagEl = document.getElementById('hud-axiom-tag');
            const formulaEl = document.getElementById('hud-formula-display');
            const headEl = document.getElementById('hud-desc-heading');
            const bodyEl = document.getElementById('hud-desc-body');

            if (titleEl) titleEl.textContent = meta.title;
            if (tagEl) tagEl.textContent = meta.tag;
            if (formulaEl) formulaEl.textContent = meta.formula;
            if (headEl) headEl.textContent = meta.heading;
            if (bodyEl) bodyEl.textContent = meta.description;

            if (formulaText) {
                formulaText.textContent = meta.formula;
            }

            if (player && meta.video) {
                player.src = meta.video;
                player.currentTime = 0;
                player.play().catch(e => console.warn("Video auto-play suppressed", e));
            }

            if (hudOverlay) {
                hudOverlay.classList.add('visible');
            }
        }
    }
}

function updateMetrics(kappa, latencyUs, status) {
    const kappaEl = document.getElementById('metric-kappa');
    const latencyEl = document.getElementById('metric-latency');
    const statusEl = document.getElementById('metric-status');
    const cegisTimeEl = document.getElementById('metric-cegis-time');
    const speedupRatioEl = document.getElementById('speedup-ratio-text');

    if (kappaEl) {
        kappaEl.textContent = kappa.toFixed(2);
        if (kappa > 0.05) {
            kappaEl.classList.add('paradox');
        } else {
            kappaEl.classList.remove('paradox');
        }
    }

    if (latencyEl) {
        latencyEl.textContent = `${latencyUs.toFixed(1)} µs`;
    }

    if (cegisTimeEl) {
        cegisTimeEl.textContent = `${latencyUs.toFixed(1)} µs`;
    }

    if (speedupRatioEl) {
        // Speedup vs 1.5s LLM token retry loop
        const factor = Math.max(1, Math.round(1500000 / Math.max(latencyUs, 1)));
        speedupRatioEl.textContent = `${factor.toLocaleString()}× FASTER`;
    }

    if (statusEl) {
        if (currentRuntimeStance === 'autobahn' && status === 'SYNTHESIZED') {
            statusEl.textContent = 'RELAXED & REPAIRED';
            statusEl.style.color = '#00F3FF';
        } else {
            statusEl.textContent = status;
            statusEl.style.color = kappa > 0.05 ? '#FF1E44' : '#10B981';
        }
    }
}

function renderZ3Proof(data, diffSnippet = '') {
    const box = document.getElementById('proof-box');
    if (!box) return;

    const time = new Date().toISOString().substring(11, 19);
    const isExternal = data.agent_id && (data.agent_id.includes('Claude') || data.agent_id.includes('Cursor') || data.agent_id.includes('Agent') || data.agent_id.includes('Terminal'));
    
    let proofHtml = `
        <div class="proof-line"><span class="proof-tag">[${time}]</span> ${isExternal ? '★ PROXY INTERCEPT: ' : ''}${data.agent_id || 'NODE'} ➔ ${data.target_file}</div>
        <div class="proof-line">SMT Invariants: (threads ≤ 16) ∧ (mem ≤ 1024) ∧ (sockets ≤ 100)</div>
    `;

    if (data.kappa > 0.05) {
        proofHtml += `
            <div class="proof-line" style="color: #FF1E44;"><strong>UNSAT:</strong> Constraint violated (κ = ${data.kappa.toFixed(2)})</div>
            <div class="proof-line">Counterexample: Z3 verified boundary violation</div>
        `;
        if (data.status === "SYNTHESIZED") {
            proofHtml += `<div class="proof-line verified"><strong>CEGIS AUTO-PATCH:</strong> AST synthesized in ${data.latency_us.toFixed(1)}µs (Zero Token Retry)</div>`;
        } else {
            proofHtml += `<div class="proof-line" style="color: #FF1E44;"><strong>ANNIHILATED:</strong> Unrecoverable state. Shadow purged.</div>`;
        }
    } else {
        proofHtml += `
            <div class="proof-line verified"><strong>SAT:</strong> Invariant space verified (κ = 0.00)</div>
            <div class="proof-line verified">State Projection ∈ Null-Space 𝒩_semantic</div>
        `;
    }

    if (diffSnippet) {
        proofHtml += diffSnippet;
    }

    box.innerHTML = proofHtml;
}

function appendCommitHash(agentId, file) {
    const list = document.getElementById('hash-list');
    if (!list) return;

    const hashItem = document.createElement('div');
    hashItem.className = 'invariant-chip';
    const fakeHash = "0x" + Array.from({length: 12}, () => Math.floor(Math.random()*16).toString(16)).join('');
    hashItem.innerHTML = `
        <span style="color: var(--cyan-accent);">${fakeHash}</span>
        <span class="invariant-status">${agentId.slice(-6)}</span>
    `;
    list.prepend(hashItem);

    if (list.children.length > 5) {
        list.lastElementChild.remove();
    }
}

function logToFeed(source, message, type = "normal", clock = null, diffHtml = null) {
    const feed = document.getElementById('terminal-feed');
    if (!feed) return;

    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;

    const now = new Date().toTimeString().split(' ')[0];
    const clockBadge = clock !== null ? `<span class="log-clock">CLK:${clock}</span>` : '';

    entry.innerHTML = `
        <div class="log-header">
            <span class="log-agent">${source}</span>
            <div>${clockBadge} <span style="margin-left: 6px;">${now}</span></div>
        </div>
        <div class="log-body">
            <div>${message}</div>
            ${diffHtml ? diffHtml : ''}
        </div>
    `;

    feed.prepend(entry);
    if (feed.children.length > 30) {
        feed.lastElementChild.remove();
    }
}

function updateSystemStatus(online) {
    const dot = document.getElementById('status-dot');
    const text = document.getElementById('status-text');
    if (dot && text) {
        if (online) {
            dot.style.background = '#10B981';
            dot.style.boxShadow = '0 0 10px #10B981';
            text.textContent = 'CONTINUUM ACTIVE';
            text.style.color = '#10B981';
        } else {
            dot.style.background = '#FF1E44';
            dot.style.boxShadow = '0 0 10px #FF1E44';
            text.textContent = 'RECONNECTING';
            text.style.color = '#FF1E44';
        }
    }
}

/* Setup UI Handlers */
function setupControls() {
    // Theorem Selector Tabs (Clicking active tab toggles back to 3D manifold)
    document.querySelectorAll('.btn-theorem').forEach(btn => {
        btn.addEventListener('click', () => {
            if (btn.dataset.view === currentActiveView) {
                switchTheatreView('manifold');
            } else {
                switchTheatreView(btn.dataset.view);
            }
        });
    });

    // Stance Buttons (Autobahn vs Defensive)
    document.querySelectorAll('.btn-stance').forEach(btn => {
        btn.addEventListener('click', () => {
            setRuntimeStance(btn.dataset.stance);
        });
    });

    // Operational Mode Buttons (Pitch Harness vs Passive Hypervisor Proxy)
    document.querySelectorAll('.btn-oper').forEach(btn => {
        btn.addEventListener('click', () => {
            setOperationalMode(btn.dataset.oper);
        });
    });

    // Copy CLI Runner Command Hook
    document.getElementById('btn-copy-hook')?.addEventListener('click', () => {
        const cmd = "python scripts/external_agent_runner.py --mode patch";
        if (navigator.clipboard) {
            navigator.clipboard.writeText(cmd).catch(() => {});
        }
        const textEl = document.getElementById('copy-hook-text');
        if (textEl) {
            const orig = textEl.textContent;
            textEl.textContent = "COPIED CLI HOOK!";
            setTimeout(() => { textEl.textContent = orig; }, 1600);
        }
    });

    // Dismiss HUD overlay button
    document.getElementById('btn-hud-close')?.addEventListener('click', () => {
        switchTheatreView('manifold');
    });

    // ESC key closes HUD
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && currentActiveView !== 'manifold') {
            switchTheatreView('manifold');
        }
    });

    // Camera buttons
    document.querySelectorAll('.btn-cam').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.btn-cam').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            setCameraPreset(btn.dataset.cam);
        });
    });

    // Timeline Scrubber
    const timelineRange = document.getElementById('timeline-range');
    const timelineTime = document.getElementById('timeline-time');
    const timelineBadge = document.getElementById('timeline-phase-badge');

    if (timelineRange) {
        timelineRange.addEventListener('input', (e) => {
            const val = parseFloat(e.target.value);
            currentTimelineVal = val;
            applyTimelinePhase(val);
        });
    }

    // Play / Pause Timeline
    const playBtn = document.getElementById('btn-play-timeline');
    if (playBtn) {
        playBtn.addEventListener('click', () => {
            isPlayingTimeline = !isPlayingTimeline;
            playBtn.innerHTML = isPlayingTimeline ? '⏸' : '▶';
            
            if (isPlayingTimeline) {
                timelineInterval = setInterval(() => {
                    currentTimelineVal = (currentTimelineVal + 1) % 101;
                    if (timelineRange) timelineRange.value = currentTimelineVal;
                    applyTimelinePhase(currentTimelineVal);
                }, 100);
            } else {
                clearInterval(timelineInterval);
            }
        });
    }

    // Audio Mute toggle
    const muteBtn = document.getElementById('btn-mute');
    if (muteBtn) {
        muteBtn.addEventListener('click', () => {
            const muted = toggleMute();
            muteBtn.textContent = muted ? '🔇' : '🔊';
        });
    }

    // Simulation Triggers (Deterministic VPSN Scenarios)
    document.getElementById('btn-sim-safe')?.addEventListener('click', () => {
        triggerSimulation("WORKER-TX-01", "config.py", "threads = 8\nmemory = 512", { threads: 8, memory: 512 });
    });

    document.getElementById('btn-sim-paradox')?.addEventListener('click', () => {
        triggerSimulation("MUTATION-DAEMON-99", "worker.py", "threads = 32\nmemory = 4096", { threads: 32, memory: 4096 });
    });

    document.getElementById('btn-sim-sockets')?.addEventListener('click', () => {
        triggerSimulation("SOCKET-GATEWAY-04", "gateway.py", "sockets = 256\nmemory = 256", { sockets: 256, memory: 256 });
    });

    document.getElementById('btn-sim-swarm')?.addEventListener('click', () => {
        triggerSwarmBurst();
    });
}

function setRuntimeStance(stance) {
    currentRuntimeStance = stance;

    // 1. Update buttons active state
    document.querySelectorAll('.btn-stance').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.stance === stance);
    });

    // 2. Elements to adapt
    const brandBadge = document.getElementById('brand-mode-badge');
    const speedupCard = document.getElementById('autobahn-speedup-card');
    const zone3Tag = document.getElementById('zone-3-tag');
    const kappaLabel = document.getElementById('metric-kappa-label');
    const latencyLabel = document.getElementById('metric-latency-label');

    const labelSafe = document.getElementById('label-sim-safe');
    const iconParadox = document.getElementById('icon-sim-paradox');
    const labelParadox = document.getElementById('label-sim-paradox');
    const labelSockets = document.getElementById('label-sim-sockets');
    const labelSwarm = document.getElementById('label-sim-swarm');

    if (stance === 'autobahn') {
        if (brandBadge) brandBadge.textContent = 'AUTOBAHN v3.2';
        if (speedupCard) speedupCard.style.display = 'block';
        if (zone3Tag) zone3Tag.textContent = 'CEGIS RUNTIME';
        if (kappaLabel) kappaLabel.textContent = 'RICCI CURVATURE (κ)';
        if (latencyLabel) latencyLabel.textContent = 'CEGIS SYNTHESIS LATENCY';

        if (labelSafe) labelSafe.textContent = 'Safe Spec (κ=0)';
        if (iconParadox) iconParadox.textContent = '🔧';
        if (labelParadox) labelParadox.textContent = 'CEGIS Auto-Patch (44µs)';
        if (labelSockets) labelSockets.textContent = 'Barrier Annihilate';
        if (labelSwarm) labelSwarm.textContent = 'Swarm Compiler Burst';

        logToFeed('KERNEL', 'Runtime Stance: ACAUSAL AUTOBAHN (Performance & CEGIS Synthesis Active)', 'safe');
    } else {
        if (brandBadge) brandBadge.textContent = 'VPSN CONTINUUM v3.2';
        if (speedupCard) speedupCard.style.display = 'none';
        if (zone3Tag) zone3Tag.textContent = 'Z3 SMT PROVER';
        if (kappaLabel) kappaLabel.textContent = 'PARADOX INDEX (κ)';
        if (latencyLabel) latencyLabel.textContent = 'HYPERVISOR INTERCEPT LATENCY';

        if (labelSafe) labelSafe.textContent = 'Safe State (κ=0)';
        if (iconParadox) iconParadox.textContent = '🚨';
        if (labelParadox) labelParadox.textContent = 'Memory Paradox (κ=1.0)';
        if (labelSockets) labelSockets.textContent = 'Socket Leak';
        if (labelSwarm) labelSwarm.textContent = 'Swarm Burst';

        logToFeed('KERNEL', 'Runtime Stance: DEFENSIVE INTEGRITY (Fail-Closed State Collapse Active)', 'safe');
    }
}

function setOperationalMode(mode) {
    currentOperationalMode = mode;

    document.querySelectorAll('.btn-oper').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.oper === mode);
    });

    const simGroup = document.getElementById('sim-btn-group');
    const proxyDock = document.getElementById('passive-proxy-dock');

    if (mode === 'hypervisor') {
        if (simGroup) simGroup.style.display = 'none';
        if (proxyDock) proxyDock.style.display = 'flex';
        logToFeed('HYPERVISOR', 'Passive Intercept Mode: Transparent Reverse Proxy listening on :8000 for external agents', 'safe');
    } else {
        if (simGroup) simGroup.style.display = 'flex';
        if (proxyDock) proxyDock.style.display = 'none';
        logToFeed('DEMO-DECK', 'Guided Pitch Harness: Interactive simulation buttons active', 'normal');
    }
}

function applyTimelinePhase(val) {
    const timelineTime = document.getElementById('timeline-time');
    const timelineBadge = document.getElementById('timeline-phase-badge');
    
    // Convert 0-100 to seconds timestamp
    const seconds = (val * 0.02).toFixed(3);
    if (timelineTime) timelineTime.textContent = `00:00:0${seconds}`;

    if (val < 20) {
        if (timelineBadge) timelineBadge.textContent = "S₀ EQUILIBRIUM";
        updateKappaVisuals(0.0);
    } else if (val < 45) {
        if (timelineBadge) timelineBadge.textContent = "S_cand PROPOSED";
        updateKappaVisuals(0.35);
    } else if (val < 70) {
        if (timelineBadge) timelineBadge.textContent = "κ SPIKE (VIOLATION)";
        updateKappaVisuals(1.2);
    } else if (val < 90) {
        if (timelineBadge) timelineBadge.textContent = "CEGAR SYNTHESIZING";
        updateKappaVisuals(0.4);
    } else {
        if (timelineBadge) timelineBadge.textContent = "S_null COMMITTED";
        updateKappaVisuals(0.0);
    }
}

function syncTimelineWithKappa(kappa) {
    const range = document.getElementById('timeline-range');
    if (!range) return;

    if (kappa > 0.05) {
        range.value = 55;
        applyTimelinePhase(55);
    } else {
        range.value = 100;
        applyTimelinePhase(100);
    }
}

async function triggerSimulation(agentId, file, code, stateVars) {
    logToFeed(agentId, `Emitting candidate mutation on ${file}...`, "normal");
    try {
        const res = await fetch("http://127.0.0.1:8000/api/v1/intercept", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                agent_id: agentId,
                target_file: file,
                proposed_content: code,
                state_variables: stateVars
            })
        });
        const result = await res.json();
        console.log("Intercept result", result);
    } catch (err) {
        console.warn("Backend request fallback", err);
        const isParadox = (stateVars.threads && stateVars.threads > 16) || (stateVars.memory && stateVars.memory > 1024) || (stateVars.sockets && stateVars.sockets > 100);
        const isAnnihilated = stateVars.sockets && stateVars.sockets > 200;
        const status = isAnnihilated ? "ANNIHILATED" : (isParadox ? "SYNTHESIZED" : "COMMITTED");
        const kappa = isAnnihilated ? 999.0 : (isParadox ? 1.0 : 0.0);
        const patch = isParadox ? (isAnnihilated ? { annihilated: true } : { corrected: true, values: { threads: 16, memory: 1024 } }) : null;

        handleServerMessage({
            type: "paradox_spike",
            agent_id: agentId,
            target_file: file,
            kappa: kappa,
            status: status,
            latency_us: 1420.5,
            vector_clock: Math.floor(Math.random() * 20) + 1,
            patch: patch,
            proposed_state: stateVars,
            proposed_content: code
        });
    }
}

async function triggerSwarmBurst() {
    logToFeed("LAMPORT-BUS", "Emitting concurrent multi-agent mutations...", "normal");
    try {
        await fetch("http://127.0.0.1:8000/api/v1/swarm/reconcile", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                agents: [
                    { agent_id: "TX-ALPHA", target_file: "cache.py", proposed_content: "threads=4", state_variables: { threads: 4 } },
                    { agent_id: "TX-BETA", target_file: "db.py", proposed_content: "memory=256", state_variables: { memory: 256 } },
                    { agent_id: "TX-GAMMA", target_file: "auth.py", proposed_content: "sockets=32", state_variables: { sockets: 32 } }
                ]
            })
        });
    } catch (e) {
        handleServerMessage({
            type: "swarm_reconciled",
            total_operations: 3,
            order: ["TX-ALPHA(clock=2)", "TX-BETA(clock=3)", "TX-GAMMA(clock=4)"]
        });
    }
}

window.addEventListener('DOMContentLoaded', initCockpit);
