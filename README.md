# Causalyn

Causalyn is a local full-stack interface for the Epoch-V Prototype 001 constraint-gated AI tool.

## Run

```powershell
python app.py
```

Open `http://127.0.0.1:8000`. The UI sends human intent to the local API, which runs the existing pipeline:

`Intent Translator -> Shadow Execution -> Verification -> Authorization -> Commit Boundary`

This is an M1 implementation analogue, not a proof of VPSN theory.

## Test

```powershell
python -m unittest discover -s tests -v
```
