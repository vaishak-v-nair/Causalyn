import sys
import causalyn
import causalyn.verification
import causalyn.verification.kappa_engine
import causalyn.verification.cegar_loop
import causalyn.shadow
import causalyn.shadow.ambient_fabric

# Backward-compatible re-export alias for legacy modules
sys.modules["backend.source"] = causalyn
sys.modules["backend.source.verification"] = causalyn.verification
sys.modules["backend.source.verification.kappa_engine"] = causalyn.verification.kappa_engine
sys.modules["backend.source.verification.cegar_loop"] = causalyn.verification.cegar_loop
sys.modules["backend.source.shadow"] = causalyn.shadow
sys.modules["backend.source.shadow.ambient_fabric"] = causalyn.shadow.ambient_fabric
source = causalyn
