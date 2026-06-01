from pathlib import Path


MODEL_RUNTIME_ROOT = Path("src/ultimate_ai_agent/core/model_runtime")


def test_model_runtime_source_has_no_real_runtime_imports_or_network_calls():
    forbidden = [
        "import openai",
        "from openai import",
        "import anthropic",
        "import requests",
        "import httpx",
        "urllib",
        "socket",
        "subprocess",
        "tokenizer",
        "tiktoken",
        "sentencepiece",
        "billing",
        "base_url",
        ".post(",
        ".get(",
    ]
    source = "\n".join(path.read_text(encoding="utf-8") for path in MODEL_RUNTIME_ROOT.rglob("*.py"))

    for marker in forbidden:
        assert marker not in source
