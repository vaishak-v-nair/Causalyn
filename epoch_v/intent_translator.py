from dataclasses import dataclass
from typing import Any, Mapping, Union
import hashlib

try:
    import torch
    _TORCH = True
except ImportError:
    torch = None
    _TORCH = False

@dataclass(frozen=True)
class IntentMatrix:
    tensor: Any
    shape: tuple
    dtype: str
    device: str
    provenance: Mapping[str, Any]
    model_identifier: str

class IntentTranslator:
    """Deterministic baseline encoder; optional sentence-transformers are not required."""
    def __init__(self, dimension: int = 3, model_identifier: str = "hash-baseline-v1"):
        self.dimension = dimension
        self.model_identifier = model_identifier

    def encode(self, requirement: Union[str, Mapping[str, Any]]) -> IntentMatrix:
        text = requirement if isinstance(requirement, str) else repr(sorted(requirement.items()))
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values = [((digest[i] / 255.0) * 2.0 - 1.0) for i in range(self.dimension ** 2)]
        matrix = [values[i*self.dimension:(i+1)*self.dimension] for i in range(self.dimension)]
        matrix = [[(matrix[i][j] + matrix[j][i]) / 2 for j in range(self.dimension)]
                  for i in range(self.dimension)]
        if _TORCH:
            tensor = torch.tensor(matrix, dtype=torch.float32)
            dtype, device = str(tensor.dtype), str(tensor.device)
        else:
            tensor, dtype, device = matrix, "float32", "cpu"
        return IntentMatrix(tensor, (self.dimension, self.dimension), dtype, device,
                            {"input_type": type(requirement).__name__, "encoding": "deterministic hash"},
                            self.model_identifier)
