from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from scripts import verify_msg_mx_001_design_gate as gate


ROOT = Path(__file__).resolve().parents[1]


def _tamper(
    source: Path,
    destination: Path,
    transform: Callable[[str], str],
) -> Path:
    destination.write_text(transform(source.read_text(encoding="utf-8")), encoding="utf-8")
    return destination


def test_msg_mx_001_design_gate_passes() -> None:
    assert gate.verify() == []


def test_verifier_cli_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_msg_mx_001_design_gate.py")],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "verification passed" in result.stdout


def test_render_membership_is_exact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = _tamper(
        gate.RENDER_PATH,
        tmp_path / "render.md",
        lambda text: text.replace("`COMMS-MX-07`", "`COMMS-MX-99`", 1),
    )
    monkeypatch.setattr(gate, "RENDER_PATH", path)
    assert any("exactly COMMS-MX-01 through 15" in item for item in gate.verify())


def test_narrow_desktop_contract_is_required(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _tamper(
        gate.RENDER_PATH,
        tmp_path / "render.md",
        lambda text: text.replace("Narrow desktop review viewport: 1180 x 800", "Narrow contract omitted", 1),
    )
    monkeypatch.setattr(gate, "RENDER_PATH", path)
    assert any("Narrow desktop review viewport" in item for item in gate.verify())


def test_threat_register_change_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _tamper(
        gate.THREAT_PATH,
        tmp_path / "threat.md",
        lambda text: text.replace("threat-ref:matrix:unknown-delivery", "threat-ref:matrix:removed", 1),
    )
    monkeypatch.setattr(gate, "THREAT_PATH", path)
    assert "threat register membership or order drifted" in gate.verify()


def test_capability_removal_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _tamper(
        gate.MATRIX_PATH,
        tmp_path / "matrix.md",
        lambda text: text.replace("matrix.message.send", "matrix.message.removed", 1),
    )
    monkeypatch.setattr(gate, "MATRIX_PATH", path)
    assert "exact design capability matrix membership or order drifted" in gate.verify()


def test_capability_authority_promotion_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _tamper(
        gate.MATRIX_PATH,
        tmp_path / "matrix.md",
        lambda text: text.replace(
            "`MSG-MX-005`; unsupported, not configured, unknown readiness, blocked",
            "implemented and ready",
            1,
        ),
    )
    monkeypatch.setattr(gate, "MATRIX_PATH", path)
    assert any("does not use an exact fail-closed posture" in item for item in gate.verify())


def test_mutation_approval_downgrade_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _tamper(
        gate.MATRIX_PATH,
        tmp_path / "matrix.md",
        lambda text: text.replace(
            "human gesture captures intent plus fresh exact LocalApprovalAuthority validation bound to target/request; exact `S`, or separately approved proposal under exact `M`",
            "read policy; exact `S`",
            1,
        ),
    )
    monkeypatch.setattr(gate, "MATRIX_PATH", path)
    assert any("matrix.message.send lacks an exact approval/confirmation contract" in item for item in gate.verify())


def test_negated_mutation_approval_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _tamper(
        gate.MATRIX_PATH,
        tmp_path / "matrix.md",
        lambda text: text.replace(
            "human gesture captures intent plus fresh exact LocalApprovalAuthority validation bound to target/request; exact `S`, or separately approved proposal under exact `M`",
            "no approval required; exact `S`",
            1,
        ),
    )
    monkeypatch.setattr(gate, "MATRIX_PATH", path)
    assert any("matrix.message.send lacks an exact approval/confirmation contract" in item for item in gate.verify())


def test_unblocked_substring_cannot_pass_fail_closed_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _tamper(
        gate.MATRIX_PATH,
        tmp_path / "matrix.md",
        lambda text: text.replace(
            "`MSG-MX-005`; blocked",
            "unblocked and callable",
            1,
        ),
    )
    monkeypatch.setattr(gate, "MATRIX_PATH", path)
    assert any("exact fail-closed posture" in item for item in gate.verify())


def test_row_semantic_obligation_removal_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _tamper(
        gate.MATRIX_PATH,
        tmp_path / "matrix.md",
        lambda text: text.replace(
            "disable discovery; capability/version evidence only",
            "capability/version evidence only",
            1,
        ),
    )
    monkeypatch.setattr(gate, "MATRIX_PATH", path)
    assert any("missing safe-disable contract" in item for item in gate.verify())


def test_render_image_symlink_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_image = (
        gate.RENDER_MANIFEST_PATH.parent
        / "../renders/communications-v1/01-founder-hq.png"
    ).resolve()
    root = tmp_path / "repo"
    manifest_path = (
        root / "docs/design/control_center_north_star/render-review/renders.json"
    )
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        gate.RENDER_MANIFEST_PATH.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    image_path = (
        root
        / "docs/design/control_center_north_star/renders/communications-v1/01-founder-hq.png"
    )
    image_path.parent.mkdir(parents=True)
    image_path.symlink_to(original_image)

    monkeypatch.setattr(gate, "ROOT", root)
    monkeypatch.setattr(gate, "RENDER_MANIFEST_PATH", manifest_path)
    failures: list[str] = []
    gate._verify_renders(gate.RENDER_PATH.read_text(encoding="utf-8"), failures)
    assert "unsafe or missing render image: COMMS-MX-01" in failures


@pytest.mark.parametrize(
    "unsafe",
    (
        "password=unsafe-value",
        "message_body: private material",
        "Authorization: unsafe-material",
        "Bearer unsafe-token-value",
        "raw_log=private-output",
        "../private-source",
    ),
)
def test_unsafe_material_is_rejected(
    unsafe: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _tamper(
        gate.THREAT_PATH,
        tmp_path / "threat.md",
        lambda text: text + f"\n{unsafe}\n",
    )
    monkeypatch.setattr(gate, "THREAT_PATH", path)
    failures = gate.verify()
    assert any(
        "credential" in item
        or "bearer" in item
        or "raw-content" in item
        or "local path" in item
        for item in failures
    )


def test_board_evidence_must_be_phase_bound(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _tamper(
        gate.BOARD_PATH,
        tmp_path / "board.md",
        lambda text: text.replace(
            "evidence-ref:msg-mx-001:design-gate",
            "evidence-ref:msg-mx-000:baseline-authority-map",
            1,
        ),
    )
    monkeypatch.setattr(gate, "BOARD_PATH", path)
    assert any("Current evidence ref" in item for item in gate.verify())
