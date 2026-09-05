from manim import *

class ParadoxIndexScene(Scene):
    def construct(self):
        # Color constants
        INDIGO = "#6366f1"
        CRIMSON = "#ff3f00"
        EMERALD = "#10b981"

        # Background color
        self.camera.background_color = "#030509" # Match Causalyn UI theme

        # Title
        title = Text("The Paradox Index", font_size=40, color=WHITE)
        kappa_sym = Text("κ", font_size=60, color=CRIMSON, font="Arial")
        kappa_sym.next_to(title, RIGHT, buff=0.3)
        title_group = VGroup(title, kappa_sym).center().to_edge(UP, buff=0.5)

        self.play(Write(title), FadeIn(kappa_sym, scale=1.5), run_time=0.8)

        # Formula
        formula = VGroup(
            Text("κ", font="Arial"),
            Text("="),
            Text("Σ"),
            Text("ω"),
            Text("·"),
            Text("P(Sc, Sl)")
        ).arrange(RIGHT, buff=0.2).scale(1.1).center()
        
        formula[0].set_color(CRIMSON)
        formula[3].set_color(INDIGO)
        formula[5].set_color(EMERALD)

        self.play(FadeIn(formula, shift=UP * 0.5), run_time=0.6)

        # Annotations
        brace_omega = Brace(formula[3], DOWN, color=INDIGO)
        label_omega = Text("Verifier Weight", font_size=20, color=INDIGO)
        label_omega.next_to(brace_omega, DOWN)

        brace_pv = Brace(formula[5], DOWN, color=EMERALD)
        label_pv = Text("Penalty Function", font_size=20, color=EMERALD)
        label_pv.next_to(brace_pv, DOWN)

        self.play(GrowFromCenter(brace_omega), Write(label_omega), run_time=0.5)
        self.play(GrowFromCenter(brace_pv), Write(label_pv), run_time=0.5)
        
        self.wait(0.5)

        # Dynamic spike demonstration
        self.play(
            FadeOut(brace_omega), FadeOut(label_omega),
            FadeOut(brace_pv), FadeOut(label_pv),
            formula.animate.shift(UP * 1.5),
            run_time=0.5
        )

        spike_text = Text("κ = 20.00", font_size=60, color=CRIMSON, font="Arial")
        spike_text.next_to(formula, DOWN, buff=1)
        
        box = SurroundingRectangle(spike_text, color=CRIMSON, buff=0.3)
        
        self.play(FadeIn(spike_text, scale=0.5), Create(box), run_time=0.5)
        self.play(Flash(spike_text, color=CRIMSON, line_length=0.5), run_time=0.5)

        # Conclusion
        conclusion = Text(
            "CATASTROPHIC DIVERGENCE DETECTED",
            font_size=24, color=CRIMSON, weight=BOLD
        ).to_edge(DOWN, buff=0.8)

        self.play(Write(conclusion), run_time=0.6)
        self.wait(1.5)
