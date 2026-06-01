from pathlib import Path

from ultimate_ai_agent.api.app import app


ROOT = Path(__file__).resolve().parents[1]


def test_control_center_source_has_no_execution_or_frontend_integrations():
    control_center_root = ROOT / "src/ultimate_ai_agent/core/control_center"
    forbidden = [
        "import requests",
        "import httpx",
        "urllib",
        "socket",
        "subprocess",
        "import openai",
        "import anthropic",
        "tiktoken",
        "tokenizers",
        "node_modules",
        "package.json",
        "react",
        "next.js",
        "vite",
        "tailwind",
        "shadcn",
        "xcode",
        "simulator",
        "computer use",
    ]

    for path in control_center_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for fragment in forbidden:
            assert fragment not in text, f"{fragment} found in {path}"


def test_control_center_public_api_has_no_execute_enable_dispatch_or_connect_route():
    paths = {getattr(route, "path", "") for route in app.routes}
    forbidden_paths = {
        "/control-center/actions/execute",
        "/control-center/plugins/enable",
        "/control-center/runtime/execute",
        "/control-center/runtime/run",
        "/control-center/runtime/connect",
        "/control-center/remote-workers/dispatch",
        "/control-center/mobile/sensors",
        "/control-center/frontend",
    }
    assert forbidden_paths.isdisjoint(paths)
