#!/usr/bin/env python3
"""Verify the MSG-MX-001 desktop design, threat, and authority gate."""

from __future__ import annotations

import json
import os
import re
import stat
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import verify_msg_mx_000_baseline_authority_gate as baseline  # noqa: E402


ADR_PATH = ROOT / "docs/decisions/ADR-0062-messenger-matrix-client-and-data-boundaries.md"
RENDER_PATH = (
    ROOT
    / "docs/design/control_center_north_star/UAA_MESSENGER_MATRIX_RENDER_ACCEPTANCE.md"
)
RENDER_MANIFEST_PATH = (
    ROOT / "docs/design/control_center_north_star/render-review/renders.json"
)
THREAT_PATH = ROOT / "docs/security/UAA_MESSENGER_MATRIX_THREAT_MODEL.md"
MATRIX_PATH = ROOT / "docs/connectors/MESSENGER_MATRIX_DESIGN_AUTHORITY_MATRIX.md"
BOARD_PATH = ROOT / "docs/kanban/current_board.md"
TRUTH_PATH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
INDEX_PATH = ROOT / "docs/DOCUMENTATION_INDEX.md"
ARTIFACT_REFS = (
    "docs/decisions/ADR-0062-messenger-matrix-client-and-data-boundaries.md",
    "docs/design/control_center_north_star/UAA_MESSENGER_MATRIX_RENDER_ACCEPTANCE.md",
    "docs/security/UAA_MESSENGER_MATRIX_THREAT_MODEL.md",
    "docs/connectors/MESSENGER_MATRIX_DESIGN_AUTHORITY_MATRIX.md",
)

EXPECTED_RENDER_IDS = tuple(f"COMMS-MX-{index:02d}" for index in range(1, 16))
EXPECTED_RENDER_FILES = (
    "01-founder-hq.png",
    "02-personal-circle.png",
    "03-direct-message.png",
    "04-group-room.png",
    "05-threads.png",
    "06-search-attention.png",
    "07-room-information.png",
    "08-create-invite.png",
    "09-room-settings.png",
    "10-sessions-recovery.png",
    "11-uaa-intelligence.png",
    "12-failure-recovery.png",
    "13-dark-theme.png",
    "14-calling.png",
    "15-setup-sign-in.png",
)
EXPECTED_THREAT_REFS = (
    "authority-confusion",
    "discovery-ssrf",
    "sso-substitution",
    "credential-exposure",
    "duplicate-client",
    "malicious-event",
    "formatted-content",
    "receipt-typing-spoof",
    "message-replay",
    "unknown-delivery",
    "media-hostile",
    "cache-leak",
    "cross-room-context",
    "model-authority",
    "verification-downgrade",
    "backup-rollback",
    "identity-reset",
    "deletion-overclaim",
    "log-evidence-leak",
    "safe-disable-gap",
    "resource-exhaustion",
    "harness-escape",
)
EXPECTED_CAPABILITY_REFS = (
    "matrix.discovery.read",
    "matrix.auth.methods.read",
    "matrix.session.password.create",
    "matrix.session.sso.launch",
    "matrix.session.sso.callback.consume",
    "matrix.session.refresh",
    "matrix.session.logout",
    "matrix.session.revoke_all",
    "matrix.credential.store_rotate",
    "matrix.credential.delete",
    "matrix.sync.read",
    "matrix.timeline.paginate.read",
    "matrix.receipt.project.read",
    "matrix.typing.project.read",
    "matrix.cache.read",
    "matrix.cache.write",
    "matrix.cache.migrate",
    "matrix.cache.purge",
    "matrix.cache.key.create",
    "matrix.cache.key.rotate",
    "matrix.cache.key.delete",
    "matrix.receipt.write",
    "matrix.typing.write",
    "matrix.draft_outbox.persist",
    "matrix.message.send",
    "matrix.message.reconcile",
    "matrix.message.retry",
    "matrix.message.edit",
    "matrix.message.redact",
    "matrix.reaction.add",
    "matrix.reaction.remove",
    "matrix.notification.desktop",
    "matrix.media.upload",
    "matrix.media.download_quarantine",
    "matrix.media.materialize",
    "matrix.media.preview",
    "matrix.media.cleanup",
    "matrix.room_state.read",
    "matrix.search.local.read",
    "matrix.dm.create",
    "matrix.room.create",
    "matrix.room.join",
    "matrix.room.leave",
    "matrix.invite.send",
    "matrix.invite.accept",
    "matrix.invite.reject",
    "matrix.invite.withdraw",
    "matrix.room.power_role.write",
    "matrix.space.mapping.write",
    "matrix.settings.notification.write",
    "matrix.settings.history_visibility.write",
    "matrix.settings.pin.write",
    "matrix.settings.account_room_preference.write",
    "matrix.verification.request",
    "matrix.verification.cancel",
    "matrix.verification.confirm",
    "matrix.device.revoke",
    "matrix.backup.configure",
    "matrix.backup.rotate",
    "matrix.recovery.restore",
    "matrix.identity.reset",
    "matrix.local_backup.create",
    "matrix.local_backup.restore",
    "matrix.local_backup.delete",
    "matrix.local_backup.expiry_reconcile",
    "matrix.context.materialize",
    "matrix.call.preflight.read",
    "matrix.call.start",
    "matrix.call.join",
    "matrix.call.leave",
    "matrix.call.terminate_all",
)

READ_ONLY_CAPABILITY_REFS = {
    "matrix.discovery.read",
    "matrix.auth.methods.read",
    "matrix.sync.read",
    "matrix.timeline.paginate.read",
    "matrix.receipt.project.read",
    "matrix.typing.project.read",
    "matrix.cache.read",
    "matrix.message.reconcile",
    "matrix.room_state.read",
    "matrix.search.local.read",
    "matrix.call.preflight.read",
}


def _read(path: Path, failures: list[str]) -> str:
    try:
        if path.is_symlink():
            failures.append(f"unsafe design artifact: {path.name}")
            return ""
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        failures.append(f"missing design artifact {path.name}: {exc}")
        return ""


def _require(label: str, text: str, fragments: tuple[str, ...], failures: list[str]) -> None:
    normalized = " ".join(text.split()).casefold()
    for fragment in fragments:
        if " ".join(fragment.split()).casefold() not in normalized:
            failures.append(f"{label} missing required contract: {fragment}")


def _png_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as stream:
            header = stream.read(24)
    except OSError:
        return None
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", header[16:24])


def _verify_renders(text: str, failures: list[str]) -> None:
    rows = re.findall(
        r"^\| `(COMMS-MX-\d{2})` \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|$",
        text,
        re.MULTILINE,
    )
    if tuple(row[0] for row in rows) != EXPECTED_RENDER_IDS:
        failures.append("render acceptance must contain exactly COMMS-MX-01 through 15")
    for render_id, decision, normal, narrow, truth in rows:
        if not decision.strip().startswith("accepted"):
            failures.append(f"{render_id} lacks an explicit acceptance decision")
        if not all(value.strip() for value in (normal, narrow, truth)):
            failures.append(f"{render_id} has an empty desktop or truth contract")

    _require(
        "render acceptance",
        text,
        (
            "Normal review viewport: 1440 x 900",
            "Narrow desktop review viewport: 1180 x 800",
            "No mobile layout",
            "human composer and UAA prompt/proposal surface remain visually and semantically separate",
            "Preview`, `Planned`, or `Blocked",
            "fixture states, not runtime outcomes",
        ),
        failures,
    )

    try:
        manifest = json.loads(RENDER_MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"render review manifest is unreadable: {exc}")
        return
    records = [record for record in manifest.get("renders", []) if record.get("set") == "communications-v1"]
    if tuple(record.get("id") for record in records) != EXPECTED_RENDER_IDS:
        failures.append("render review manifest communications-v1 membership or order drifted")
        return
    expected_images = tuple(
        f"../renders/communications-v1/{name}" for name in EXPECTED_RENDER_FILES
    )
    if tuple(record.get("image") for record in records) != expected_images:
        failures.append("render review manifest image bindings drifted")
    for record in records:
        relative = record.get("image")
        if not isinstance(relative, str):
            continue
        candidate = Path(os.path.abspath(RENDER_MANIFEST_PATH.parent / relative))
        try:
            if not candidate.is_relative_to(ROOT):
                raise OSError("render path escapes repository root")
            cursor = ROOT
            for part in candidate.relative_to(ROOT).parts:
                cursor /= part
                if cursor.is_symlink():
                    raise OSError("render path contains a symlink")
            if not stat.S_ISREG(candidate.lstat().st_mode):
                raise OSError("render path is not a regular file")
            path = candidate.resolve(strict=True)
        except OSError:
            failures.append(f"unsafe or missing render image: {record.get('id')}")
            continue
        if not path.is_relative_to(ROOT):
            failures.append(f"unsafe or missing render image: {record.get('id')}")
            continue
        dimensions = _png_dimensions(path)
        if dimensions is None or dimensions[1] != 992 or dimensions[0] not in {1585, 1586}:
            failures.append(f"unexpected render image contract: {record.get('id')}")


def _verify_adr(text: str, failures: list[str]) -> None:
    _require(
        "ADR",
        text,
        (
            "no runtime authority or implementation",
            "original product, Python, TypeScript, CSS, fixture, and test code",
            "will not fork, embed, reskin, transpile, translate, or transplant Element",
            "matrix-js-sdk` is the selected future client library",
            "does not install it or accept a package version",
            "Python Core remains authoritative",
            "React cannot import the Matrix SDK",
            "one live Matrix client",
            "device-only, non-synchronizing macOS Keychain",
            "crypto-store encryption key and protected conversation-cache key are separate",
            "drafts and outbox state use a third dedicated key item",
            "local backups use a fourth dedicated backup-wrapping key item",
            "failure and `finally` paths always attempt that bounded cleanup",
            "safe-disable blocks new operations",
            "Approval refs are identifiers only",
        ),
        failures,
    )


def _verify_threats(text: str, failures: list[str]) -> None:
    refs = tuple(re.findall(r"^\| `threat-ref:matrix:([^`]+)` \|", text, re.MULTILINE))
    if refs != EXPECTED_THREAT_REFS:
        failures.append("threat register membership or order drifted")
    _require(
        "threat model",
        text,
        (
            "source plane is separate from the governance plane",
            "untrusted external input",
            "fresh exact pre-start evaluation",
            "remote terminal evidence alone marks delivery",
            "externally compensating, not local atomic transactions",
            "message content is untrusted quoted data",
            "default lock-screen projection contains no message body or participant identity",
            "no runtime lane",
        ),
        failures,
    )


def _verify_matrix(text: str, failures: list[str]) -> None:
    rows = re.findall(
        r"^\| `([^`]+)` \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|$",
        text,
        re.MULTILINE,
    )
    if tuple(row[0] for row in rows) != EXPECTED_CAPABILITY_REFS:
        failures.append("exact design capability matrix membership or order drifted")
    allowed_phase_postures = {
        "blocked",
        "blocked; raw-token import denied",
        "blocked; distinct from logout",
        "blocked; grants no write",
        "blocked; cannot reuse add profile",
        "blocked; no hidden context or Memory write",
        "unsupported, not configured, unknown readiness, blocked",
        "implemented; live configuration required",
        "concrete GET transport implemented; live executor configuration required",
        "authority declared; canonical executor uncomposed and blocked",
        "primitive tested; canonical dispatcher executor uncomposed and blocked",
        "authority declared; canonical GET executor uncomposed and blocked",
    }
    allowed_later_postures = {
        "deferred separate lane; blocked pending MatrixRTC/TURN decision",
        "unsupported later lane; blocked; no implementation or authority",
        "unsupported later lane; blocked",
    }
    for capability, owner, target, approval, behavior, posture in rows:
        if not all(value.strip() for value in (owner, target, approval, behavior)):
            failures.append(f"{capability} has an incomplete exact authority contract")
        approval_lower = approval.casefold()
        if capability in READ_ONLY_CAPABILITY_REFS:
            if "policy" not in approval_lower:
                failures.append(f"{capability} lacks an exact read-policy contract")
        else:
            negated_approval = any(
                marker in approval_lower
                for marker in (
                    "no approval",
                    "approval not required",
                    "without approval",
                    "no localapprovalauthority",
                    "localapprovalauthority not required",
                    "localapprovalauthority is not required",
                    "without localapprovalauthority",
                )
            )
            positive_approval = any(
                marker in approval_lower
                for marker in ("approval", "confirmation", "localapprovalauthority")
            )
            if negated_approval or not positive_approval:
                failures.append(f"{capability} lacks an exact approval/confirmation contract")
        phase_match = re.fullmatch(r"`MSG-MX-\d{3}`; (.+)", posture.strip())
        if phase_match:
            posture_valid = phase_match.group(1) in allowed_phase_postures
        else:
            posture_valid = posture.strip() in allowed_later_postures
        if not posture_valid:
            failures.append(f"{capability} does not use an exact fail-closed posture")
        behavior_lower = behavior.casefold()
        obligations = {
            "idempotency/replay": (
                "fingerprint",
                "generation",
                "transaction",
                "compare-and-swap",
                "compare-and-set",
                "one-use",
                "since-token",
                "monotonic",
                "fence",
                "validator",
                "binding",
                "digest",
            ),
            "rollback/irreversibility": (
                "rollback",
                "restore",
                "delete",
                "discard",
                "cancel",
                "irreversible",
                "revoke",
                "retain",
                "leave",
                "terminate",
                "compensat",
                "retract",
                "expiry",
                "expire",
                "unknown truth",
                "no retry",
            ),
            "safe-disable": ("disable", "lock", "stop", "kill", "force", "safe-disable"),
            "receipt/evidence": (" ref", "refs", "evidence", "counts", "outcome", "receipt", "progress"),
        }
        for obligation, markers in obligations.items():
            if not any(marker in behavior_lower for marker in markers):
                failures.append(f"{capability} missing {obligation} contract")
    _require(
        "authority matrix",
        text,
        (
            "Immediately before every future operation starts",
            "Approval refs identify records only",
            "Every mutation row requires fresh exact LocalApprovalAuthority validation",
            "fresh exact LocalApprovalAuthority validation bound to account, room/event range, purpose, model destination, expiry, and complete request fingerprint",
            "catalog `unsupported`",
            "configuration `not_configured`",
            "authority `blocked`",
            "derived readiness `unknown`",
            "Inspectable never means callable",
            "Any Matrix operation absent from this table is unsupported and blocked",
        ),
        failures,
    )


def verify() -> list[str]:
    failures: list[str] = []
    documents = {
        "ADR": _read(ADR_PATH, failures),
        "render acceptance": _read(RENDER_PATH, failures),
        "threat model": _read(THREAT_PATH, failures),
        "authority matrix": _read(MATRIX_PATH, failures),
        "board": _read(BOARD_PATH, failures),
        "product truth": _read(TRUTH_PATH, failures),
        "documentation index": _read(INDEX_PATH, failures),
    }
    if documents["render acceptance"]:
        _verify_renders(documents["render acceptance"], failures)
    if documents["ADR"]:
        _verify_adr(documents["ADR"], failures)
    if documents["threat model"]:
        _verify_threats(documents["threat model"], failures)
    if documents["authority matrix"]:
        _verify_matrix(documents["authority matrix"], failures)

    failures.extend(
        f"baseline authority gate: {failure}" for failure in baseline.verify()
    )
    phase_match = re.search(
        r"^Current phase: `MSG-MX-(\d{3})`$",
        documents["board"],
        flags=re.MULTILINE,
    )
    if phase_match is None or int(phase_match.group(1)) < 1:
        failures.append("board must remain at or beyond the accepted MSG-MX-001 phase")
    evidence_match = re.search(
        r"^Current evidence ref: `(evidence-ref:msg-mx-\d{3}:[a-z0-9:-]+)`$",
        documents["board"],
        flags=re.MULTILINE,
    )
    if (
        phase_match is not None
        and (
            evidence_match is None
            or not evidence_match.group(1).startswith(
                f"evidence-ref:msg-mx-{phase_match.group(1)}:"
            )
        )
    ):
        failures.append("current board evidence ref is not bound to its current phase")
    _require(
        "board",
        documents["board"],
        (
            "The accepted design gate is recorded",
            "docs/decisions/ADR-0062-messenger-matrix-client-and-data-boundaries.md",
            "docs/security/UAA_MESSENGER_MATRIX_THREAT_MODEL.md",
        ),
        failures,
    )
    _require(
        "product truth",
        documents["product truth"],
        ("MSG-MX-001 accepts the desktop target-render contract",),
        failures,
    )
    for relative in ARTIFACT_REFS:
        if relative not in documents["documentation index"]:
            failures.append(f"documentation index missing MSG-MX-001 artifact: {relative}")

    for label in ("ADR", "render acceptance", "threat model", "authority matrix"):
        if documents[label]:
            baseline._scan_security(label, documents[label], failures)
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("MSG-MX-001 design gate verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
