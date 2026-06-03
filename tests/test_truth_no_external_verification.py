from pathlib import Path

from ultimate_ai_agent.core.truth import build_truth_router_manifest


def test_truth_module_contains_no_external_lookup_or_model_call_fragments():
    truth_root = Path("src/ultimate_ai_agent/core/truth")
    source = "\n".join(path.read_text(encoding="utf-8") for path in truth_root.glob("*.py"))

    forbidden = [
        "requests.get(",
        "requests.post(",
        "httpx.get(",
        "httpx.post(",
        "urllib.request.urlopen(",
        "openai.",
        "anthropic.",
        "ollama.",
    ]

    assert not [fragment for fragment in forbidden if fragment in source]


def test_truth_manifest_disables_external_verification_by_default():
    manifest = build_truth_router_manifest("0.29.0")

    assert manifest.external_verification_enabled is False
    assert manifest.web_search_enabled is False
    assert manifest.model_verification_enabled is False
    assert manifest.automatic_claim_verification_enabled is False
