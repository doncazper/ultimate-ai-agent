from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from scripts import verify_msg_mx_000_baseline_authority_gate as gate


def _tamper(
    source: Path,
    destination: Path,
    transform: Callable[[str], str],
) -> Path:
    destination.write_text(transform(source.read_text(encoding="utf-8")), encoding="utf-8")
    return destination


def _patch_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    path_attr: str,
    transform: Callable[[str], str],
) -> None:
    source = getattr(gate, path_attr)
    path = _tamper(source, tmp_path / f"{path_attr.lower()}.md", transform)
    monkeypatch.setattr(gate, path_attr, path)


@pytest.mark.parametrize(
    "claim",
    (
        "Matrix is authorized.",
        "Matrix execution is enabled.",
        "Matrix callable=true.",
        "Full Machine Access enables Matrix execution.",
        "An approval identifier grants authority.",
        "messages-live-send-adapter proves Matrix implementation.",
        "The capability is ready and may execute.",
        "Matrix may execute.",
        "Matrix can execute.",
        "Matrix is ready and supported.",
        "Matrix runtime is available.",
        "Matrix is production ready.",
        "Mobile implementation is in scope.",
    ),
)
def test_authority_drift_claims_fail_closed(
    claim: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "MAP_PATH",
        lambda text: text + f"\n{claim}\n",
    )
    assert any("forbidden authority claim" in failure for failure in gate.verify())


def test_truthful_not_production_ready_does_not_false_positive(
) -> None:
    failures: list[str] = []
    gate._scan_security("probe", "Matrix is not production ready.", failures)
    assert failures == []


def test_product_truth_authority_claim_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "TRUTH_PATH",
        lambda text: text.replace(
            "baseline and subordinate authority map.",
            "baseline and subordinate authority map. Matrix is authorized.",
            1,
        ),
    )
    assert any(
        "product truth Matrix row" in failure and "forbidden" in failure
        for failure in gate.verify()
    )


def test_additional_product_truth_matrix_claim_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "TRUTH_PATH",
        lambda text: text
        + "\n| A later Messenger Matrix row claims Matrix is authorized. | `safe-ref` |\n",
    )
    assert any(
        "product truth Matrix row" in failure and "forbidden" in failure
        for failure in gate.verify()
    )


def test_product_truth_runtime_ready_substitution_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "TRUTH_PATH",
        lambda text: text.replace(
            "keeps MSG-MX-004 through MSG-MX-010 blocked pending separately accepted exact lanes",
            "makes MSG-MX-004 through MSG-MX-010 runtime ready for execution",
            1,
        ),
    )
    assert "product truth historical MSG-MX-000 row drifted" in gate.verify()


def test_board_authority_claim_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "BOARD_PATH",
        lambda text: text.replace(
            gate.BOARD_MARKERS[1],
            "Matrix execution is enabled.\n" + gate.BOARD_MARKERS[1],
            1,
        ),
    )
    assert any("current board overlay contains forbidden" in failure for failure in gate.verify())


@pytest.mark.parametrize(
    "unsafe_value",
    (
        "password=hunter2",
        "Token: raw-token-value",
        "api_key=example-secret-material",
        '"token": "raw-secret"',
        '"api_key": "raw-secret"',
        "Client secret: example-secret-material",
        "Authorization: example-secret-material",
        "Bearer example-token-material",
        "openai_key_shape",
        "private_key_header_shape",
        "access_token=example-token",
        "recovery_material=example-value",
        "message_body: private text",
        "Message body: private conversation text",
        '"message_body": "private conversation"',
        "Message content: private conversation text",
        "raw_log=private-output",
        "raw_prompt=private-input",
        "prompt_content: private-input",
        "raw_response=private-output",
        "response_content: private-output",
        "provider_payload: private-value",
        "account_id=private-account",
        "Room ID: private-room",
        "Event-ID: private-event",
        "Homeserver URL: private-endpoint",
        "hostname=private-host",
        "serial=private-device",
    ),
)
def test_unsafe_content_fields_fail_closed(
    unsafe_value: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if unsafe_value == "openai_key_shape":
        unsafe_value = "".join(("sk", "-proj-", "example", "-material"))
    elif unsafe_value == "private_key_header_shape":
        unsafe_value = "".join(("-----BEGIN ", "PRIVATE", " KEY-----"))
    _patch_path(
        monkeypatch,
        tmp_path,
        "MAP_PATH",
        lambda text: text + f"\n{unsafe_value}\n",
    )
    failures = gate.verify()
    assert any(
        "secret or credential" in failure
        or "bearer credential" in failure
        or "high-signal secret" in failure
        or "unsafe raw-content" in failure
        for failure in failures
    )


@pytest.mark.parametrize(
    "unsafe_path",
    (
        "/etc/passwd",
        "/System/Library/private",
        "/Applications/private",
        "/opt/private",
        "/usr/bin/private",
        "/var/log/private",
        "/tmp/private",
        "/private/value",
        "/Users/private/value",
        "/home/private/value",
        "/root/.ssh/private",
        "/srv/private/value",
        "/mnt/private/value",
        "/proc/private/value",
        "/dev/private-value",
        "/run/private/value",
        "/Volumes/private/value",
        "/workspace/project/private",
        "/build/project/private",
        "/runner/_work/project/private",
        "/github/workspace/private",
        "file:///Users/private/value",
        "~/private",
        "../private",
        r"C:\Users\private\value",
        r"\\server\private",
    ),
)
def test_local_or_traversing_paths_fail_closed(
    unsafe_path: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "MAP_PATH",
        lambda text: text + f"\nLocal source: {unsafe_path}\n",
    )
    assert any("local path" in failure for failure in gate.verify())


def test_missing_evidence_path_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "MAP_PATH",
        lambda text: text.replace(
            "`src/ultimate_ai_agent/api/contracts.py` |",
            "`docs/missing-msg-mx-evidence.md` |",
            1,
        ),
    )
    assert any("baseline evidence table" in failure for failure in gate.verify())


def test_board_overlay_future_success_requires_phase_acceptance_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def advance(text: str) -> str:
        return (
            text
            .replace(
                "Current program status: `fixture_desktop_shell_implemented_pending_merge_gate`",
                "Current program status: `fixture_shell_ready`",
                1,
            )
            .replace(
                "Current evidence ref: `evidence-ref:msg-mx-002:desktop-fixture-shell`",
                "Current evidence ref: `evidence-ref:msg-mx-002:unaccepted`",
                1,
            )
        )

    _patch_path(monkeypatch, tmp_path, "BOARD_PATH", advance)
    assert "current board success lacks accepted phase evidence" in gate.verify()


def test_board_overlay_can_record_a_phase_bound_external_blocker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def block(text: str) -> str:
        return (
            text.replace("Current phase: `MSG-MX-002`", "Current phase: `MSG-MX-005`", 1)
            .replace(
                "Current program status: `fixture_desktop_shell_implemented_pending_merge_gate`",
                "Current program status: `blocked_external_facility_required`",
                1,
            )
            .replace(
                "Current evidence ref: `evidence-ref:msg-mx-002:desktop-fixture-shell`",
                "Current evidence ref: `evidence-ref:msg-mx-005:external-blocker`",
                1,
            )
        )

    _patch_path(monkeypatch, tmp_path, "BOARD_PATH", block)
    assert gate.verify() == []


def test_board_overlay_generic_ready_status_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def promote(text: str) -> str:
        return (
            text.replace("Current phase: `MSG-MX-002`", "Current phase: `MSG-MX-004`", 1)
            .replace(
                "Current program status: `fixture_desktop_shell_implemented_pending_merge_gate`",
                "Current program status: `ready`",
                1,
            )
            .replace(
                "Current evidence ref: `evidence-ref:msg-mx-002:desktop-fixture-shell`",
                "Current evidence ref: `evidence-ref:msg-mx-004:ready`",
                1,
            )
        )

    _patch_path(monkeypatch, tmp_path, "BOARD_PATH", promote)
    assert "current board success lacks accepted phase evidence" in gate.verify()


def test_board_overlay_cross_phase_evidence_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def advance(text: str) -> str:
        return (
            text.replace("Current phase: `MSG-MX-002`", "Current phase: `MSG-MX-003`", 1)
        )

    _patch_path(monkeypatch, tmp_path, "BOARD_PATH", advance)
    assert "current board evidence ref is not bound to its current phase" in gate.verify()


@pytest.mark.parametrize(
    "extra_line",
    (
        "Current program status: local Synapse harness implemented and ready for use",
        "Current phase: MSG-MX-008 manual messaging implemented",
    ),
)
def test_board_overlay_rejects_malformed_duplicate_projection_lines(
    extra_line: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "BOARD_PATH",
        lambda text: text.replace(
            gate.BOARD_MARKERS[1],
            f"{extra_line}\n{gate.BOARD_MARKERS[1]}",
            1,
        ),
    )
    assert any("one canonical Current" in failure for failure in gate.verify())


def test_reordered_markers_fail_closed_without_crashing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    start, end = gate.SECTION_MARKERS
    _patch_path(
        monkeypatch,
        tmp_path,
        "MAP_PATH",
        lambda text: text.replace(start, "TEMP", 1)
        .replace(end, start, 1)
        .replace("TEMP", end, 1),
    )
    assert "milestone sections marker ordering is invalid" in gate.verify()


def test_lane_ledger_wrapped_in_fence_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    start, end = gate.LANE_MARKERS
    _patch_path(
        monkeypatch,
        tmp_path,
        "MAP_PATH",
        lambda text: text.replace(start, f"```text\n{start}", 1).replace(
            end,
            f"{end}\n```",
            1,
        ),
    )
    assert any("planned lane ledger marker is not rendered" in failure for failure in gate.verify())


@pytest.mark.parametrize(
    ("path_attr", "token"),
    (
        ("TRUTH_PATH", "MSG-MX-000 accepts a planning-only Messenger Matrix baseline"),
        ("INDEX_PATH", "Messenger Matrix MSG-MX-000 baseline authority map"),
    ),
)
def test_supporting_table_row_wrapped_in_fence_fails_closed(
    path_attr: str,
    token: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fence(text: str) -> str:
        lines = text.splitlines()
        for index, line in enumerate(lines):
            if line.startswith("|") and token in line:
                lines[index : index + 1] = ["```text", line, "```"]
                return "\n".join(lines) + "\n"
        raise AssertionError("target row not found")

    _patch_path(monkeypatch, tmp_path, path_attr, fence)
    failures = gate.verify()
    assert any("must contain one rendered" in failure for failure in failures)


def test_duplicate_evidence_identity_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "MAP_PATH",
        lambda text: text.replace(
            "| `evidence-ref:msg-mx-000:route-taxonomy` |",
            "| `evidence-ref:msg-mx-000:authority-taxonomy` |",
            1,
        ),
    )
    assert any("baseline evidence table" in failure for failure in gate.verify())


def test_evidence_directory_substitution_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "MAP_PATH",
        lambda text: text.replace(
            "`src/ultimate_ai_agent/api/contracts.py` |",
            "`docs` |",
            1,
        ),
    )
    assert any("baseline evidence table" in failure for failure in gate.verify())


def test_harness_script_bypass_wording_is_required(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "MAP_PATH",
        lambda text: text.replace(
            "any repo-local harness script is test-only and cannot bypass policy, approval, "
            "lease, budget, readiness, kill-switch, safe-disable, idempotency, or receipt gates",
            "scripts-only bypass",
            1,
        ),
    )
    assert any("shared future runtime gate missing" in failure for failure in gate.verify())


@pytest.mark.parametrize(
    ("original", "replacement"),
    (
        (
            "separate exact evaluation for discovery, auth, session mutation, browser launch, callback, and credential mutation",
            "approval is optional and no lease is needed",
        ),
        (
            "revoke session, delete exact credential item, disable adapter, and prove terminal receipt",
            "no rollback or compensation is required",
        ),
        (
            "Calls, agent room participants, hosted infrastructure, public federation,",
            "Matrix is fully implemented and usable now.",
        ),
    ),
)
def test_complete_authority_map_obligations_are_immutable(
    original: str,
    replacement: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "MAP_PATH",
        lambda text: text.replace(original, replacement, 1),
    )
    assert "authority map differs from the immutable historical baseline" in gate.verify()


def test_board_immutable_historical_text_cannot_claim_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "BOARD_PATH",
        lambda text: text.replace(
            "The baseline adds no Matrix SDK",
            "The baseline includes a Matrix SDK",
            1,
        ),
    )
    assert "current board immutable historical baseline drifted" in gate.verify()


def test_future_completion_with_fabricated_evidence_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fabricate(text: str) -> str:
        return (
            text.replace("Current phase: `MSG-MX-002`", "Current phase: `MSG-MX-012`", 1)
            .replace(
                "Current program status: `fixture_desktop_shell_implemented_pending_merge_gate`",
                "Current program status: `messenger_acceptance_complete`",
                1,
            )
            .replace(
                "Current evidence ref: `evidence-ref:msg-mx-002:desktop-fixture-shell`",
                "Current evidence ref: `evidence-ref:msg-mx-012:does-not-exist`",
                1,
            )
        )

    _patch_path(monkeypatch, tmp_path, "BOARD_PATH", fabricate)
    assert "current board success lacks accepted phase evidence" in gate.verify()


def test_board_overlay_fence_state_cannot_be_changed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    start, end = gate.BOARD_MARKERS
    _patch_path(
        monkeypatch,
        tmp_path,
        "BOARD_PATH",
        lambda text: text.replace(start, f"```\n{start}", 1).replace(
            end,
            f"{end}\n```text",
            1,
        ),
    )
    assert any("current board overlay marker is not rendered" in failure for failure in gate.verify())


def test_lane_ledger_tilde_fence_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    start, end = gate.LANE_MARKERS
    _patch_path(
        monkeypatch,
        tmp_path,
        "MAP_PATH",
        lambda text: text.replace(start, f"~~~text\n{start}", 1).replace(
            end,
            f"{end}\n~~~",
            1,
        ),
    )
    assert any("planned lane ledger marker is not rendered" in failure for failure in gate.verify())


@pytest.mark.parametrize("wrapper", (("~~~text", "~~~"), ("<pre>", "</pre>")))
def test_product_truth_non_backtick_code_wrapper_fails_closed(
    wrapper: tuple[str, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token = "MSG-MX-000 accepts a planning-only Messenger Matrix baseline"

    def wrap(text: str) -> str:
        lines = text.splitlines()
        for index, line in enumerate(lines):
            if line.startswith("|") and token in line:
                lines[index : index + 1] = [wrapper[0], line, wrapper[1]]
                return "\n".join(lines) + "\n"
        raise AssertionError("target row not found")

    _patch_path(monkeypatch, tmp_path, "TRUTH_PATH", wrap)
    assert any("product truth must contain one rendered" in failure for failure in gate.verify())


def test_board_binding_hidden_in_comment_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rendered = f"Baseline authority map: `{gate.MAP_REF}`"
    _patch_path(
        monkeypatch,
        tmp_path,
        "BOARD_PATH",
        lambda text: text.replace(rendered, f"<!-- {rendered} -->", 1),
    )
    assert any("must render the baseline map" in failure for failure in gate.verify())


@pytest.mark.parametrize(
    ("path_attr", "ref", "expected"),
    (
        ("TRUTH_PATH", gate.MAP_REF, "product truth must contain"),
        ("INDEX_PATH", gate.TEST_REF, "documentation index row must contain"),
    ),
)
def test_rendered_supporting_binding_fails_closed(
    path_attr: str,
    ref: str,
    expected: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        path_attr,
        lambda text: text.replace(ref, "removed-ref", 1),
    )
    assert any(expected in failure for failure in gate.verify())


def test_documentation_index_runtime_ready_suffix_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_path(
        monkeypatch,
        tmp_path,
        "INDEX_PATH",
        lambda text: text.replace(
            "Messenger Matrix MSG-MX-000 baseline authority map |",
            "Messenger Matrix MSG-MX-000 baseline authority map - runtime ready |",
            1,
        ),
    )
    assert "documentation index historical MSG-MX-000 row drifted" in gate.verify()
