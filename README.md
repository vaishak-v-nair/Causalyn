# Causalyn

Causalyn is a local full-stack interface for the Epoch-V Prototype 001 constraint-gated AI tool.

## Run

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:8000`. The UI sends human intent to the local API, which runs the existing pipeline:

`Intent Translator -> Shadow Execution -> Verification -> Authorization -> Commit Boundary`

The supported server is FastAPI/Uvicorn. It adds typed request validation, request IDs,
serialized pipeline execution, and a SQLite audit store at `runtime/causalyn.sqlite3`.
Set `CAUSALYN_DB` to move that store. This is an M1 implementation analogue, not a proof
of VPSN theory.

## Test

```powershell
python -m unittest discover -s tests -v
```

## Epoch-V numerical runtime

`epoch_v/` is an M1 experimental approximation of the VPSN vocabulary: it encodes
an Intent Vector as a symmetric matrix, models the authentication Ambient Fabric
as three finite-dimensional coordinates, and runs a constraint-gated,
geometry-inspired optimizer. `R_APPROX` is explicitly a state-energy surrogate,
not an exact Ricci tensor; κ is the sum of executable invariant violations.
Nothing here claims to prove VPSN, acausal computation, or flawless software.

Run the dependency-free experiment with:

```powershell
python -m epoch_v.experiment
python -m unittest discover -s epoch_v/tests -v
```

PyTorch is optional. If installed, the solver uses differentiable `torch.Tensor`
state and Adam; otherwise a deterministic projected-gradient fallback is used.
The fallback keeps the prototype runnable but does not provide autograd evidence.
The current hypothesis is falsified if repeated adversarial cases fail to reduce κ
or converge while an invariant remains violated. Sentence-transformers are not
downloaded by default; the deterministic hash encoder is a baseline surrogate.
