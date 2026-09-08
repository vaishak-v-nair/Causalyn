"""Native Acceleration Engine for Causalyn & VPSN.

Provides microsecond-latency routines for:
1. Shannon entropy analysis to detect high-entropy credential leakage
2. Pairwise SHA-256 Merkle root computation over candidate states
3. Continuous Symplectic Curvature tensor calculation for the Vaishak Continuum

Seamlessly loads compiled native library (Rust crates/causalyn-core) via ctypes
if present, or transparently falls back to optimized vectorized pure-Python routines.
"""

from __future__ import annotations

import ctypes
import hashlib
import math
import os
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple


class NativeKernelBridge:
    """Interface to native causalyn-core library with automatic fallback."""

    def __init__(self, lib_path: Optional[str] = None) -> None:
        self._lib: Optional[ctypes.CDLL] = None
        self._is_native = False
        self._init_native(lib_path)

    def _init_native(self, custom_path: Optional[str] = None) -> None:
        search_paths = []
        if custom_path:
            search_paths.append(custom_path)

        # Look in crate target directories
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        crate_target = os.path.join(base_dir, "crates", "causalyn-core", "target", "release")
        
        if sys.platform == "win32":
            search_paths.extend([
                os.path.join(crate_target, "causalyn_core.dll"),
                os.path.join(base_dir, "causalyn_core.dll"),
            ])
        elif sys.platform == "darwin":
            search_paths.extend([
                os.path.join(crate_target, "libcausalyn_core.dylib"),
                os.path.join(base_dir, "libcausalyn_core.dylib"),
            ])
        else:
            search_paths.extend([
                os.path.join(crate_target, "libcausalyn_core.so"),
                os.path.join(base_dir, "libcausalyn_core.so"),
            ])

        for p in search_paths:
            if os.path.isfile(p):
                try:
                    lib = ctypes.CDLL(p)
                    # Bind signatures
                    lib.causalyn_compute_entropy.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
                    lib.causalyn_compute_entropy.restype = ctypes.c_double

                    lib.causalyn_compute_merkle_root.argtypes = [
                        ctypes.c_char_p,
                        ctypes.c_size_t,
                        ctypes.c_char_p,
                    ]
                    lib.causalyn_compute_merkle_root.restype = ctypes.c_int

                    lib.causalyn_compute_symplectic_curvature.argtypes = [
                        ctypes.c_double,
                        ctypes.c_double,
                        ctypes.c_double,
                        ctypes.c_double,
                        ctypes.c_double,
                        ctypes.c_double,
                    ]
                    lib.causalyn_compute_symplectic_curvature.restype = ctypes.c_double

                    self._lib = lib
                    self._is_native = True
                    break
                except Exception:
                    continue

    @property
    def is_native(self) -> bool:
        """True if running compiled Rust kernel, False if running pure-Python fallback."""
        return self._is_native

    def compute_shannon_entropy(self, data: str | bytes) -> float:
        """Computes Shannon entropy: H = - sum(p_i * log2(p_i))."""
        raw_bytes = data.encode("utf-8") if isinstance(data, str) else data
        if not raw_bytes:
            return 0.0

        if self._is_native and self._lib:
            try:
                return float(self._lib.causalyn_compute_entropy(raw_bytes, len(raw_bytes)))
            except Exception:
                pass

        # Optimized pure-Python fallback
        length = len(raw_bytes)
        counts: Dict[int, int] = {}
        for b in raw_bytes:
            counts[b] = counts.get(b, 0) + 1

        entropy = 0.0
        for count in counts.values():
            p = count / length
            entropy -= p * math.log2(p)
        return float(entropy)

    def scan_high_entropy_tokens(
        self, text: str, threshold: float = 4.3, min_token_len: int = 20
    ) -> List[Dict[str, Any]]:
        """Scans text for high-entropy tokens (e.g. leaked API keys, tokens, private hashes)."""
        findings = []
        # Code punctuation delimiters (preserve dashes and underscores for token continuity)
        delimiters = " \t\r\n\"'=:;,().[]{}<>+*/|&!~^#@?`"
        current_token: List[str] = []

        def check_token(t: str):
            if len(t) >= min_token_len:
                # Disallow common code brackets or slashes
                if any(c in t for c in ("\\", "/", "(", ")", "[", "]", "{", "}")):
                    return
                has_upper = any(c.isupper() for c in t)
                has_lower = any(c.islower() for c in t)
                has_digit = any(c.isdigit() for c in t)
                # True secrets have mixed character types (letters + digits) or high variety
                if (has_upper and has_lower and has_digit) or (has_digit and (has_upper or has_lower) and len(t) >= 16):
                    ent = self.compute_shannon_entropy(t)
                    if ent >= threshold:
                        findings.append({
                            "token": t[:6] + "..." + t[-4:],
                            "entropy": round(ent, 4),
                            "length": len(t),
                            "threshold": threshold,
                        })

        for char in text:
            if char in delimiters:
                if current_token:
                    check_token("".join(current_token))
                    current_token = []
            else:
                current_token.append(char)
        if current_token:
            check_token("".join(current_token))

        return findings

    def compute_merkle_root(self, leaf_hashes: Sequence[str | bytes]) -> str:
        """Computes a deterministic pairwise SHA-256 Merkle root from hex/byte leaf hashes."""
        if not leaf_hashes:
            return hashlib.sha256(b"").hexdigest()

        # Normalize to 32-byte raw bytes
        normalized: List[bytes] = []
        for h in leaf_hashes:
            if isinstance(h, str):
                normalized.append(bytes.fromhex(h) if len(h) == 64 else hashlib.sha256(h.encode("utf-8")).digest())
            else:
                normalized.append(h if len(h) == 32 else hashlib.sha256(h).digest())

        if self._is_native and self._lib:
            try:
                buf = b"".join(normalized)
                out_buf = ctypes.create_string_buffer(32)
                res = self._lib.causalyn_compute_merkle_root(buf, len(normalized), out_buf)
                if res == 0:
                    return out_buf.raw.hex()
            except Exception:
                pass

        # Optimized pure-Python fallback
        current_layer = list(normalized)
        while len(current_layer) > 1:
            next_layer = []
            for i in range(0, len(current_layer), 2):
                left = current_layer[i]
                right = current_layer[i + 1] if i + 1 < len(current_layer) else left
                combined = hashlib.sha256(left + right).digest()
                next_layer.append(combined)
            current_layer = next_layer

        return current_layer[0].hex()

    def compute_symplectic_curvature(
        self,
        t: float,
        cs: float,
        cc: float,
        grad_i: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> float:
        r"""Computes continuous symplectic curvature metric for the Vaishak Continuum:
        κ = ||∇ I|| * (1.0 - tanh(c_s * c_c)) / (1.0 + 0.05 * max(0, t))
        """
        gx, gy, gz = grad_i
        if self._is_native and self._lib:
            try:
                return float(
                    self._lib.causalyn_compute_symplectic_curvature(
                        float(t), float(cs), float(cc), float(gx), float(gy), float(gz)
                    )
                )
            except Exception:
                pass

        grad_norm = math.sqrt(gx * gx + gy * gy + gz * gz)
        admissibility = max(0.0, min(1.0, math.tanh(cs * cc)))
        decay = 1.0 / (1.0 + 0.05 * max(0.0, t))
        curvature = grad_norm * (1.0 - admissibility) * decay
        return max(0.0, float(curvature))


# Global singleton
_KERNEL_INSTANCE = NativeKernelBridge()


def get_native_accelerator() -> NativeKernelBridge:
    """Returns the global native acceleration kernel instance."""
    return _KERNEL_INSTANCE
