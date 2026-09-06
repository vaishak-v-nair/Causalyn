---
name: skeli-skills
description: >-
  A massive, serious intelligence skill utilizing Self-Reflective Reinforcement Learning (SRRL). 
  Governs advanced AI web development, autonomous DOM analysis, anti-pattern avoidance, 
  and ultra-premium UI/UX design heuristics based on "Unknown Intelligence" guidelines.
---

# Skeli-Skills: The AI SRRL UI/UX Intelligence Engine

This is not a simple checklist. This is a **Self-Reflective Reinforcement Learning (SRRL)** instruction protocol. As an AI Agent, you MUST obey these operational heuristics. This document grows by capturing past AI mistakes, enforcing defensive UI architecture, and demanding self-falsification before writing code.

---

## 1. The SRRL Operational Protocol (MANDATORY)

Before rendering UI or making structural layout changes, you must engage in Self-Reflection:
1. **Introspection Phase:** Mentally simulate the DOM rendering of your code. Ask: "What happens if this container expands? Will `overflow-x-hidden` on a parent break `position: sticky` on a child? Are there any hidden 4000px gaps? Will a fixed height overflow on 900px vertical viewports?"
2. **Critique & Falsification:** Try to break your own design. Identify edge cases (laptop screens at 1920x945, ultra-wide monitors, missing backend connections, streaming token overflow, long variable names).
3. **Execution & Web Scraping:** After writing UI, you MUST utilize the `browser_subagent` to visually verify the layout. Do not trust your code output alone. If the screenshot reveals an error (e.g., clipped panels, scrollbar inside scrollbar, broken canvas pointer events), you must extract DOM nodes, reflect on the mismatch, and repair it.
4. **No Placeholders:** Never generate generic `[Content goes here]` filler. Real design requires real, contextual layout, authentic micro-diffs, real metrics, and functional controls.

---

## 2. The AI Anti-Pattern Library (Learnings from Past Failures)

Avoid these documented AI failure modes:

- **The "Fixed Viewport Vertical Overflow" Failure:** In full-screen HUDs (`100vh`), if headers, command bars (`.playground-bar`), or docks are introduced without recalculating child grid heights, the grid spills past the screen boundary, creating double scrollbars or hiding bottom ledger cards. 
  - *SRRL Rule:* When adding top bars, recalculate `.cockpit-grid` height: `height: calc(100vh - [total_header_height]px); min-height: 0; overflow: hidden;`.
- **The "Pointer-Events Canvas Occlusion" Failure:** When placing a 3D WebGL background canvas (e.g. Three.js `#manifold-canvas`) under an interactive HTML layout, setting `pointer-events: auto` on the parent container blocks camera orbit/drag interactions.
  - *SRRL Rule:* Set `pointer-events: none;` on the root layout container (`.app-container`), and selectively enable `pointer-events: auto;` only on interactive glass panels (`.panel`, `.interactive`, `.top-deck`).
- **The "Slide Deck Takeover" Failure:** Replacing the active 3D visualization or primary runtime canvas with full-screen slide takeovers breaks ambient immersion and destroys situational awareness.
  - *SRRL Rule:* Never unmount or cover the WebGL canvas. Implement floating frosted-glass HUD overlays (`backdrop-filter: blur(24px)`) positioned directly above the live 60 FPS viewport.
- **The "Static Kiosk Deception" Failure:** Building hardcoded mock buttons without real arbitrary prompt inputs or dynamic invariant toggles reduces an autonomous hypervisor to a canned kiosk demo.
  - *SRRL Rule:* Developer control planes must provide active playground bars (`>_ PROMPT AGENT:`), model selector dropdowns, live token streaming boxes with typing cursors, and real-time toggleable invariant registries.
- **The "Sticky-Void" Failure:** Do NOT apply `overflow: hidden`, `overflow-x-hidden`, or `overflow-y-hidden` to structural wrappers if any child components rely on `position: sticky`. It breaks the sticky context and causes elements to vanish out of view.
- **The "Boxed-In" SaaS Failure:** Do NOT wrap dynamic telemetry visualizations in constrained `.max-w-7xl.mx-auto` containers unless building text-heavy documentation. Let backgrounds bleed edge-to-edge.
- **The "Phantom Backend" Failure:** Never build a frontend that white-screens if the API is offline. UI components must gracefully handle network failures, displaying intentional status chips and fallback states.
- **The "Blind Animation" Failure:** When mapping scroll or state opacities, ensure there are no overlapping dead zones where opacity drops entirely to 0 for extended durations. Always cross-fade.

---

## 3. Cyber-Industrial Glassmorphic Design System (Tokens & Specs)

Strictly adhere to this calibrated design system extracted from the production Causalyn Acausal Control Plane:

### A. Color Palette (Cyber-Industrial High-Contrast)
```css
:root {
  /* Canvas & Panel Backgrounds */
  --bg-base: #030712;                    /* Deep obsidian base */
  --bg-secondary: #0A1120;               /* Sub-surface void */
  --panel-bg: rgba(10, 17, 34, 0.82);    /* Frosted crystalline glass */
  --panel-card: rgba(13, 21, 41, 0.9);   /* Sub-panel tile */
  --panel-border: rgba(30, 41, 59, 0.8); /* Slate sub-pixel boundary */
  --panel-border-focus: rgba(0, 243, 255, 0.6);

  /* Typography & Faint Tones */
  --text-primary: #F8FAFC;
  --text-secondary: #94A3B8;
  --text-muted: #64748B;
  --text-faint: #475569;

  /* Functional Neons & Accents */
  --cyan-accent: #00F3FF;                /* Compiler / SMT Active */
  --cyan-light: rgba(0, 243, 255, 0.12);
  --cyan-border: rgba(0, 243, 255, 0.35);
  --cyan-glow: rgba(0, 243, 255, 0.45);

  --indigo-primary: #6366F1;             /* Equilibrium & Clocks */
  --indigo-light: rgba(99, 102, 241, 0.15);
  --indigo-border: rgba(99, 102, 241, 0.35);

  --safe-emerald: #10B981;               /* Commit Verified (κ=0) */
  --safe-bg: rgba(16, 185, 129, 0.12);
  --safe-border: rgba(16, 185, 129, 0.35);

  --paradox-crimson: #FF1E44;            /* State Collapse / Invariant Violation */
  --paradox-bg: rgba(255, 30, 68, 0.15);
  --paradox-border: rgba(255, 30, 68, 0.45);
  --paradox-glow: rgba(255, 30, 68, 0.6);

  --amber-warn: #F59E0B;                 /* Speculative AST Warning */
  --amber-bg: rgba(245, 158, 11, 0.12);

  /* Depth Shadows */
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.4), 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 20px -2px rgba(0, 0, 0, 0.6), 0 2px 6px -1px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 15px 35px -5px rgba(0, 0, 0, 0.8), 0 5px 15px -3px rgba(0, 243, 255, 0.15);
}
```

### B. Volumetric Lighting & Background Ambient Formula
Never use flat black. Apply triple radial lighting:
```css
body {
  background: var(--bg-base);
  background-image: 
    radial-gradient(at 15% 15%, rgba(0, 243, 255, 0.06) 0px, transparent 50%),
    radial-gradient(at 85% 20%, rgba(99, 102, 241, 0.08) 0px, transparent 50%),
    radial-gradient(at 50% 85%, rgba(255, 30, 68, 0.05) 0px, transparent 50%);
}
```

### C. Crystalline Glass Panel Specification
```css
.panel {
  background: var(--panel-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--panel-border);
  border-radius: 16px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-md);
  pointer-events: auto;
  overflow: hidden;
  position: relative;
}
```

---

## 4. The 3-Zone Acausal Cockpit Architecture

Spatial dashboards governing runtime systems must employ strict Left-to-Right informational flow:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────┐
│  TOP NAVIGATION DECK (Brand, Stance Switches, Sim Buttons, Audio Spectrum, Kernel Status)     │
├────────────────────────────────────────────────────────────────────────────────────────────────┤
│  ACAUSAL PLAYGROUND BAR (>_ PROMPT AGENT: [Model Select] [Prompt Input] [⚡ RUN] Presets | CLI) │
├──────────────────────────┬──────────────────────────────────────────┬──────────────────────────┤
│ ZONE 1: SWARM HUB        │ ZONE 2: MATHEMATICAL CONTINUUM           │ ZONE 3: GROUND TRUTH     │
│ - Reasoning Stream Box   │ - Master Stage Tabs (3D / Proofs)        │ - 34,200x Speedup Hero   │
│   (Live Token Streaming) │ - Floating Ambient Math HUD Overlay      │ - Paradox Curvature (κ)  │
│ - Lamport Clock RPC Feed │ - 3D Symplectic Wireframe Canvas         │ - Hypervisor Latency     │
│ - Syntax Micro-Diffs     │ - LTX-2 Precision Timeline Scrubber      │ - Dynamic Invariant Deck │
│   (Green/Red AST Deltas) │   (Phase markers: S₀ -> S_cand -> S_null)│ - Z3 Proof Box / Ledger  │
└──────────────────────────┴──────────────────────────────────────────┴──────────────────────────┘
```

### Proportional Grid Layout
```css
.cockpit-grid {
  flex: 1;
  display: grid;
  grid-template-columns: 340px 1fr 350px;
  gap: 16px;
  padding: 12px 20px 16px;
  overflow: hidden;
  height: calc(100vh - 144px);
  min-height: 0;
}
```

### Master Z-Axis Layering Hierarchy
1. `z-index: 1`: Three.js canvas `#manifold-canvas` (fullscreen, `pointer-events: auto`).
2. `z-index: 10`: Root UI container `.app-container` (`pointer-events: none`).
3. `z-index: 20`: Interactive floating docks (`.top-deck`, `.playground-bar`, `.panel`, `pointer-events: auto`).
4. `z-index: 100`: Ambient HUD overlays (`.theorem-hud-overlay`).

---

## 5. Kinetic Physics & Interactive Components

### A. Cyber Toggle Switch (Dynamic Invariants)
```css
.inv-toggle {
  position: relative;
  display: inline-block;
  width: 28px;
  height: 16px;
}
.inv-slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background-color: rgba(51, 65, 85, 0.8);
  transition: 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 16px;
  border: 1px solid rgba(71, 85, 105, 0.7);
}
.inv-slider:before {
  position: absolute;
  content: "";
  height: 10px;
  width: 10px;
  left: 2px;
  bottom: 2px;
  background-color: #94A3B8;
  transition: 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border-radius: 50%;
}
.inv-toggle input:checked + .inv-slider {
  background-color: rgba(16, 185, 129, 0.35);
  border-color: #10B981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
}
.inv-toggle input:checked + .inv-slider:before {
  transform: translateX(12px);
  background-color: #10B981;
  box-shadow: 0 0 6px #10B981;
}
```

### B. Micro-Animations & Telemetry Pulses
- **Status Beacon:**
  ```css
  @keyframes pulse-dot {
    0% { transform: scale(0.95); opacity: 0.8; }
    50% { transform: scale(1.2); opacity: 1; }
    100% { transform: scale(0.95); opacity: 0.8; }
  }
  ```
- **Typing Cursor Pulse:**
  ```css
  @keyframes cursor-blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
  }
  ```
- **Hero Acceleration Card Top Gradient:**
  ```css
  .autobahn-speedup-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #00F3FF, #6366F1, #10B981);
  }
  ```

---

## 6. Self-Reflective Verification Rules (SRRL Checkpoints)

Before claiming any UI task complete, the agent must run through these 5 Self-Reflective Checkpoints:

1. **The 900px Viewport Gate:** Does the dashboard fit into a `1920x945` laptop viewport without triggering a window-level vertical scrollbar? (Verify `.cockpit-grid` height calculation).
2. **The 3D Interaction Gate:** Can the user click and orbit the 3D WebGL manifold without being blocked by invisible parent DOM layers? (Verify `pointer-events: none` on `.app-container` and `pointer-events: auto` on interactive cards).
3. **The State Nullification Gate:** When a destructive invariant violation occurs ($\kappa > 0$), does the UI visually deform (crimson glow, localized manifold spike, status collapse) while proving zero host mutations?
4. **The Live Typing Gate:** When an agent prompt is dispatched, do tokens stream visibly into the thought container with continuous autoscroll and active status pulsation?
5. **The Reactivity Gate:** When a user toggles an invariant OFF in Zone 3, does the subsequent prompt execution reflect the rule change immediately without requiring a browser refresh?

---

## 7. The Multi-Page Architectural Decoupling Rule (Selective Page Splitting)

When addressing UI congestion, clutter, or information density:
- **THE CARDINAL HYPERVISOR INVARIANT:** Never fragment the live execution feedback loop across different pages. An engineer testing an agent prompt MUST observe the speculative `<thinking>` trace, the 3D manifold deformation/repair, the SMT solver proof trace, and the immutable ledger commit on ONE unified screen without page hops.
- **WHAT IS PERMITTED ON SEPARATE PAGES:**
  1. **Academic Theory & Formal Proofs (`/proofs`):** Heavy mathematical derivations, LaTeX equations, Axioms I–IV, embedded 3B1B/Manim video lectures, and whitepaper download links. Moving these off the live cockpit allows the 3D Symplectic Manifold to breathe at full resolution without occlusion.
  2. **Policy Studio & Deep Governance (`/invariants`):** Full multi-column policy registries, custom rule authoring suites with live SMT compilation, and dry-run boundary testers. On the main cockpit, provide a compact, clean quick-toggle monitor with a direct link to the studio.
- **GLOBAL NAVIGATION INTEGRITY:**
  - Every decoupled page must share the unified obsidian/cyan `.top-deck` with `.top-nav-links` (`⚡ Cockpit`, `🛡️ Policy Studio`, `📐 Theory & Proofs`, `📖 Docs ↗`).
  - Active page states must glow cyan with subtle box-shadows (`box-shadow: 0 0 14px rgba(0, 243, 255, 0.3)`).
  - Unused controls on secondary pages (e.g. prompt bars, 3D camera switches) must not be rendered, ensuring dedicated pages are focused and responsive.

---

## 8. The Responsive Multi-Viewport Invariant Rule (SRRL Viewport Gates)

Every web application and dashboard governed by Skeli-Skills MUST satisfy strict multi-viewport integrity:

### A. The Zero Horizontal Overflow Invariant
- **The Law:** Under NO circumstances may any page (`/`, `/invariants`, `/proofs`) trigger a window-level horizontal scrollbar (`scrollWidth > clientWidth`).
- **Audit Requirement:** Verification must be conducted across all standard device viewports:
  1. Desktop: `1920x1080`
  2. Small Desktop / Laptop: `1366x768`
  3. Tablet Portrait: `768x1024`
  4. Mobile Portrait: `390x844`
- **Global CSS Safeguard:**
  ```css
  html, body {
    max-width: 100vw;
    overflow-x: hidden !important;
  }
  ```

### B. Adaptive Viewport Hierarchy
1. **Desktop ($> 1200\text{px}$):**
   - Fixed-height HUD (`height: calc(100vh - 144px); min-height: 0; overflow: hidden;`).
   - 3-column proportional grid (`310px 1fr 310px`), with internal scrollable regions inside panels.
2. **Tablet Landscape & Medium Screens ($768\text{px} - 1100\text{px}$):**
   - Unconstrain height: switch `body` and `.app-container` from `overflow: hidden; height: 100vh;` to `overflow-y: auto; height: auto; min-height: 100vh;`.
   - Stack `.cockpit-grid` vertically in prioritized order:
     - **Order 1:** Stage Panel (Three.js 3D canvas viewport maintained at `min-height: 440px`).
     - **Order 2:** Zone 1 Multi-Agent Swarm Stream (`min-height: 360px`).
     - **Order 3:** Zone 3 Ground Truth Ledger & Invariant Monitor (`min-height: 360px`).
3. **Mobile ($< 768\text{px}$):**
   - Top deck wraps cleanly: brand on top, nav links scrolling horizontally with `-webkit-overflow-scrolling: touch`, stance selectors stacked.
   - Command playground: prompt input expands to 100% width, run button occupies full-width touch target ($44\text{px}$ minimum height).
   - Scenario chips scroll horizontally in an edge-to-edge kinetic row.
   - Data tables (`.policy-table`) reside in isolated touch-scrollable wrappers (`.policy-table-container { overflow-x: auto; max-width: 100%; }`) while preserving zero page-level overflow.

### C. The Page Scrollability Invariant (`.page-scrollable`)
When creating subpages with extensive academic proofs, video archives, or expansive tabular registries:
- The body tag MUST declare `<body class="page-scrollable">`.
- Root container MUST declare `<div class="app-container page-container">`.
- CSS must enforce:
  ```css
  body.page-scrollable {
    overflow-y: auto !important;
    overflow-x: hidden !important;
    height: auto !important;
    min-height: 100vh;
  }
  .page-container {
    height: auto !important;
    min-height: 100vh;
    overflow-y: visible;
    pointer-events: auto;
  }
  ```

---

## 9. Offline Self-Containment, Protocol Agnosticism & HTML Sanitization

### A. Zero External CDN Dependency (Air-Gapped & Offline Resilience)
- **Failure Mode:** Importing essential visualization libraries directly from public CDNs (e.g. `import * as THREE from 'https://cdn.skypack.dev/...'`) causes instantaneous white-screen failures if the client is offline, air-gapped, behind corporate proxies, or when the CDN experiences downtime.
- **SRRL Rule:** Always bundle vendor libraries locally (e.g., `web/static/three.min.js`).
- **Progressive Fallback Pattern:**
  ```javascript
  // Prefer local bundled distribution, fallback to CDN only if local is absent
  const THREE = window.THREE || (await import('https://cdn.skypack.dev/three@0.136.0'));
  ```

### B. Mathematical Expression HTML Sanitization
- **Failure Mode:** When rendering dynamic invariant rules, user input strings, or SMT formulas into tables via `tr.innerHTML = \`...\${expr}...\``, any expression containing mathematical inequalities like `threads <= 16` or `x < y` has its `<` parsed as an unclosed HTML tag. The browser breaks the DOM node, drops following cells, and displays corrupted empty rows.
- **SRRL Rule:** ALWAYS sanitize all dynamic expressions and strings before `innerHTML` interpolation:
  ```javascript
  function escapeHtml(str) {
      if (str == null) return '';
      return String(str)
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;')
          .replace(/'/g, '&#039;');
  }
  ```

### C. Port & Protocol Dynamic Resolution
- **Failure Mode:** Hardcoding `http://127.0.0.1:8000` or `ws://127.0.0.1:8000` breaks when accessed via `localhost`, custom `--port`, Docker containers, ngrok tunnels, or TLS reverse proxies (`https`/`wss`).
- **SRRL Rule:** Always compute endpoints dynamically:
  ```javascript
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host; // includes port if non-standard
  const wsUrl = `${protocol}//${host}/ws/continuum`;
  // REST calls: Use relative paths
  const res = await fetch('/api/v1/intercept', { ... });
  ```

### D. Video Asset Optimization
Multi-video research portals must never eager-load heavy video files on initial page load:
```html
<video class="axiom-video-player" src="..." controls loop muted playsinline preload="metadata"></video>
```
Setting `preload="metadata"` ensures header metadata and dimensions are known immediately for zero-shift layout calculation without saturating browser memory or network bandwidth.

---

## 10. Cognitive Information Architecture & Dashboard Placement Heuristics

### A. The 5-Second Cognitive Comprehension Law
Visitors encountering an advanced technical dashboard (such as a formal verification hypervisor or compiler sandbox) must immediately grasp its core purpose and mental model within 5 seconds.
- **Anti-Pattern:** Dumping raw metrics, unlinked graphs, and complex controls into disjointed 3-column layouts where users cannot discern where execution begins, where it transforms, or where it ends.
- **SaaS Heuristic:** Structure the interface around an unmistakable left-to-right temporal lifecycle:
  1. **Phase 1: Agent Intent & Speculative AST** (What the AI model wants to do)
  2. **Phase 2: Shadow Intercept & Geometrical Manifold** (What the hypervisor captures and inspects in ephemeral memory)
  3. **Phase 3: Formal Verification Resolution & Atomic Commit** (How Z3 SMT proves safety, auto-patches bad AST parameters via CEGIS in 44µs, or annihilates toxic operations with zero host disk write)

### B. The 3-Phase Lifecycle Stepper
Linearize multi-column cognitive density by anchoring an interactive, real-time status stepper bar spanning above the panels:
```html
<div class="lifecycle-stepper-bar" id="lifecycle-stepper">
    <div class="stepper-step active" id="stepper-step-1" data-phase="1">
        <span class="step-num">01</span>
        <span class="step-title">AGENT INTENT</span>
    </div>
    <div class="stepper-connector"></div>
    <div class="stepper-step" id="stepper-step-2" data-phase="2">
        <span class="step-num">02</span>
        <span class="step-title">SHADOW MANIFOLD</span>
    </div>
    <div class="stepper-connector"></div>
    <div class="stepper-step" id="stepper-step-3" data-phase="3">
        <span class="step-num">03</span>
        <span class="step-title">VERIFY &amp; COMMIT</span>
    </div>
</div>
```
- During idle: Step 1 is gently lit.
- Upon dispatch: Step 1 pulses active (`.active`).
- Upon intercept: Step 2 illuminates yellow or crimson violation (`.violation`).
- Upon synthesis or commit: Step 3 illuminates verified emerald (`.verified`).
- Step clicks smoothly scroll to the corresponding zone on mobile/tablet screens.

### C. First-Run Guided Discovery Scenario Cards
Never present new visitors with an empty input box or a cold blank screen:
- Populate the idle container with **Guided Scenario Attack Cards** (e.g. *CEGIS Auto-Patch*, *Fatal Annihilation*, *Safe Spec*).
- Each card describes the scenario, the technical stakes, and has a single-click action that immediately triggers the live execution pipeline.

### D. 30-Second "How It Works" Infographic Modal
Provide an easily discoverable `💡 HOW IT WORKS` button in the top navigation deck. It launches a high-contrast glassmorphic modal explaining the 3-phase execution model in concise, plain-English terms with zero clutter.

### E. Top Deck Anti-Collision & Responsive Zero-Overflow Discipline
- Brand subtitles (e.g. `FORMAL VERIFICATION HYPERVISOR`) belong directly beneath the primary brand logo in the flex column, never as floating 400px fixed-width banners in the top deck that cause horizontal overflow on laptops (1366x768).
- Under `@media (max-width: 1366px)`, button text labels must collapse gracefully (e.g. `.stance-label { display: none; }`, reduced gap and padding) to guarantee that `docScrollWidth === docClientWidth` across all screen resolutions.

### F. Favicon 404 Prevention Invariant
- Modern browsers and automated crawlers systematically request `/favicon.ico` via both `GET` and `HEAD` methods.
- Always provide `@app.api_route("/favicon.ico", methods=["GET", "HEAD"])` in the backend API, serve a dedicated SVG/ICO asset, and declare `<link rel="icon" type="image/svg+xml" href="/favicon.ico">` in every HTML document.

---

## 11. High-Throughput Pressure Testing, DOM Resilience & Stress Invariants

Any mission-critical, AI-orchestrated control plane must be impervious to traffic storms, adversarial payloads, and unbounded DOM growth. The following heuristics and architectural invariants must be enforced:

### A. Bounded DOM Node Invariant (Preventing UI Memory Leaks)
Under high-frequency WebSocket event storms (e.g. 50–100 telemetry packets/sec), appending nodes indefinitely causes catastrophic browser memory spikes, garbage collection jank, and eventual tab crashes:
- **Terminal Event Feeds**: Strictly cap real-time terminal and audit log containers to a fixed maximum (e.g., 30 items). Always prune overflow nodes from the tail:
  ```javascript
  if (feed.children.length > 30) {
      feed.lastElementChild.remove();
  }
  ```
- **Cryptographic Ledgers & Hash Feeds**: Cap historical ledger cards to a fixed maximum (e.g., 5 items):
  ```javascript
  if (list.children.length > 5) {
      list.lastElementChild.remove();
  }
  ```
- **Telemetry Throttling**: Decouple high-rate incoming socket packets from DOM rendering using `requestAnimationFrame` or a fixed batching cadence so the main thread never drops below 60fps.

### B. High-Frequency UI Fuzzing & Rapid State Transitions
Frontends must withstand hostile, rapid-fire user interactions without state desynchronization or uncaught exceptions:
- **Rapid Stance & Mode Switching**: Fast toggling between operational modes (e.g. Autobahn vs. Defensive Hypervisor) must cleanly update active button classes and recalculate policy metrics without visual glitches.
- **Camera & Manifold Transformations**: Rapid perspective switching (Default Manifold, High-Angle Isometric, Top-Down Symplectic) must smoothly interpolate Three.js camera coordinates without throwing WebGL context loss or matrix inversion errors.
- **Modal Dialog Lifecycle**: Rapid open/close cycles on modals (e.g., Guide and Infographic dialogs) must correctly update `aria-hidden`, manage focus trap, and restore viewport scrolling with zero backdrop freeze.
- **Timeline Scrubber Seeking**: Interactive temporal scrubbers must handle rapid, non-monotonic value seeks without race conditions in shadow execution playback.

### C. Concurrent Multi-Tab WebSocket Continuum
- Multiple browser tabs connected to the same backend WebSocket endpoint (e.g. `/ws/continuum`) must operate independently and receive streaming telemetry simultaneously.
- Broadcast dispatches from any single client session must stream cleanly across all active connections without blocking backend event loops or dropping packets.

### D. Backend Concurrency & Throughput Benchmarks
The backend verification engine, CRDT bus, and SMT solver must be validated against four distinct stress vectors:
1. **Burst Intercept Concurrency**: Intercept 120+ burst requests at concurrency 30 with 0% 500-errors, sub-second wallclock execution, and fail-closed annihilation on hazardous code.
2. **Swarm CRDT Vector Clock Burst**: Process 60+ batches across 20 concurrent threads merging 900+ atomic operations, verifying 100% deterministic and monotonic vector clocks (>2,400 ops/sec).
3. **Adversarial Fuzzing Defense**: Intercept 8 high-risk boundary attacks (unclosed syntax, raw binary shell scripts, path traversal escapes, extreme negative integers, giant numbers for Z3 overflow defense, 50KB injected comment buffers, zero-variable state, schema pollution) with instant containment.
4. **WebSocket Stream Multiplexing**: Sustain 25+ simultaneous WebSocket connections under continuous telemetry broadcast with 100% packet delivery and zero drops.

### E. Integration Test Isolation Discipline
- When testing stateful backends (e.g., with FastAPI `TestClient`), relying solely on `setUpClass()` causes insidious test order dependencies where mutating tests (such as pipeline intent commits) pollute the state of subsequent assertions.
- Always implement per-test cleanup (`setUp(self)`) that calls `app.WORLD_STATE.reset()` and re-seeds canonical fixture files before every individual test method.
- Route handlers that broadcast real-time state over WebSockets should be declared as `async def` to execute on the main event loop and directly await broadcast delivery, avoiding cross-thread event loop dispatch deadlocks.

---

## 12. References
- Control Plane CSS: `web/css/glassmorphism.css`
- Live Execution Cockpit: `web/index.html`
- Invariant Policy Studio: `web/invariants.html`
- Mathematical Theory & Proofs: `web/proofs.html`
- Cockpit JS Logic: `web/js/cockpit.js`
- 3D Symplectic Manifold: `web/js/manifold_stream.js`
- Local Three.js Bundle: `web/three.min.js`
- Invariant Registry: `backend/core/invariant_registry.py`
- Reasoning Engine: `backend/core/agent_reasoning.py`
- External CLI Wrap: `scripts/causalyn_wrap.py`
- Multi-Viewport Verification: `scripts/verify_responsive.py`
- Interactive Stepper Verification: `scripts/verify_interactive_stepper.py`
- Web Cockpit Pressure Test Suite: `scripts/pressure_test_web.py`
- Backend Pressure & Stress Benchmark Suite: `tests/stress/run_all_pressure_tests.py`


