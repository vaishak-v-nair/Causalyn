"""Unit tests for the Deterministic Verification Certificate Generator."""

from pathlib import Path
import pytest
from causalyn.compliance.certificate import VerificationCertificateGenerator, RICCI_FLOW_SVG_DIAGRAM


def test_generate_html_certificate_defaults(tmp_path: Path):
    generator = VerificationCertificateGenerator(workspace_root=tmp_path)
    html = generator.generate_html_certificate()

    assert "<!DOCTYPE html>" in html
    assert "Causalyn Autonomous Formal Hypervisor" in html
    assert "Deterministic Verification Certificate" in html
    assert "Theorem 1 (Acausal Semantic Nullification &amp; Convergence)" in html
    assert "INV_MAX_THREADS" in html
    assert "FORBID_DB_DROP" in html
    assert "EU AI Act (Regulation 2024/1689) Article 10" in html
    assert "SOC2 Type II Trust Services Criteria" in html
    assert "<svg viewBox=" in html
    assert "Semantic Ricci Flow" in html
    assert "CRYPTOGRAPHIC MERKLE STATE ROOT" in html


def test_generate_html_certificate_custom_metadata(tmp_path: Path):
    generator = VerificationCertificateGenerator(workspace_root=tmp_path)
    custom_meta = {
        "cert_id": "CERT-CUSTOM-9999",
        "project_name": "DeepMind-Autonomous-Suite",
        "agent_id": "claude-3-7-sonnet-researcher",
        "merkle_root": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "hashes": ["0x111111", "0x222222", "0x333333", "0x444444"]
    }
    html = generator.generate_html_certificate(metadata=custom_meta)

    assert "CERT-CUSTOM-9999" in html
    assert "DeepMind-Autonomous-Suite" in html
    assert "claude-3-7-sonnet-researcher" in html
    assert "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" in html
    assert "0x111111 &rarr; 0x222222 &rarr; 0x333333 &rarr; 0x444444" in html


def test_generate_html_dynamic_proof_matrix_and_svg(tmp_path: Path):
    """Verify certificate dynamically reflects real invariant results and real measured latency."""
    generator = VerificationCertificateGenerator(workspace_root=tmp_path)
    custom_invariants = [
        {
            "id": "CUSTOM_TENSOR_DIM_INVARIANT",
            "specification": "dim(tensor) == [B, 128, 768]",
            "engine": "Z3 Tensor Shape SMT",
            "measured": "dim = [B, 128, 768]",
            "status": "PASS",
        },
        {
            "id": "CUSTOM_GPU_MEMORY_CEILING",
            "specification": "gpu_vram <= 24GB",
            "engine": "CUDA Runtime Monitor",
            "measured": "vram = 32GB",
            "status": "VIOLATED",
        },
    ]

    html = generator.generate_html_certificate(metadata={
        "latency_us": 18.75,
        "initial_kappa": 0.85,
        "final_kappa": 0.0,
        "invariant_results": custom_invariants,
    })

    assert "CUSTOM_TENSOR_DIM_INVARIANT" in html
    assert "CUSTOM_GPU_MEMORY_CEILING" in html
    assert "SATISFIED" in html
    assert "VIOLATED" in html
    assert "18.8µs" in html
    assert "18.75" in html


@pytest.mark.asyncio
async def test_compile_pdf_async(tmp_path: Path):
    generator = VerificationCertificateGenerator(workspace_root=tmp_path)
    out_pdf = tmp_path / "test_audit.pdf"

    result_path = await generator.compile_pdf(output_path=out_pdf)

    assert result_path.exists()
    assert result_path == out_pdf
    pdf_bytes = out_pdf.read_bytes()
    assert len(pdf_bytes) > 5000
    assert pdf_bytes.startswith(b"%PDF")


def test_compile_pdf_sync(tmp_path: Path):
    generator = VerificationCertificateGenerator(workspace_root=tmp_path)
    out_pdf = tmp_path / "test_sync_audit.pdf"

    result_path = generator.compile_pdf_sync(output_path=out_pdf)

    assert result_path.exists()
    assert result_path == out_pdf
    pdf_bytes = out_pdf.read_bytes()
    assert len(pdf_bytes) > 5000
    assert pdf_bytes.startswith(b"%PDF")
