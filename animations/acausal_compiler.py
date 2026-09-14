from manim import *
import numpy as np

class AcausalCompilerScene(Scene):
    def construct(self):
        # Colors
        INDIGO = "#6366f1"
        CRIMSON = "#ff3f00"
        EMERALD = "#10b981"

        # Title
        title = Text("The Acausal Compiler", font_size=42).to_edge(UP)
        subtitle = Text("Eliminating Trial-and-Error Latency via Semantic Ricci Flow", font_size=24, color=INDIGO)
        subtitle.next_to(title, DOWN, buff=0.2)
        
        self.play(Write(title), FadeIn(subtitle))
        self.wait(1)

        # Standard Agent Path
        agent_label = Text("Standard Agent Execution", font_size=20, color=CRIMSON).to_edge(LEFT).shift(UP*1.5)
        self.play(Write(agent_label))

        # Agent Path Line
        agent_path = Line(LEFT * 5, RIGHT * 2, color=WHITE).shift(UP*0.5)
        self.play(Create(agent_path))

        # Compiler Error Wall
        error_wall = Rectangle(height=2, width=0.2, color=CRIMSON, fill_opacity=0.8).move_to(RIGHT * 2 + UP * 0.5)
        error_label = Text("Compiler Error", font_size=16, color=CRIMSON).next_to(error_wall, UP)
        self.play(FadeIn(error_wall), Write(error_label))

        # Collision & Backtracking
        dot1 = Dot(color=CRIMSON).move_to(agent_path.get_start())
        self.play(dot1.animate.move_to(error_wall.get_left()), run_time=1.5, rate_func=linear)
        
        collision_flash = Flash(error_wall.get_left(), color=CRIMSON, line_length=0.5)
        self.play(collision_flash)
        
        # Backtracking
        backtrack_label = Text("Token Waste & Latency", font_size=16, color=CRIMSON).next_to(agent_path, DOWN)
        self.play(dot1.animate.shift(LEFT*2), FadeIn(backtrack_label))
        self.wait(1)

        # Causalyn Path
        causalyn_label = Text("Causalyn Acausal Compiler", font_size=20, color=EMERALD).to_edge(LEFT).shift(DOWN*1.5)
        self.play(Write(causalyn_label))

        # Axes for Ricci Flow
        axes = Axes(
            x_range=[0, 8, 1], y_range=[-1, 3, 1],
            x_length=8, y_length=3,
            axis_config={"color": "#475569", "include_numbers": False},
        ).shift(DOWN * 2.5 + RIGHT * 1)
        
        self.play(Create(axes))

        # The Z3 Predictor (Acausal prediction)
        predict_curve = axes.plot(lambda x: 2 * np.exp(-((x - 4)**2)), x_range=[0, 8], color=CRIMSON, stroke_width=2, stroke_opacity=0.5)
        predict_label = Text("Z3 Prediction: Paradox Detected", font_size=14, color=CRIMSON).next_to(predict_curve, UP, buff=0.1)
        self.play(Create(predict_curve), Write(predict_label))
        self.wait(1)

        # Semantic Ricci Flow Auto-Correction
        flow_curve = axes.plot(lambda x: 0.2 * np.sin(x), x_range=[0, 8], color=EMERALD, stroke_width=4)
        flow_label = Text("Semantic Ricci Flow: AST Auto-Corrected", font_size=14, color=EMERALD).next_to(flow_curve, DOWN, buff=0.1)
        
        self.play(Transform(predict_curve, flow_curve), Transform(predict_label, flow_label), run_time=2)
        self.wait(0.5)

        # Smooth Execution
        dot2 = Dot(color=EMERALD).move_to(axes.c2p(0, 0))
        self.play(MoveAlongPath(dot2, flow_curve), run_time=2, rate_func=linear)
        
        success_label = Text("Zero Latency. Flawless Execution.", font_size=20, color=EMERALD).next_to(axes, RIGHT)
        self.play(FadeIn(success_label))
        
        self.wait(2)
