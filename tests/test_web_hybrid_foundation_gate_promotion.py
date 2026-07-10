from pathlib import Path

from ultimate_ai_agent.core.gate.criteria import default_foundation_gate_criteria
from ultimate_ai_agent.core.gate.evaluators import FoundationGateEvaluator
from ultimate_ai_agent.core.gate.legacy_support import (
    WEB_HYBRID_EXACT_ADAPTER_FILES,
    _is_web_hybrid_promoted_static_fragment,
)


def test_web_hybrid_foundation_gate_exception_is_file_and_fragment_scoped() -> None:
    for adapter_file in WEB_HYBRID_EXACT_ADAPTER_FILES:
        assert _is_web_hybrid_promoted_static_fragment(
            adapter_file,
            "network_call_performed=True",
            "    network_call_performed=True,\n",
        )
        assert _is_web_hybrid_promoted_static_fragment(
            adapter_file,
            "socket.",
            _allowed_socket_source(adapter_file),
        )
        assert _is_web_hybrid_promoted_static_fragment(
            adapter_file,
            "runtime_allowed=True",
            "    provider_runtime_allowed=True,\n",
        )
        assert not _is_web_hybrid_promoted_static_fragment(
            adapter_file,
            "runtime_allowed=True",
            "    runtime_allowed=True\n",
        )
        assert not _is_web_hybrid_promoted_static_fragment(
            adapter_file,
            "production_authority_granted=True",
            "production_authority_granted=True\n",
        )
        assert not _is_web_hybrid_promoted_static_fragment(
            adapter_file,
            "browser_automation_enabled=True",
            "browser_automation_enabled=True\n",
        )

    assert not _is_web_hybrid_promoted_static_fragment(
        "src/ultimate_ai_agent/core/network/unsafe.py",
        "network_call_performed=True",
        "network_call_performed=True,\n",
    )


def _allowed_socket_source(adapter_file: str) -> str:
    if adapter_file.endswith("firecrawl_cloud.py"):
        return "def _cloud_json_request():\n    socket.create_connection()\n"
    if adapter_file.endswith("firecrawl_markdown.py"):
        return (
            "def _loopback_json_post():\n    socket.create_connection()\n"
            "def validate_resolved_public_target():\n"
            "    socket.getaddrinfo(type=socket.SOCK_STREAM)\n"
            "    socket.gaierror\n"
        )
    return "def _loopback_json_get():\n    socket.create_connection()\n"


def test_web_hybrid_socket_exception_rejects_unreviewed_call_site() -> None:
    adapter = "src/ultimate_ai_agent/core/web_access/firecrawl_cloud.py"
    assert not _is_web_hybrid_promoted_static_fragment(
        adapter,
        "socket.",
        "def unreviewed_transport():\n    socket.create_connection()\n",
    )
    assert not _is_web_hybrid_promoted_static_fragment(
        adapter,
        "socket.",
        "def _cloud_json_request():\n    socket.socket().listen()\n",
    )


def test_web_hybrid_endpoint_exception_rejects_endpoint_drift(tmp_path: Path) -> None:
    adapter = (
        tmp_path
        / "src/ultimate_ai_agent/core/web_access/firecrawl_cloud.py"
    )
    adapter.parent.mkdir(parents=True)
    adapter.write_text(
        'FIRECRAWL_CLOUD_BASE_URL = "https://api.firecrawl.dev"\n'
        'UNREVIEWED_ENDPOINT = "https://unreviewed.invalid"\n',
        encoding="utf-8",
    )
    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id == "forbidden_runtime_integrations_absent"
    )

    result = FoundationGateEvaluator(tmp_path).evaluate([criterion]).results[0]

    assert result.status == "failed"
    assert len(result.failures) == 1
    assert "unreviewed" not in result.failures[0]


def test_web_hybrid_runtime_exception_rejects_generic_runtime_marker(
    tmp_path: Path,
) -> None:
    adapter = (
        tmp_path
        / "src/ultimate_ai_agent/core/web_access/firecrawl_cloud.py"
    )
    adapter.parent.mkdir(parents=True)
    adapter.write_text("runtime_allowed=True\n", encoding="utf-8")
    criterion = next(
        item
        for item in default_foundation_gate_criteria()
        if item.criterion_id
        == "m98_scoped_recurring_low_risk_automation_static_safety"
    )

    result = FoundationGateEvaluator(tmp_path).evaluate([criterion]).results[0]

    assert result.status == "failed"
    assert any("runtime_allowed=True" in failure for failure in result.failures)
