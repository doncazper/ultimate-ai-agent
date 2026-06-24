from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_control_center_operator_shell_gap_map_is_current_and_safe() -> None:
    doc_path = ROOT / "docs/control_center/OPERATOR_SHELL_GAP_MAP.md"
    text = doc_path.read_text(encoding="utf-8")
    compact = " ".join(text.lower().split())

    assert "status: active uaa-p0-007 operator-shell gap map" in compact
    assert "api boundary: current fastapi manifest has 152 openapi paths" in compact
    assert (
        "| surface | current frontend component/page | current backend route(s) | "
        "missing backend route(s) | authority boundary | side-effect class | "
        "approval requirement | evidence/audit output | readiness status | "
        "production-readiness blocker |"
    ) in compact

    for surface in [
        "chat local operator",
        "setup assistant",
        "plans",
        "models",
        "approvals",
        "files",
        "runtime",
        "evidence",
        "settings",
    ]:
        assert f"| {surface} |" in compact

    for route in [
        "`get /v1/models`",
        "`post /v1/chat/completions`",
        "`post /task-decomposition/classify`",
        "`post /task-decomposition/decompose`",
        "`post /files/tree/preview`",
        "`post /files/read/preview`",
        "`get /observability/session-events`",
        "`post /observability/client-errors`",
        "`get /control-center/setup-assistant/summary`",
        "`get /control-center/today/summary`",
        "`get /control-center/actions/inbox`",
        "`post /control-center/actions/{action_id}/local-task/commit`",
        "`get /control-center/morning-briefing/summary`",
        "`get /control-center/storage/status`",
        "`get /control-center/routes`",
    ]:
        assert route in compact

    for rule in [
        "no hidden authority",
        "no fake completion",
        "no raw json as primary ui for operator-critical flows",
    ]:
        assert rule in compact

    for forbidden in [
        "production ready for external users",
        "public distribution is available",
        "control center executes actions",
        "plugin runtime import is enabled",
    ]:
        assert forbidden not in compact
