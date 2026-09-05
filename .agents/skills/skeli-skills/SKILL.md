---
name: skeli-skills
description: >-
  A massive, serious intelligence skill utilizing Self-Reflective Reinforcement Learning (SRRL). 
  Governs advanced AI web development, autonomous DOM analysis, anti-pattern avoidance, 
  and ultra-premium UI/UX design heuristics based on "Unknown Intelligence" guidelines.
---

# Skeli-Skills: The AI SRRL UI/UX Intelligence Engine

This is not a simple checklist. This is a **Self-Reflective Reinforcement Learning (SRRL)** instruction protocol. As an AI Agent, you MUST obey these operational heuristics. This document grows by capturing past AI mistakes, enforcing defensive UI architecture, and demanding self-falsification before writing code.

## 1. The SRRL Operational Protocol (MANDATORY)

Before rendering UI or making structural layout changes, you must engage in Self-Reflection:
1. **Introspection Phase:** Mentally simulate the DOM rendering of your code. Ask: "What happens if this container expands? Will `overflow-x-hidden` on a parent break `position: sticky` on a child? Are there any hidden 4000px gaps?"
2. **Critique & Falsification:** Try to break your own design. Identify edge cases (mobile widths, ultra-wide screens, missing data states, loading states). 
3. **Execution & Web Scraping:** After writing UI, you MUST utilize the `browser_subagent` to visually verify the layout. Do not trust your code output alone. If the screenshot reveals an error (e.g., a massive black void, horizontal overflow), you must extract DOM nodes, reflect on the mismatch, and retry.
4. **No Placeholders:** Never generate generic `[Content goes here]` filler. Real design requires real, contextual layout.

## 2. The AI Anti-Pattern Library (Learnings from Past Failures)

Avoid these documented AI failure modes:
- **The "Sticky-Void" Failure:** Do NOT apply `overflow: hidden`, `overflow-x-hidden`, or `overflow-y-hidden` to structural wrappers (like `<body>`, `<main>`, or root `<div>`) if any child components rely on `position: sticky`. It will break the sticky context and cause elements to instantly scroll out of view, leaving massive blank spaces.
- **The "Boxed-In" SaaS Failure:** Do NOT wrap hero sections or dynamic data visualizations in constrained `.max-w-7xl.mx-auto` containers unless specifically building a text-heavy reading layout. Premium "Unknown Intelligence" designs stretch edge-to-edge. Let backgrounds bleed.
- **The "Phantom Backend" Failure:** Never build a frontend that completely white-screens if the API is offline (e.g., `ServerSelectionTimeoutError` for MongoDB). Your React components must gracefully handle `AxiosError`, returning empty arrays and rendering striking, intentional Empty States (`NO ANOMALIES DETECTED`).
- **The "Blind Animation" Failure:** When mapping framer-motion `useScroll` opacities (e.g., `useTransform(scrollYProgress, [0.2, 0.4], [0, 1])`), ensure there are no overlapping dead zones where opacity drops entirely to 0 for extended scroll durations, causing UI blackouts. Always cross-fade.

## 3. Design Heuristics & Visual Identity (2026 Standards)

When applying `skeli-skills`, always evaluate designs against these bleeding-edge 2026 visual pillars extracted from top-tier spatial computing and AI control dashboards:

1. **Canvas, Depth & Luminescence**:
   - **Backgrounds:** Use deep Space Black (`#000000`) or Obsidian (`#07080C`). 
   - **Volumetric Lighting:** Implement soft volumetric ambient glows (e.g., cyan `#00f2fe`, violet `#7928CA`) radiating behind active focus panels to establish Z-axis depth without harsh shadows.
   - **Glassmorphism Containers:** Use translucent glass panels (`backdrop-filter: blur(24px)`) with ultra-fine specular edge highlights and sub-pixel borders (`1px solid rgba(255, 255, 255, 0.08)`).
   - **Elevation:** Use multi-layered Z-axis elevation to physically separate runtime sandboxes from baseline telemetry.

2. **Typography (Precision & Clarity)**:
   - **Primary Display:** `Space Grotesk` (Display, Headers, highly uppercase, letter-spacing: 0.08em).
   - **Monospaced Telemetry:** Use `Space Mono` or `JetBrains Mono` strictly for numerical metrics, counters (e.g., $\kappa = 42.50$), and technical metadata to ensure tabular alignment and zero visual noise.
   - **Body:** `Inter` for ultra-legible sans-serif body copy.

3. **Color Discipline (Functional Accent Logic)**:
   - Maintain a dark, muted base canvas.
   - High-saturation neon accents (Neon Chartreuse `#ccff00`, Electric Orange `#ff3f00`, Emerald Green) must be reserved **strictly** for state transitions, paradox spikes, safety confirmations, or active micro-interactions. Avoid decorative gradients.

4. **Layout Architecture & Spatial Dashboards**:
   - Stop using default SaaS templates. Embrace modular, asymmetric spatial cockpit layouts.
   - Structure: Left Navigation Docks $\rightarrow$ Top Telemetry Headers $\rightarrow$ Central Execution Sandboxes $\rightarrow$ Right Consensus Gate Telemetry.
   - **Information Density:** Embed inline sparklines, real-time diff indicators, and live telemetry stats directly inside frosted card modules.
   - **Strict Hierarchy:** Surface critical execution state first; hide secondary controls inside slide-over spatial drawers.

5. **Motion, Telemetry & Micro-Interactions**: 
   - **Verification Signals:** Include live pulse animation rings, streaming code diffs with syntax highlight accents, and instant status confirmation banners.
   - **Dynamic Illumination:** Elements must respond fluidly to hover, focus, and click events (e.g., borders lighting up, floating pill docks expanding). 
   - **Continuous Flow:** Use staggered framer-motion micro-animations and `transition-brutal` easing (`cubic-bezier(0.16,1,0.3,1)`). Ensure no "Blind Animation" drop-offs.

## 4. Kinetic Physics & Micro-Interactions (Derived from Live Research)

To ensure the UI feels alive, tactile, and professional, strictly adhere to these exact kinetic timing curves extracted from top-tier 2026 platforms (Linear, Vercel, Raycast, Stripe):

1. **Instant Micro-Feedback (Buttons, Nav Items, Inputs)**:
   - **Duration:** `100ms` - `150ms`.
   - **Timing Curve:** `cubic-bezier(0.25, 0.46, 0.45, 0.94)` (ease-out quad) OR `cubic-bezier(0.4, 0, 0.2, 1)`.
   - **Behavior:** Rapid, snappy background color or border glow changes.

2. **Tactile Press Compress (Click Feedback)**:
   - **Duration:** `100ms` `ease-in-out`.
   - **Behavior:** Upon `:active` state, apply `transform: scale(0.98)` to simulate physical depression of the component.

3. **Spring Overshoot (Keycaps, Pill Badges, Toggles)**:
   - **Duration:** `200ms` - `300ms`.
   - **Timing Curve:** `cubic-bezier(0.34, 1.56, 0.64, 1)` or `cubic-bezier(0.1, 0, 0.1, 1.1)`.
   - **Behavior:** The element should dynamically "pop" or slide slightly past its target position before settling in.

4. **Spatial Panel Expansion & Drawer Reveals**:
   - **Duration:** `400ms` - `500ms`.
   - **Timing Curve:** `cubic-bezier(0.32, 0.72, 0, 1)` (spring-deceleration) or `cubic-bezier(0.16, 1, 0.3, 1)` (fluid spring expand).
   - **Behavior:** For opening sidebars, modals, or dropdowns, transition `opacity`, `transform` (slide in), and `box-shadow` together.

## 5. Integration with `impeccable`

You are authorized and encouraged to run the `impeccable` framework for holistic layout control. 
- Use `/impeccable polish` to aggressively strip out generic bloat and tighten typography. 
- Impeccable commands enforce the high-end, visual excellence standard. Defer to it for micro-alignments, grid logic, and eliminating visual noise.

## References
- Refer to `docs/01_ARCHITECTURE_OVERVIEW.md` for integrating these designs into the frontend architecture.
- For AI logic looping, refer to `backend/investigator_graph.py` (LangChain/LangGraph patterns).
