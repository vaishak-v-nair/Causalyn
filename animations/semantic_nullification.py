from manim import *

class SemanticNullificationScene(Scene):
    def construct(self):
        CRIMSON = "#ff3f00"
        EMERALD = "#10b981"
        INDIGO = "#6366f1"

        # Background color
        self.camera.background_color = "#030509" # Match Causalyn UI theme

        title = Text("Semantic Nullification", font_size=40).to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=0.6)

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
            run_time=0.8
        )
        self.wait(0.5)

        # Kappa spike
        kappa_badge = Text("κ = 20.00", color=CRIMSON, font_size=40, font="Arial")
        kappa_badge.shift(DOWN * 2.5)
        self.play(Write(kappa_badge), run_time=0.5)
        self.wait(0.3)

        # Annihilation of shadow
        self.play(
            shadow_box.animate.set_fill(CRIMSON, opacity=0.4),
            Flash(shadow_box.get_center(), color=CRIMSON, line_length=0.8),
            run_time=0.5
        )
        annihilate_text = Text("ANNIHILATED", font_size=24, color=CRIMSON)
        annihilate_text.move_to(shadow_box.get_center())
        cross = Cross(shadow_box, color=CRIMSON, stroke_width=6)
        
        self.play(
            FadeOut(shadow_mutation),
            Write(annihilate_text),
            Create(cross),
            run_time=0.6
        )

        # Production untouched
        check = Text("✓ UNCHANGED", font_size=24, color=EMERALD)
        check.next_to(prod_box, DOWN)
        self.play(Write(check), run_time=0.5)
        self.wait(1.5)
