import hashlib
import os
import tempfile
import base64
import threading
from pathlib import Path
from typing import Dict, Any

try:
    from manim import *
    import numpy as np
    HAS_MANIM = True

    # Adjust manim global config for bright, radiant headless rendering
    config.background_color = "#F8FAFC"  # Beautiful bright pearl background
    config.pixel_width = 800
    config.pixel_height = 450
    config.frame_rate = 15

    class SymplecticManifoldScene(ThreeDScene):
        def __init__(self, kappa: float, **kwargs):
            self.kappa = kappa
            super().__init__(**kwargs)

        def construct(self):
            # Setup camera with elegant isometric perspective
            self.set_camera_orientation(phi=60 * DEGREES, theta=45 * DEGREES, zoom=0.85)

            # Create the parametric surface representing the Vaishak Continuum
            # z = sin(u)cos(v) + kappa * e^{-(u^2 + v^2)}
            def param_surface(u, v):
                z = np.sin(u) * np.cos(v) + self.kappa * np.exp(-(u**2 + v**2))
                return np.array([u, v, z])

            surface = Surface(
                param_surface,
                u_range=[-3, 3],
                v_range=[-3, 3],
                resolution=(32, 32)
            )
            
            # Bright, luminous palette: Vivid Indigo for Safe vs Vibrant Crimson for Paradox
            if self.kappa > 0:
                surface.set_style(
                    fill_opacity=0.75, 
                    stroke_color="#BE123C", 
                    stroke_width=1.2, 
                    fill_color="#E11D48"
                )
            else:
                surface.set_style(
                    fill_opacity=0.75, 
                    stroke_color="#3730A3", 
                    stroke_width=1.2, 
                    fill_color="#4F46E5"
                )

            self.add(surface)

            # Animate rotation for 2 seconds
            self.play(Rotate(surface, angle=PI/2, axis=UP), run_time=2.0)

except ImportError:
    HAS_MANIM = False
    SymplecticManifoldScene = None

class ManimEngine:
    def __init__(self):
        self.cache: Dict[str, str] = {}  # sha256 -> base64 mp4
        self.output_dir = Path(tempfile.mkdtemp(prefix="causalyn_manim_bright_"))
        self._render_lock = threading.Lock()
        self._prewarm_cache()

    def _prewarm_cache(self):
        """Pre-loads rendered Manim scenes into memory cache for instantaneous responses."""
        repo_root = Path(__file__).resolve().parent.parent.parent
        video_map = {
            0.0: repo_root / "web" / "assets" / "manim" / "videos" / "semantic_nullification" / "480p15" / "SemanticNullificationScene.mp4",
            1.0: repo_root / "web" / "assets" / "manim" / "videos" / "paradox_index" / "480p15" / "ParadoxIndexScene.mp4",
            float('inf'): repo_root / "web" / "assets" / "manim" / "videos" / "acausal_compiler" / "480p15" / "AcausalCompilerScene.mp4",
            999.0: repo_root / "web" / "assets" / "manim" / "videos" / "acausal_compiler" / "480p15" / "AcausalCompilerScene.mp4",
        }
        for kappa_val, path in video_map.items():
            if path.exists():
                try:
                    with open(path, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode("utf-8")
                    self.cache[self.compute_hash(kappa_val)] = b64
                except Exception as e:
                    print(f"[ManimEngine] Could not pre-cache {path}: {e}")

    def compute_hash(self, kappa: float) -> str:
        data = f"bright_kappa:{kappa:.4f}"
        return hashlib.sha256(data.encode()).hexdigest()

    def render_state(self, kappa: float) -> str:
        """
        Renders the mathematical manifold based on kappa in bright aesthetic.
        Returns the base64 encoded MP4 video. Thread-safe and cache-backed.
        """
        state_hash = self.compute_hash(kappa)
        
        if state_hash in self.cache:
            return self.cache[state_hash]

        # Check for close canonical matches before heavy rendering
        if kappa == 0.0 or abs(kappa) < 1e-4:
            canonical_hash = self.compute_hash(0.0)
            if canonical_hash in self.cache:
                return self.cache[canonical_hash]
        elif abs(kappa - 1.0) < 1e-4:
            canonical_hash = self.compute_hash(1.0)
            if canonical_hash in self.cache:
                return self.cache[canonical_hash]
        elif kappa >= 100.0 or math.isinf(kappa):
            canonical_hash = self.compute_hash(999.0)
            if canonical_hash in self.cache:
                return self.cache[canonical_hash]

        if not HAS_MANIM:
            # Fallback to pre-rendered canonical videos
            target_kappa = 1.0 if kappa > 0.5 else 0.0
            canonical_h = self.compute_hash(target_kappa)
            return self.cache.get(canonical_h, "")

        with self._render_lock:
            # Re-check cache after acquiring lock
            if state_hash in self.cache:
                return self.cache[state_hash]

            # Programmatically render scene
            scene = SymplecticManifoldScene(kappa=kappa)
            
            out_file = self.output_dir / f"{state_hash}.mp4"
            config.media_dir = str(self.output_dir)
            config.output_file = str(out_file)
            config.format = "mp4"
            config.quality = "low_quality"
            config.disable_caching = True
            
            try:
                scene.render()
                videos = list(self.output_dir.rglob("*.mp4"))
                if not videos:
                    return ""
                    
                latest_video = max(videos, key=os.path.getctime)

                with open(latest_video, "rb") as f:
                    b64_vid = base64.b64encode(f.read()).decode("utf-8")
                    
                self.cache[state_hash] = b64_vid
                try:
                    os.remove(latest_video)
                except Exception:
                    pass
                return b64_vid
            except Exception as e:
                print(f"[ManimEngine] Rendering error: {e}")
                return ""
