"""Software backend checks with dimensionless synthetic fixtures, not neural data."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import tempfile

import torch

from cerebro.sequence_models import make_sequence_model


MODEL_KINDS = ("mlp", "gru", "lstm", "temporal_cnn", "transformer", "state_space")


def backend_availability():
    """Report actual availability without substituting another device."""
    return {
        "cpu": True,
        "mps": torch.backends.mps.is_available(),
        "cuda": torch.cuda.is_available(),
    }


def check_model(kind, backend, checkpoint_path):
    """Exercise optimization and a weights-only round trip on one backend."""
    if backend == "mps" and os.environ.get("PYTORCH_ENABLE_MPS_FALLBACK") == "1":
        raise RuntimeError("Disable PYTORCH_ENABLE_MPS_FALLBACK for an honest MPS check")
    device = torch.device(backend)
    torch.manual_seed(14)
    model = make_sequence_model(kind, input_units=3, hidden=8, output_coordinates=2)
    model = model.to(device)
    synthetic_inputs = torch.linspace(-1, 1, 42).reshape(2, 7, 3).to(device)
    synthetic_targets = torch.zeros(2, 7, 2, device=device)
    original_parameters = [parameter.detach().clone() for parameter in model.parameters()]
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    optimizer.zero_grad()
    outputs = model(synthetic_inputs)
    if outputs.shape != synthetic_targets.shape or not torch.isfinite(outputs).all():
        raise ValueError("Invalid forward output")
    loss = (outputs - synthetic_targets).square().mean()
    loss.backward()
    for parameter in model.parameters():
        if parameter.grad is None or not torch.isfinite(parameter.grad).all():
            raise ValueError("Missing or nonfinite parameter gradient")
    optimizer.step()
    changed = False
    for original, parameter in zip(original_parameters, model.parameters()):
        if parameter.device.type != backend or not torch.isfinite(parameter).all():
            raise ValueError("Parameters left requested backend or became nonfinite")
        changed = changed or not torch.equal(original, parameter.detach())
    if not changed:
        raise ValueError("Optimizer did not change any parameter")
    model.eval()
    with torch.no_grad():
        expected = model(synthetic_inputs)
    if not torch.isfinite(expected).all():
        raise ValueError("Nonfinite output after optimizer step")
    torch.save(model.state_dict(), checkpoint_path)
    restored_state = torch.load(checkpoint_path, weights_only=True, map_location=device)
    replica = make_sequence_model(kind, input_units=3, hidden=8, output_coordinates=2).to(device)
    replica.load_state_dict(restored_state)
    replica.eval()
    with torch.no_grad():
        restored = replica(synthetic_inputs)
    torch.testing.assert_close(restored, expected, rtol=1e-5, atol=1e-6)
    return {"status": "PASS", "loss_before_step": float(loss.detach().cpu()),
            "parameter_update_checked": True, "weights_only_restore_checked": True,
            "output_device": str(restored.device)}


def run(output="data/processed/mission_014/hardware.json"):
    availability = backend_availability()
    report = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(), "torch_version": str(torch.__version__),
        "platform": platform.platform(), "machine": platform.machine(),
        "mps_built": torch.backends.mps.is_built(), "cuda_build_version": torch.version.cuda,
        "mps_cpu_fallback_environment": os.environ.get("PYTORCH_ENABLE_MPS_FALLBACK"),
        "fixture": "Dimensionless synthetic inputs (2 sequences, 7 bins, 3 features), zero targets",
        "scope": "Software forward/backward, optimizer update and same-backend weights-only restoration; no scientific benchmark, timing or neural validation",
        "backends": {},
    }
    failed = False
    with tempfile.TemporaryDirectory(prefix="cerebro-hardware-") as temporary:
        for backend, available in availability.items():
            checks = {}
            for kind in MODEL_KINDS:
                if not available:
                    checks[kind] = {"status": "NOT_TESTED", "reason": "Backend unavailable"}
                    continue
                checkpoint_path = Path(temporary) / (backend + "_" + kind + ".pt")
                try:
                    checks[kind] = check_model(kind, backend, checkpoint_path)
                except Exception as error:
                    checks[kind] = {"status": "FAIL", "error_type": type(error).__name__,
                                    "error": str(error)}
                    failed = True
            backend_status = "NOT_TESTED" if not available else "PASS"
            if any(check["status"] == "FAIL" for check in checks.values()):
                backend_status = "FAIL"
            report["backends"][backend] = {
                "available": available, "status": backend_status, "models": checks,
            }
    report["status"] = "FAIL" if failed else "PASS"
    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="data/processed/mission_014/hardware.json")
    arguments = parser.parse_args(argv)
    report = run(arguments.output)
    print(json.dumps({backend: result["status"] for backend, result in report["backends"].items()}))
    return 1 if report["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
