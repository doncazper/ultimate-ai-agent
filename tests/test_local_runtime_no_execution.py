from pathlib import Path

from ultimate_ai_agent.api.app import app

ROOT = Path(__file__).resolve().parents[1]
MODEL_RUNTIME_ROOT = ROOT / "src" / "ultimate_ai_agent" / "core" / "model_runtime"


def test_m22_model_runtime_contract_sources_do_not_import_runtime_packages_or_call_networks():
    forbidden_fragments = [
        "import ollama",
        "from ollama import",
        "import llama_cpp",
        "from llama_cpp import",
        "import mlx",
        "from mlx import",
        "import vllm",
        "from vllm import",
        "import lmstudio",
        "import requests",
        "import httpx",
        "subprocess",
        "requests.get(",
        "requests.post(",
        "requests.request(",
        "httpx.get(",
        "httpx.post(",
        "httpx.request(",
        "urllib.request.urlopen(",
        "create_completion",
        "chat.completions.create(",
        "ollama.generate(",
        "ollama.pull(",
        "/api/generate",
        "/v1/chat/completions",
    ]
    allowed_files = {
        "manual_loopback_transport.py",
        "local_adapter.py",
        "smoke_policy.py",
        "simulator.py",
        "transports.py",
    }

    failures: list[str] = []
    for path in MODEL_RUNTIME_ROOT.rglob("*.py"):
        if path.name in allowed_files:
            continue
        text = path.read_text(encoding="utf-8").lower()
        for fragment in forbidden_fragments:
            if fragment in text:
                failures.append(f"{path.relative_to(ROOT)} contains {fragment}")

    assert failures == []


def test_m22_adds_no_backend_runtime_activation_routes():
    paths = set(app.openapi()["paths"])

    forbidden_routes = {
        "/runtime/activate",
        "/runtime/probe",
        "/runtime/local/activate",
        "/runtime/local/probe",
        "/runtime/model-call",
        "/model-runtime/activate",
        "/model-runtime/probe",
        "/model-runtime/call",
        "/model-runtime/local/activate",
        "/model-runtime/local/probe",
        "/model-runtime/local/call",
        "/model-runtime/local/generate",
        "/local-model/call",
        "/local-model/activate",
    }
    assert paths.isdisjoint(forbidden_routes)
