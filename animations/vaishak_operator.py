from manim import *

class VaishakOperatorScene(Scene):
    def construct(self):
        CRIMSON = "#e11d48"
        EMERALD = "#059669"
        INDIGO = "#4f46e5"

        self.camera.background_color = "#f8fafd"

        title = Text("The Vaishak Operator", font_size=36, color="#0f172a", font="Arial").to_edge(UP, buff=0.6)
        subtitle = Text("Acausal Gating Boundary Condition", font_size=20, color="#64748b", font="Arial").next_to(title, DOWN, buff=0.2)
        self.play(Write(title), FadeIn(subtitle), run_time=0.7)

        # Operator definition
        op_formula = VGroup(
            Text("Υ(κ, f)  =", font_size=32, color="#0f172a", font="Arial"),
            Text("COMMIT(f)        if κ = 0", font_size=26, color=EMERALD, font="Arial"),
            Text("ANNIHILATE(f)    if κ > 0", font_size=26, color=CRIMSON, font="Arial")
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.35).center().shift(UP * 0.2)

        self.play(FadeIn(op_formula, shift=UP * 0.3), run_time=0.8)
        self.wait(0.5)

        # Demonstration with concrete paradox
        demo_box = RoundedRectangle(width=8, height=2.2, corner_radius=0.15, color="#cbd5e1", fill_opacity=0.4, fill_color="#ffffff").shift(DOWN * 1.8)
        
        kappa_val = Text("Observed Paradox: κ = 1.00", font_size=24, color=CRIMSON, font="Arial").move_to(demo_box.get_top() + DOWN * 0.4)
        result_text = Text("Action: Instantaneous State Annihilation (Zero Disk Mutation)", font_size=18, color=CRIMSON, font="Arial").next_to(kappa_val, DOWN, buff=0.3)
        
        self.play(Create(demo_box), Write(kappa_val), Write(result_text), run_time=0.8)
        self.play(Flash(result_text.get_center(), color=CRIMSON, line_length=0.4), run_time=0.5)
        self.wait(1.0)
