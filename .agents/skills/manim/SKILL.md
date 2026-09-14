---
name: manim
description: Generates programmatic mathematical animations and visual explanations using 3b1b/manim. Ideal for animating Causalyn's Semantic Nullification theories and the Paradox Index (\kappa).
---

# Manim Programmatic Animation Skill

Use this skill when the user asks for explanatory videos, mathematical animations, or visual proofs of Causalyn theories (such as the Paradox Index $\kappa$, Semantic Nullification, or the Vaishak Operator $\Upsilon$).

## Prerequisites

```bash
pip install manim
# Requires: Python 3.9+, FFmpeg, LaTeX (MiKTeX/TeX Live) for formula rendering
```

## Core Principles

1. **Use `manim` library**: Generate Python scripts that subclass `Scene`, `MovingCameraScene`, or `ThreeDScene` from `manim`.
2. **Mathematical Rigor**: Use LaTeX for all formulas via `MathTex`. Keep animations precise, clean, and pedagogical.
3. **Color Discipline**: Use the Causalyn color palette:
   - Safe/Equilibrium: Indigo `#6366f1`
   - Danger/Paradox: Neon Crimson `#ff3f00`
   - Nullification: Electric Emerald `#10b981`
   - Neutral: `#94a3b8`
4. **Causalyn Context**: Animate these specific theoretical constructs:
   - The State Manifold and candidate trajectories
   - The divergence of Candidate States $S_c$ from Legal States $S_l$
   - The Paradox Index $\kappa$ calculation and spike
   - Semantic Nullification (annihilation of invalid states)
   - The Vaishak Operator $\Upsilon(\kappa, f)$
   - CEGAR refinement loop convergence

## Animation Templates

### 1. Paradox Index Formula Introduction
```python
from manim import *

class ParadoxIndexScene(Scene):
    def construct(self):
        # Color constants
        INDIGO = "#6366f1"
        CRIMSON = "#ff3f00"
        EMERALD = "#10b981"

        # Title
        title = Text("The Paradox Index", font_size=48, color=WHITE)
        kappa_sym = MathTex(r"\kappa", font_size=72, color=CRIMSON)
        kappa_sym.next_to(title, RIGHT, buff=0.3)
        title_group = VGroup(title, kappa_sym).center().to_edge(UP, buff=1)

        self.play(Write(title), FadeIn(kappa_sym, scale=1.5))
        self.wait(0.5)

        # Formula
        formula = MathTex(
            r"\kappa", r"=", r"\sum_{v \in V}",
            r"\omega_v", r"\cdot", r"P_v(S_c, S_l)"
        ).scale(1.3).center()
        formula[0].set_color(CRIMSON)
        formula[3].set_color(INDIGO)
        formula[5].set_color(EMERALD)

        self.play(FadeIn(formula, shift=UP * 0.5))
        self.wait(1)

        # Annotations
        brace_omega = Brace(formula[3], DOWN, color=INDIGO)
        label_omega = Text("Verifier Weight", font_size=20, color=INDIGO)
        label_omega.next_to(brace_omega, DOWN)

        brace_pv = Brace(formula[5], DOWN, color=EMERALD)
        label_pv = Text("Penalty Function", font_size=20, color=EMERALD)
        label_pv.next_to(brace_pv, DOWN)

        self.play(GrowFromCenter(brace_omega), Write(label_omega))
        self.wait(0.5)
        self.play(GrowFromCenter(brace_pv), Write(label_pv))
        self.wait(1)

        # Conclusion
        conclusion = Text(
            "κ = 0 → Admissible     κ > 0 → Annihilated",
            font_size=28, color=WHITE
        ).to_edge(DOWN, buff=1)
        conclusion[4:5].set_color(EMERALD)
        conclusion[-1:].set_color(CRIMSON)

        self.play(Write(conclusion))
        self.wait(2)
```

### 2. State Manifold Divergence (2D Phase Portrait)
```python
from manim import *
import numpy as np

class StateManifoldScene(Scene):
    def construct(self):
        INDIGO = "#6366f1"
        CRIMSON = "#ff3f00"
        EMERALD = "#10b981"

        # Title
        title = Text("State Manifold Divergence", font_size=36).to_edge(UP)
        self.play(Write(title))

        # Axes
        axes = Axes(
            x_range=[0, 6, 1], y_range=[0, 5, 1],
            x_length=8, y_length=5,
            axis_config={"color": "#475569"},
        ).shift(DOWN * 0.3)
        x_label = axes.get_x_axis_label("t", direction=RIGHT)
        y_label = axes.get_y_axis_label("S", direction=UP)
        self.play(Create(axes), Write(x_label), Write(y_label))

        # Legal trajectory (stable)
        legal_curve = axes.plot(
            lambda x: 2 + 0.3 * np.sin(x * 1.5),
            x_range=[0, 5.5], color=EMERALD, stroke_width=3,
        )
        legal_label = Text("S_l (Legal)", font_size=20, color=EMERALD)
        legal_label.next_to(legal_curve, UP, buff=0.2).shift(RIGHT * 2)

        # Candidate trajectory (diverging)
        candidate_curve = axes.plot(
            lambda x: 2 + 0.3 * np.sin(x * 1.5) + 0.15 * x**2,
            x_range=[0, 5.5], color=CRIMSON, stroke_width=3,
        )
        candidate_label = Text("S_c (Candidate)", font_size=20, color=CRIMSON)
        candidate_label.next_to(candidate_curve, UP, buff=0.2).shift(LEFT)

        self.play(Create(legal_curve), Write(legal_label))
        self.wait(0.5)
        self.play(Create(candidate_curve), Write(candidate_label))
        self.wait(0.5)

        # Divergence region
        divergence_arrow = Arrow(
            axes.c2p(4, 2.3), axes.c2p(4, 4.5),
            color=CRIMSON, buff=0.1, stroke_width=2,
        )
        div_label = MathTex(r"\kappa > 0", font_size=32, color=CRIMSON)
        div_label.next_to(divergence_arrow, RIGHT)

        self.play(GrowArrow(divergence_arrow), Write(div_label))
        self.wait(1)

        # Annihilation flash
        flash = Flash(axes.c2p(4, 4.5), color=CRIMSON, line_length=0.4)
        annihilated = Text("ANNIHILATED", font_size=24, color=CRIMSON)
        annihilated.next_to(axes.c2p(4, 4.5), UR)
        self.play(flash, FadeIn(annihilated, scale=0.5))
        self.wait(2)
```

### 3. Vaishak Operator Animation
```python
from manim import *

class VaishakOperatorScene(Scene):
    def construct(self):
        CRIMSON = "#ff3f00"
        EMERALD = "#10b981"
        INDIGO = "#6366f1"

        title = Text("The Vaishak Operator", font_size=42).to_edge(UP)
        self.play(Write(title))

        # Operator definition
        op_def = MathTex(
            r"\Upsilon(\kappa, f) = \begin{cases} "
            r"\text{COMMIT}(f) & \text{if } \kappa = 0 \\ "
            r"\text{ANNIHILATE}(f) & \text{if } \kappa > 0 "
            r"\end{cases}"
        ).scale(0.9)
        self.play(FadeIn(op_def))
        self.wait(1.5)
        self.play(op_def.animate.shift(UP * 0.5))

        # Demonstration with a concrete kappa
        kappa_val = MathTex(r"\kappa = 0.94", color=CRIMSON, font_size=48)
        kappa_val.next_to(op_def, DOWN, buff=1)
        self.play(Write(kappa_val))
        self.wait(0.5)

        # Result
        result = MathTex(
            r"\Upsilon(0.94, f) = \text{ANNIHILATE}(f)",
            color=CRIMSON, font_size=36,
        )
        result.next_to(kappa_val, DOWN, buff=0.8)
        self.play(Write(result))

        # Visual flash
        box = SurroundingRectangle(result, color=CRIMSON, buff=0.2)
        self.play(Create(box))
        self.play(Flash(result.get_center(), color=CRIMSON, line_length=0.6))
        self.wait(1)

        # Safe case
        safe_kappa = MathTex(r"\kappa = 0.00", color=EMERALD, font_size=48)
        safe_result = MathTex(
            r"\Upsilon(0.00, f) = \text{COMMIT}(f)",
            color=EMERALD, font_size=36,
        )
        safe_group = VGroup(safe_kappa, safe_result).arrange(DOWN, buff=0.5)
        safe_group.move_to(ORIGIN)

        self.play(
            FadeOut(op_def), FadeOut(kappa_val),
            FadeOut(result), FadeOut(box),
        )
        self.play(FadeIn(safe_group))
        safe_box = SurroundingRectangle(safe_result, color=EMERALD, buff=0.2)
        self.play(Create(safe_box))
        self.wait(2)
```

### 4. CEGAR Refinement Loop
```python
from manim import *

class CEGARLoopScene(Scene):
    def construct(self):
        INDIGO = "#6366f1"
        CRIMSON = "#ff3f00"
        EMERALD = "#10b981"
        AMBER = "#f59e0b"

        title = Text("CEGAR Verification Loop", font_size=36).to_edge(UP)
        self.play(Write(title))

        # Loop nodes
        nodes = {
            "Abstract":     Circle(radius=0.6, color=INDIGO).shift(LEFT * 3 + UP),
            "Verify":       Circle(radius=0.6, color=AMBER).shift(RIGHT * 0 + UP),
            "Counterexample":Circle(radius=0.6, color=CRIMSON).shift(RIGHT * 3 + UP),
            "Refine":       Circle(radius=0.6, color=EMERALD).shift(RIGHT * 0 + DOWN * 1.5),
        }
        labels = {}
        for name, node in nodes.items():
            label = Text(name, font_size=16, color=WHITE).move_to(node)
            labels[name] = label

        for node in nodes.values():
            self.play(Create(node), run_time=0.3)
        for label in labels.values():
            self.play(Write(label), run_time=0.2)

        # Arrows
        arrows = [
            Arrow(nodes["Abstract"].get_right(), nodes["Verify"].get_left(), color=WHITE, buff=0.1),
            Arrow(nodes["Verify"].get_right(), nodes["Counterexample"].get_left(), color=CRIMSON, buff=0.1),
            Arrow(nodes["Counterexample"].get_bottom(), nodes["Refine"].get_right(), color=AMBER, buff=0.1),
            Arrow(nodes["Refine"].get_left(), nodes["Abstract"].get_bottom(), color=EMERALD, buff=0.1),
        ]
        for arrow in arrows:
            self.play(GrowArrow(arrow), run_time=0.4)

        self.wait(1)

        # Iteration counter
        counter = Text("Iteration: 1", font_size=28, color=WHITE).to_edge(DOWN)
        self.play(Write(counter))

        # Animate 3 refinement iterations
        for i in range(1, 4):
            for arrow in arrows:
                self.play(
                    arrow.animate.set_color(EMERALD),
                    run_time=0.2,
                )
                self.play(
                    arrow.animate.set_color(WHITE),
                    run_time=0.1,
                )
            counter_new = Text(f"Iteration: {i+1}", font_size=28, color=WHITE).to_edge(DOWN)
            self.play(Transform(counter, counter_new), run_time=0.3)

        # Convergence
        converged = Text("✓ CONVERGED — κ = 0.00", font_size=32, color=EMERALD)
        converged.next_to(counter, UP, buff=0.5)
        self.play(Write(converged))
        self.wait(2)
```

### 5. Semantic Nullification Visualization
```python
from manim import *

class SemanticNullificationScene(Scene):
    def construct(self):
        CRIMSON = "#ff3f00"
        EMERALD = "#10b981"
        INDIGO = "#6366f1"

        title = Text("Semantic Nullification", font_size=42).to_edge(UP)
        self.play(Write(title))

        # Production state box
        prod_box = RoundedRectangle(
            width=4, height=2.5, corner_radius=0.2,
            color=EMERALD, fill_opacity=0.1,
        ).shift(LEFT * 3)
        prod_label = Text("Production\nGround Truth", font_size=20, color=EMERALD)
        prod_label.move_to(prod_box.get_top() + DOWN * 0.4)
        prod_hash = Text("hash: a2c4e689...", font_size=14, color="#94a3b8")
        prod_hash.move_to(prod_box.get_center())

        # Shadow sandbox box
        shadow_box = RoundedRectangle(
            width=4, height=2.5, corner_radius=0.2,
            color=CRIMSON, fill_opacity=0.1,
        ).shift(RIGHT * 3)
        shadow_label = Text("Shadow\nSandbox", font_size=20, color=CRIMSON)
        shadow_label.move_to(shadow_box.get_top() + DOWN * 0.4)
        shadow_mutation = Text('"api_secret": "leaked"', font_size=14, color=CRIMSON)
        shadow_mutation.move_to(shadow_box.get_center())

        self.play(
            Create(prod_box), Write(prod_label), Write(prod_hash),
            Create(shadow_box), Write(shadow_label), Write(shadow_mutation),
        )
        self.wait(1)

        # Kappa spike
        kappa_badge = MathTex(r"\kappa = 0.94", color=CRIMSON, font_size=48)
        kappa_badge.shift(DOWN * 2.5)
        self.play(Write(kappa_badge))
        self.wait(0.5)

        # Annihilation of shadow
        self.play(
            shadow_box.animate.set_fill(CRIMSON, opacity=0.4),
            Flash(shadow_box.get_center(), color=CRIMSON, line_length=0.8),
        )
        annihilate_text = Text("ANNIHILATED", font_size=24, color=CRIMSON)
        annihilate_text.move_to(shadow_box.get_center())
        cross = Cross(shadow_box, color=CRIMSON, stroke_width=6)
        self.play(
            FadeOut(shadow_mutation),
            Write(annihilate_text),
            Create(cross),
        )

        # Production untouched
        check = Text("✓ UNCHANGED", font_size=24, color=EMERALD)
        check.next_to(prod_box, DOWN)
        self.play(Write(check))
        self.wait(2)
```

## Execution

To render any animation:

```bash
# Low quality preview (fast iteration)
manim -pql script.py SceneName

# High quality render (1080p, 60fps)
manim -pqh script.py SceneName

# 4K render
manim -pqk script.py SceneName

# Export to GIF
manim -pql --format gif script.py SceneName
```

## File Organization

Place animation scripts under `E:\BrosKi\causalyn\animations\`:
```
animations/
  paradox_index.py
  state_manifold.py
  vaishak_operator.py
  cegar_loop.py
  semantic_nullification.py
```

## Integration Notes

- All animations use the Causalyn color palette for visual consistency with the dashboard.
- The `setContinuumState()` function in `web/app.js` uses the same Crimson/Indigo color mapping.
- Rendered videos can be embedded in documentation or the web dashboard via `<video>` tags.
