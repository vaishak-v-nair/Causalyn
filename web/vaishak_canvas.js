/**
 * Vaishak Continuum (V) - Pure Three.js & Custom GLSL Shader Engine
 * 
 * Physically realizes the Vaishak Principle of Semantic Nullification (VPSN):
 * 1. High-density PlaneGeometry representing the Semantic Null-Space (V)
 * 2. GLSL Vertex Shader: Injects Paradox Index (kappa) directly into GPU coordinates
 *    - Flat equilibrium when kappa == 0.0
 *    - Violent non-linear topological curvature spikes when kappa > 0.0
 * 3. GLSL Fragment Shader: Visualizes Destructive Semantic Interference
 *    - Sweeping luminescent Intent Vector (I) plane of blue laser light
 *    - Digital ash dissolve on singularity collision
 *    - Smooth Semantic Ricci Flow relaxation back to flat equilibrium
 * 4. Three.js Particle Cloud for radiant digital ash explosion
 */

(function (root, factory) {
  if (typeof define === "function" && define.amd) {
    define([], factory);
  } else if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.VaishakContinuumEngine = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  // GLSL Vertex Shader: Mathematical Curvature Deformation
  const VERTEX_SHADER = `
    uniform float u_time;
    uniform float u_kappa;
    uniform float u_annihilation_phase;
    uniform float u_ricci_relaxation;
    uniform float u_intent_sweep;

    varying vec2 vUv;
    varying vec3 vPosition;
    varying vec3 vNormal;
    varying float vElevation;
    varying float vCurvature;

    void main() {
      vUv = uv;
      vec3 pos = position;

      // 1. Semantic Null-Space Harmonic Equilibrium (kappa == 0)
      // Smooth symplectic Riemannian pulses
      float harmonic1 = sin(pos.x * 0.18 + u_time * 1.2) * cos(pos.y * 0.18 + u_time * 0.9) * 0.35;
      float harmonic2 = sin(pos.x * 0.09 - u_time * 0.6 + pos.y * 0.09) * 0.25;
      float baseEquilibrium = harmonic1 + harmonic2;

      // 2. The Paradox Eruption (kappa > 0)
      // When kappa spikes, high-frequency violent topological curvature warps the mesh
      float normalizedKappa = clamp(u_kappa / 30.0, 0.0, 3.5);

      // Paradox Singularity Core coordinates (center-right)
      vec2 singularity = vec2(3.5, -2.2);
      float dist = length(pos.xy - singularity);

      // Curvature envelope: exponential tension gradient
      float tensionEnvelope = exp(-dist * 0.38);
      
      // High-frequency, jagged, non-linear curvature tension
      float highFreqWave = sin(pos.x * 3.8 + u_time * 9.0) * cos(pos.y * 3.8 - u_time * 8.0);
      float shockSpike = (sin(dist * 5.2 - u_time * 14.0) * 2.8 + highFreqWave * 3.6) * tensionEnvelope;
      shockSpike += (sin(pos.x * 2.0 + u_time * 5.0) * 1.8) * exp(-dist * 0.18);

      // Annihilation Wave Collapse:
      // As the sweeping blue Intent Vector sweeps across, forced back to flat equilibrium
      float sweepCoord = (pos.x + 18.0) / 36.0;
      float isSwept = smoothstep(sweepCoord - 0.08, sweepCoord + 0.08, u_intent_sweep);
      float annihilationDecay = mix(1.0, 0.0, isSwept * u_annihilation_phase);

      // Semantic Ricci Flow: smooths remaining topological tension
      float effectiveKappa = normalizedKappa * annihilationDecay * (1.0 - u_ricci_relaxation);

      // Total Z-axis displacement on the continuous manifold
      float totalDisp = (baseEquilibrium * 0.7) + (shockSpike * effectiveKappa * 3.6);

      pos.z += totalDisp;
      vElevation = totalDisp;
      vCurvature = length(shockSpike * effectiveKappa);
      vPosition = pos;
      vNormal = normal;

      gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
    }
  `;

  // GLSL Fragment Shader: Energy, Light, and Destructive Interference
  const FRAGMENT_SHADER = `
    uniform float u_time;
    uniform float u_kappa;
    uniform float u_annihilation_phase;
    uniform float u_intent_sweep;
    uniform vec2 u_resolution;

    varying vec2 vUv;
    varying vec3 vPosition;
    varying float vElevation;
    varying float vCurvature;

    void main() {
      // 1. Color Palette Definitions (Deep Space / Symplectic Continuum)
      vec3 deepVoid = vec3(0.025, 0.045, 0.08);
      vec3 nullSpaceBlue = vec3(0.08, 0.28, 0.75);
      vec3 cyanWire = vec3(0.18, 0.75, 0.98);
      vec3 paradoxRed = vec3(0.96, 0.12, 0.24);
      vec3 paradoxAmber = vec3(1.0, 0.65, 0.05);
      vec3 intentLaser = vec3(0.35, 0.88, 1.0);
      vec3 ashWhite = vec3(0.95, 0.98, 1.0);

      // 2. Procedural Antialiased Wireframe Grid
      vec2 gridScale = vUv * 64.0;
      vec2 gridUv = fract(gridScale);
      vec2 gridDeriv = fwidth(gridScale);
      vec2 gridEdge = step(gridDeriv * 1.3, gridUv) * step(gridDeriv * 1.3, 1.0 - gridUv);
      float gridLine = 1.0 - (gridEdge.x * gridEdge.y);

      // 3. Base Manifold Shading
      float normElev = clamp((vElevation + 2.0) / 6.0, 0.0, 1.0);
      vec3 surface = mix(deepVoid, nullSpaceBlue, normElev * 0.7);

      // 4. Paradox Singularity Glow (Topological Curvature Spike)
      float paradoxIntensity = clamp(vCurvature * 0.45, 0.0, 1.0);
      if (u_kappa > 0.05) {
        vec3 fieryCore = mix(paradoxRed, paradoxAmber, clamp((vElevation - 1.5) * 0.4, 0.0, 1.0));
        surface = mix(surface, fieryCore, paradoxIntensity * 0.9);
      }

      // 5. Wireframe Glow Overlay
      vec3 wireGlow = mix(cyanWire * 0.7, paradoxRed * 1.5, paradoxIntensity);
      surface = mix(surface, wireGlow, gridLine * 0.68);

      // 6. Destructive Semantic Interference: Intent Vector (I) Plane Collision
      float sweepCoord = (vPosition.x + 18.0) / 36.0;
      float sweepDist = abs(sweepCoord - u_intent_sweep);
      float sweepWave = smoothstep(0.12, 0.0, sweepDist);
      float laserEdge = smoothstep(0.03, 0.0, sweepDist);

      if (u_annihilation_phase > 0.001) {
        // Sweeping luminescent plane of blue energy
        surface += intentLaser * sweepWave * 2.4 * u_annihilation_phase;
        surface += vec3(1.0, 1.0, 1.0) * laserEdge * 3.5 * u_annihilation_phase;

        // Digital Ash Dissolve Effect behind the sweep plane
        if (sweepCoord < u_intent_sweep && paradoxIntensity > 0.08) {
          float ashNoise = fract(sin(dot(vUv * 128.0 + u_time * 25.0, vec2(12.9898, 78.233))) * 43758.5453);
          if (ashNoise > 0.45) {
            surface = mix(surface, ashWhite * 2.8, 0.75 * u_annihilation_phase);
          }
        }
      }

      // Vignette / Depth Fade at boundaries
      float radialDist = length(vUv - vec2(0.5)) * 2.0;
      float alpha = smoothstep(1.38, 0.45, radialDist);

      gl_FragColor = vec4(surface, alpha * 0.94);
    }
  `;

  class VaishakContinuumEngine {
    constructor(canvasId) {
      this.canvas = document.getElementById(canvasId);
      if (!this.canvas) {
        console.warn(`[VPSN Engine] Canvas element #${canvasId} not found.`);
        return;
      }

      this.wrapper = this.canvas.parentElement;
      this.running = true;
      this.time = 0;

      // Telemetry state
      this.kappa = 0.0;
      this.targetKappa = 0.0;
      this.annihilationPhase = 0.0;
      this.intentSweep = -0.2;
      this.ricciRelaxation = 0.0;
      this.operatorStatus = "EQUILIBRIUM";

      // Orbit interaction
      this.rotationX = -Math.PI / 3.4;
      this.rotationZ = Math.PI / 8;
      this.targetRotX = this.rotationX;
      this.targetRotZ = this.rotationZ;
      this.isDragging = false;
      this.lastMouseX = 0;
      this.lastMouseY = 0;

      // Initialize Three.js WebGL or fallback
      if (typeof THREE !== "undefined") {
        this.initThree();
      } else {
        console.info("[VPSN Engine] Three.js not loaded; using high-speed Canvas fallback.");
        this.initCanvasFallback();
      }

      this.initEvents();
      this.animate();
    }

    initThree() {
      this.isThree = true;
      const width = this.wrapper ? this.wrapper.clientWidth : 800;
      const height = this.wrapper ? this.wrapper.clientHeight : 380;

      // 1. Scene & Perspective Camera
      this.scene = new THREE.Scene();
      this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
      this.camera.position.set(0, -32, 22);
      this.camera.lookAt(0, 0, 0);

      // 2. WebGL Renderer with Anti-Aliasing
      this.renderer = new THREE.WebGLRenderer({
        canvas: this.canvas,
        antialias: true,
        alpha: true,
        powerPreference: "high-performance",
      });
      this.renderer.setSize(width, height);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

      // 3. High-Density Symplectic Manifold Mesh (The Semantic Null-Space)
      const planeGeo = new THREE.PlaneGeometry(36, 36, 128, 128);

      this.uniforms = {
        u_time: { value: 0.0 },
        u_kappa: { value: 0.0 },
        u_annihilation_phase: { value: 0.0 },
        u_ricci_relaxation: { value: 0.0 },
        u_intent_sweep: { value: -0.2 },
        u_resolution: { value: new THREE.Vector2(width, height) },
      };

      this.shaderMaterial = new THREE.ShaderMaterial({
        vertexShader: VERTEX_SHADER,
        fragmentShader: FRAGMENT_SHADER,
        uniforms: this.uniforms,
        transparent: true,
        side: THREE.DoubleSide,
        depthWrite: false,
      });

      this.manifoldMesh = new THREE.Mesh(planeGeo, this.shaderMaterial);
      this.manifoldMesh.rotation.x = this.rotationX;
      this.manifoldMesh.rotation.z = this.rotationZ;
      this.scene.add(this.manifoldMesh);

      // 4. Radiant Digital Ash Particle Cloud
      this.initParticleCloud();

      // 5. Intent Vector Laser Beam Indicator Plane
      this.initIntentLaserPlane();
    }

    initParticleCloud() {
      const count = 1200;
      const positions = new Float32Array(count * 3);
      const velocities = new Float32Array(count * 3);
      const colors = new Float32Array(count * 3);

      for (let i = 0; i < count; i++) {
        const i3 = i * 3;
        // Seed around singularity (3.5, -2.2, 0)
        positions[i3] = (Math.random() - 0.5) * 36;
        positions[i3 + 1] = (Math.random() - 0.5) * 36;
        positions[i3 + 2] = (Math.random() - 0.5) * 4;

        velocities[i3] = (Math.random() - 0.5) * 0.04;
        velocities[i3 + 1] = (Math.random() - 0.5) * 0.04;
        velocities[i3 + 2] = Math.random() * 0.06;

        // Radiant cyan-blue quantum particles
        colors[i3] = 0.3 + Math.random() * 0.3;
        colors[i3 + 1] = 0.7 + Math.random() * 0.3;
        colors[i3 + 2] = 1.0;
      }

      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
      geo.setAttribute("color", new THREE.BufferAttribute(colors, 3));

      const mat = new THREE.PointsMaterial({
        size: 0.28,
        vertexColors: true,
        transparent: true,
        opacity: 0.65,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });

      this.particleCloud = new THREE.Points(geo, mat);
      this.particleCloud.rotation.x = this.rotationX;
      this.particleCloud.rotation.z = this.rotationZ;
      this.particleVelocities = velocities;
      this.scene.add(this.particleCloud);
    }

    initIntentLaserPlane() {
      // Luminescent sweep line
      const lineGeo = new THREE.BufferGeometry();
      const points = new Float32Array([0, -18, 0, 0, 18, 0]);
      lineGeo.setAttribute("position", new THREE.BufferAttribute(points, 3));

      const lineMat = new THREE.LineBasicMaterial({
        color: 0x60a5fa,
        transparent: true,
        opacity: 0.0,
        linewidth: 2,
      });

      this.intentLine = new THREE.Line(lineGeo, lineMat);
      this.intentLine.rotation.x = this.rotationX;
      this.intentLine.rotation.z = this.rotationZ;
      this.scene.add(this.intentLine);
    }

    initCanvasFallback() {
      this.isThree = false;
      this.ctx = this.canvas.getContext("2d");
      this.resizeCanvasFallback();
    }

    resizeCanvasFallback() {
      if (!this.canvas || !this.wrapper) return;
      const rect = this.wrapper.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      this.width = rect.width || 800;
      this.height = rect.height || 380;
      this.canvas.width = this.width * dpr;
      this.canvas.height = this.height * dpr;
      this.canvas.style.width = `${this.width}px`;
      this.canvas.style.height = `${this.height}px`;
      this.ctx.scale(dpr, dpr);
    }

    initEvents() {
      // Resize listener
      window.addEventListener("resize", () => {
        if (this.isThree && this.renderer && this.wrapper) {
          const w = this.wrapper.clientWidth;
          const h = this.wrapper.clientHeight;
          this.camera.aspect = w / h;
          this.camera.updateProjectionMatrix();
          this.renderer.setSize(w, h);
          this.uniforms.u_resolution.value.set(w, h);
        } else if (!this.isThree) {
          this.resizeCanvasFallback();
        }
      });

      // Mouse Drag Orbit
      const dom = this.canvas;
      dom.addEventListener("mousedown", (e) => {
        this.isDragging = true;
        this.lastMouseX = e.clientX;
        this.lastMouseY = e.clientY;
      });

      window.addEventListener("mousemove", (e) => {
        if (!this.isDragging) return;
        const dx = e.clientX - this.lastMouseX;
        const dy = e.clientY - this.lastMouseY;
        this.lastMouseX = e.clientX;
        this.lastMouseY = e.clientY;

        this.targetRotZ += dx * 0.008;
        this.targetRotX += dy * 0.008;
        this.targetRotX = Math.max(-Math.PI / 2.2, Math.min(-Math.PI / 6, this.targetRotX));
      });

      window.addEventListener("mouseup", () => {
        this.isDragging = false;
      });

      // Touch Drag
      dom.addEventListener("touchstart", (e) => {
        if (e.touches.length === 1) {
          this.isDragging = true;
          this.lastMouseX = e.touches[0].clientX;
          this.lastMouseY = e.touches[0].clientY;
        }
      }, { passive: true });

      window.addEventListener("touchmove", (e) => {
        if (!this.isDragging || e.touches.length !== 1) return;
        const dx = e.touches[0].clientX - this.lastMouseX;
        const dy = e.touches[0].clientY - this.lastMouseY;
        this.lastMouseX = e.touches[0].clientX;
        this.lastMouseY = e.touches[0].clientY;

        this.targetRotZ += dx * 0.008;
        this.targetRotX += dy * 0.008;
      }, { passive: true });

      window.addEventListener("touchend", () => {
        this.isDragging = false;
      });
    }

    /**
     * Trigger a violent topological Paradox Eruption (kappa > 0)
     */
    triggerParadoxEruption(kappaValue, reason) {
      this.targetKappa = Math.max(25.0, Number(kappaValue || 50.0));
      this.annihilationPhase = 0.0;
      this.intentSweep = -0.2;
      this.ricciRelaxation = 0.0;
      this.operatorStatus = "PARADOX_ERUPTION";
      this.lastReason = reason || "Violates Invariant Specification";
      this.updateHud();

      // Burst particle cloud at singularity
      if (this.particleCloud) {
        const pos = this.particleCloud.geometry.attributes.position.array;
        const count = pos.length / 3;
        for (let i = 0; i < count; i++) {
          const i3 = i * 3;
          if (Math.random() < 0.4) {
            pos[i3] = 3.5 + (Math.random() - 0.5) * 3;
            pos[i3 + 1] = -2.2 + (Math.random() - 0.5) * 3;
            pos[i3 + 2] = (Math.random() - 0.5) * 2;
          }
        }
        this.particleCloud.geometry.attributes.position.needsUpdate = true;
      }
    }

    /**
     * Trigger Destructive Semantic Interference (The Annihilation Sequence)
     */
    triggerAnnihilation() {
      this.annihilationPhase = 1.0;
      this.intentSweep = -0.1;
      this.operatorStatus = "DESTRUCTIVE_INTERFERENCE";
      this.updateHud();

      // Sweeping Intent Plane Animation
      const startTime = performance.now();
      const sweepDuration = 1600; // ms

      const stepSweep = (now) => {
        const progress = Math.min(1.0, (now - startTime) / sweepDuration);
        this.intentSweep = -0.1 + progress * 1.3;

        if (progress < 1.0) {
          requestAnimationFrame(stepSweep);
        } else {
          // Semantic Ricci Flow Relaxation to flat equilibrium
          this.operatorStatus = "ANNIHILATED";
          this.targetKappa = 0.0;
          this.ricciRelaxation = 1.0;
          this.updateHud();
          setTimeout(() => {
            this.resetEquilibrium();
          }, 800);
        }
      };

      requestAnimationFrame(stepSweep);
    }

    /**
     * Reset the manifold back to pure Semantic Null-Space equilibrium
     */
    resetEquilibrium() {
      this.targetKappa = 0.0;
      this.annihilationPhase = 0.0;
      this.intentSweep = -0.2;
      this.ricciRelaxation = 0.0;
      this.operatorStatus = "EQUILIBRIUM";
      this.lastReason = "Semantic Null-Space Admitted (kappa = 0.0)";
      this.updateHud();
    }

    updateHud() {
      const kappaEl = document.getElementById("canvas-hud-kappa");
      const statusEl = document.getElementById("canvas-hud-status");
      const curvatureEl = document.getElementById("canvas-hud-curvature");

      if (kappaEl) kappaEl.textContent = this.targetKappa.toFixed(2);
      if (statusEl) {
        statusEl.textContent = this.operatorStatus;
        statusEl.className = "telemetry-value " + (
          this.operatorStatus === "EQUILIBRIUM" ? "badge-green" :
          (this.operatorStatus === "ANNIHILATED" ? "badge-blue" : "badge-red")
        );
      }
      if (curvatureEl) {
        const curv = (this.targetKappa * 0.12).toFixed(3);
        curvatureEl.textContent = `${curv} rad/tensor`;
      }
    }

    animate() {
      if (!this.running) return;
      requestAnimationFrame(() => this.animate());

      this.time += 0.016;

      // Smooth interpolation
      this.kappa += (this.targetKappa - this.kappa) * 0.12;
      this.rotationX += (this.targetRotX - this.rotationX) * 0.08;
      this.rotationZ += (this.targetRotZ - this.rotationZ) * 0.08;

      if (this.isThree) {
        // Update Shader Uniforms directly on GPU
        this.uniforms.u_time.value = this.time;
        this.uniforms.u_kappa.value = this.kappa;
        this.uniforms.u_annihilation_phase.value = this.annihilationPhase;
        this.uniforms.u_intent_sweep.value = this.intentSweep;
        this.uniforms.u_ricci_relaxation.value = this.ricciRelaxation;

        // Rotate Mesh
        this.manifoldMesh.rotation.x = this.rotationX;
        this.manifoldMesh.rotation.z = this.rotationZ;

        if (this.particleCloud) {
          this.particleCloud.rotation.x = this.rotationX;
          this.particleCloud.rotation.z = this.rotationZ;

          // Animate particles
          const pos = this.particleCloud.geometry.attributes.position.array;
          const vels = this.particleVelocities;
          const count = pos.length / 3;

          for (let i = 0; i < count; i++) {
            const i3 = i * 3;
            pos[i3] += vels[i3];
            pos[i3 + 1] += vels[i3 + 1];
            pos[i3 + 2] += vels[i3 + 2] * (this.annihilationPhase > 0 ? 3.0 : 1.0);

            // Re-wrap bounds
            if (pos[i3 + 2] > 12) {
              pos[i3] = (Math.random() - 0.5) * 36;
              pos[i3 + 1] = (Math.random() - 0.5) * 36;
              pos[i3 + 2] = -2;
            }
          }
          this.particleCloud.geometry.attributes.position.needsUpdate = true;
        }

        if (this.intentLine) {
          this.intentLine.rotation.x = this.rotationX;
          this.intentLine.rotation.z = this.rotationZ;
          const sweepX = -18 + this.intentSweep * 36;
          this.intentLine.position.x = sweepX;
          this.intentLine.material.opacity = this.annihilationPhase > 0.01 ? 0.9 : 0.0;
        }

        this.renderer.render(this.scene, this.camera);
      } else {
        // 2D Canvas Fallback rendering
        this.renderCanvasFallback();
      }
    }

    renderCanvasFallback() {
      const ctx = this.ctx;
      const w = this.width;
      const h = this.height;

      ctx.fillStyle = "#060910";
      ctx.fillRect(0, 0, w, h);

      // Subtle isometric grid
      ctx.strokeStyle = this.kappa > 0 ? "rgba(239, 68, 68, 0.4)" : "rgba(59, 130, 246, 0.25)";
      ctx.lineWidth = 1;

      const cols = 28;
      const rows = 18;
      const cx = w / 2;
      const cy = h / 2 + 30;

      for (let y = 0; y < rows; y++) {
        ctx.beginPath();
        for (let x = 0; x < cols; x++) {
          const nx = (x / cols - 0.5) * 2;
          const ny = (y / rows - 0.5) * 2;
          const d = Math.hypot(nx - 0.3, ny + 0.2);
          const spike = this.kappa > 0 ? Math.exp(-d * 3) * Math.sin(d * 12 - this.time * 6) * this.kappa * 0.8 : 0;
          const wave = Math.sin(nx * 4 + this.time * 2) * 8 + spike;

          const px = cx + (x - y) * 16;
          const py = cy + (x + y) * 8 - wave;

          if (x === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        }
        ctx.stroke();
      }
    }
  }

  return VaishakContinuumEngine;
});
