#!/usr/bin/env python3
"""Verify the immutable MSG-MX-000 planning and authority baseline."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "docs" / "connectors" / "MESSENGER_MATRIX_BASELINE_AUTHORITY_MAP.md"
BOARD_PATH = ROOT / "docs" / "kanban" / "current_board.md"
TRUTH_PATH = ROOT / "docs" / "roadmap" / "PRODUCT_RELEASE_TRUTH_PACKET.md"
INDEX_PATH = ROOT / "docs" / "DOCUMENTATION_INDEX.md"

BASELINE_SHA = "d1066c0cdc90a3d882114eab145e235cb8d1ae38"
AUTHORITY_MAP_SHA256 = (
    "1ab43406065a7c0d35904d89e0c6ca11b69b1ebc02fdf2183c4358e3470d083f"
)
LANE_LEDGER_SHA256 = "609aa80cfb86c5f05551aefa8e171fe0d0c582609e732699c7c7f3ce764c708a"
TRUTH_ROW_SHA256 = "eb4bc4f91f6093c079b48379c37860de3529a4add5362449b6659c36dcc4ce77"
INDEX_ROW_SHA256 = "053009f39a2fd2958d446eff9312d3da5a4031107dbd226def3b14ac7d6622f4"
BOARD_STATIC_SHA256 = "dd64259af2d5ee3a88b0607ffc443d12033e9a7c2f9b7558dace2c1df67300e5"
MAP_REF = "docs/connectors/MESSENGER_MATRIX_BASELINE_AUTHORITY_MAP.md"
VERIFIER_REF = "scripts/verify_msg_mx_000_baseline_authority_gate.py"
TEST_REF = "tests/test_msg_mx_000_baseline_authority_gate.py"
EXPECTED_MILESTONES = tuple(f"MSG-MX-{index:03d}" for index in range(13))
ACCEPTED_CURRENT_SUCCESS = {
    "MSG-MX-000": (
        "planning_audit_accepted_on_merge",
        "evidence-ref:msg-mx-000:baseline-authority-map",
    ),
    "MSG-MX-001": (
        "design_gate_accepted_on_merge",
        "evidence-ref:msg-mx-001:design-gate",
    ),
    "MSG-MX-002": (
        "fixture_desktop_shell_implemented_pending_merge_gate",
        "evidence-ref:msg-mx-002:desktop-fixture-shell",
    ),
    "MSG-MX-003": (
        "backend_contracts_api_cli_implemented_pending_merge_gate",
        "evidence-ref:msg-mx-003:communications-contracts",
    ),
    "MSG-MX-004": (
        "exact_local_harness_lanes_live_verified_pending_merge_evidence",
        "evidence-ref:msg-mx-004:local-synapse-harness",
    ),
    "MSG-MX-005": (
        "partial_discovery_auth_read_lanes_implemented_pending_merge_gate",
        "evidence-ref:msg-mx-005:partial-discovery-session",
    ),
    "MSG-MX-006": (
        "readonly_sync_two_get_transports_cache_primitives_ten_executors_uncomposed",
        "evidence-ref:msg-mx-006:readonly-sync-cache",
    ),
    "MSG-MX-007": (
        "crypto_exact_authority_accepted_persistent_adapter_required",
        "evidence-ref:msg-mx-007:crypto-authority-contracts",
    ),
    "MSG-MX-008": (
        "manual_messaging_exact_lanes_implemented_configuration_required",
        "evidence-ref:msg-mx-008:manual-messaging-loopback",
    ),
}
SAFE_BLOCKED_CURRENT_STATUS = {
    "blocked_authority_not_accepted",
    "blocked_configuration_required",
    "blocked_external_facility_required",
    "blocked_unsupported_platform_facility",
}

MILESTONE_MARKERS = (
    "<!-- MSG-MX-MILESTONE-LEDGER:START -->",
    "<!-- MSG-MX-MILESTONE-LEDGER:END -->",
)
LANE_MARKERS = (
    "<!-- MSG-MX-LANE-LEDGER:START -->",
    "<!-- MSG-MX-LANE-LEDGER:END -->",
)
SECTION_MARKERS = (
    "<!-- MSG-MX-SECTIONS:START -->",
    "<!-- MSG-MX-SECTIONS:END -->",
)
BOARD_MARKERS = (
    "<!-- MSG-MX-CURRENT-OVERLAY:START -->",
    "<!-- MSG-MX-CURRENT-OVERLAY:END -->",
)

EXPECTED_MILESTONE_ROWS = (
    (
        "MSG-MX-000",
        "declared",
        "planning_audit_accepted_on_merge",
        "implemented_planning_audit",
        "not_applicable_audit_metadata",
        "not_applicable_audit_metadata",
        "authority map, board binding, verifier, focused tests",
    ),
    (
        "MSG-MX-001",
        "planned",
        "planned_no_runtime_authority",
        "missing",
        "not_applicable_audit_metadata",
        "not_applicable_audit_metadata",
        "accepted clean-room ADR, render review, threat model, authority matrix",
    ),
    (
        "MSG-MX-002",
        "planned",
        "planned_no_runtime_authority",
        "missing",
        "not_applicable_audit_metadata",
        "not_applicable_audit_metadata",
        "fixture-only desktop shell, all commands Preview/Planned/Blocked, frontend proof",
    ),
    (
        "MSG-MX-003",
        "planned",
        "planned_no_runtime_authority",
        "missing",
        "not_applicable_audit_metadata",
        "not_applicable_audit_metadata",
        "Python contracts, read-only API/CLI inspection, disabled adapter, parity proof",
    ),
    *tuple(
        (
            f"MSG-MX-{index:03d}",
            "planned",
            "blocked_pending_separate_exact_authority",
            "unsupported_missing",
            "blocked",
            "unknown",
            evidence,
        )
        for index, evidence in (
            (
                4,
                "accepted loopback/container/harness lanes and hostile lifecycle proof",
            ),
            (
                5,
                "accepted discovery/session/auth/credential/SSO/callback lanes and revocation proof",
            ),
            (6, "accepted read/sync/cache/key lanes and cross-scope isolation proof"),
            (
                7,
                "accepted crypto/device/backup/recovery/reset lanes and loss/recovery proof",
            ),
            (
                8,
                "accepted exact human-commanded messaging/outbox/notification lanes and delivery proof",
            ),
            (9, "accepted room/admin/media/search lanes and quarantine/cleanup proof"),
            (
                10,
                "accepted context/provider/proposal/attachment lane families and isolation proof",
            ),
        )
    ),
    (
        "MSG-MX-011",
        "planned",
        "planned_no_new_lane_hardening",
        "missing",
        "not_applicable_audit_metadata",
        "not_applicable_audit_metadata",
        "hardening evidence under fresh exact authority for every exercised call",
    ),
    (
        "MSG-MX-012",
        "planned",
        "planned_no_new_lane_acceptance",
        "missing",
        "not_applicable_audit_metadata",
        "not_applicable_audit_metadata",
        "integrated acceptance evidence for exact previously accepted lanes only",
    ),
)

EXPECTED_LANE_REFS = {
    "MSG-MX-004": (
        "harness-inspect",
        "harness-start",
        "harness-smoke",
        "harness-stop",
        "harness-reset-cleanup",
    ),
    "MSG-MX-005": (
        "discovery",
        "auth-capability-discovery",
        "session-authenticate-create",
        "session-refresh",
        "session-logout-revoke",
        "credential-keychain-lifecycle",
        "sso-browser-launch",
        "sso-callback-consume",
    ),
    "MSG-MX-006": (
        "sync-read",
        "timeline-pagination",
        "room-state-read",
        "encrypted-cache-read",
        "encrypted-cache-write",
        "encrypted-cache-purge",
        "cache-key-lifecycle",
    ),
    "MSG-MX-007": (
        "crypto-store-init",
        "device-verification",
        "cross-signing",
        "secure-backup-write",
        "restore-recovery",
        "identity-reset",
    ),
    "MSG-MX-008": (
        "draft-persist",
        "manual-send-reply-thread",
        "manual-send-retry",
        "reaction-write",
        "edit-write",
        "redaction",
        "typing-indicator",
        "read-receipt-write",
        "outbox-persist",
        "outbox-cleanup",
        "desktop-notification",
    ),
    "MSG-MX-009": (
        "dm-create",
        "room-create",
        "invite-send",
        "room-join",
        "room-leave",
        "role-power-admin",
        "space-mutate",
        "notification-settings",
        "history-visibility",
        "pin-favorite",
        "encrypted-search",
        "media-upload",
        "media-download",
        "media-materialize",
        "media-quarantine",
        "media-preview",
        "media-cleanup",
    ),
    "MSG-MX-010": (
        "context-preview",
        "content-materialize",
        "provider-invoke",
        "proposal-persist",
        "attachment-materialize",
        "attachment-scan-analyze",
        "attachment-cleanup",
    ),
}
EXPECTED_EVIDENCE_PATHS = (
    (
        "evidence-ref:msg-mx-000:authority-taxonomy",
        (
            "src/ultimate_ai_agent/core/authority/contracts.py",
            "src/ultimate_ai_agent/core/capabilities/models.py",
        ),
    ),
    (
        "evidence-ref:msg-mx-000:route-taxonomy",
        ("src/ultimate_ai_agent/api/contracts.py",),
    ),
    (
        "evidence-ref:msg-mx-000:matrix-runtime-absence",
        (
            "docs/design/UAA_MESSENGER_MATRIX_IMPLEMENTATION_PLAN.md",
            "docs/design/control_center_north_star/UAA_COMMUNICATIONS_MATRIX_NORTH_STAR.md",
        ),
    ),
    (
        "evidence-ref:msg-mx-000:dependency-absence",
        (
            "pyproject.toml",
            "uv.lock",
            "apps/control-center/package.json",
            "apps/control-center/package-lock.json",
        ),
    ),
    (
        "evidence-ref:msg-mx-000:messages-connector-denials",
        (
            "src/ultimate_ai_agent/core/connectors/messages_connector_contract_review.py",
            "src/ultimate_ai_agent/core/connectors/connector_read_only_runtime.py",
            "tests/test_m124_messages_connector_contract_review.py",
        ),
    ),
    (
        "evidence-ref:msg-mx-000:current-messages-lane",
        ("src/ultimate_ai_agent/core/authority/lane_registry.py",),
    ),
)

STATUS_FIELDS = (
    "Declaration status",
    "Program status",
    "Implementation status",
    "Availability snapshot posture",
    "Catalog status",
    "Compatibility status",
    "Configuration status",
    "Health status",
    "Authority posture",
    "Resource/budget status",
    "Cost posture",
    "Safe-disable status",
    "Freshness status",
    "Derived readiness",
)
DETAIL_FIELDS = (
    "Planned exact capability refs",
    "Current domain/capability mapping",
    "Taxonomy gap",
    "Adapter/provider/target scope",
    "Route/side-effect posture",
    "Policy/approval/lease gate",
    "Deadline/TTL posture",
    "Idempotency/replay posture",
    "Rollback posture",
    "Receipt/evidence/redaction",
    "Blocker refs",
    "Promotion evidence",
)
RUNTIME_STATUS = {
    "Availability snapshot posture": "baseline_fail_closed_projection_not_persisted",
    "Catalog status": "unsupported",
    "Compatibility status": "unknown",
    "Configuration status": "not_configured",
    "Health status": "unknown",
    "Authority posture": "blocked",
    "Resource/budget status": "unknown",
    "Cost posture": "unknown",
    "Safe-disable status": "unknown",
    "Freshness status": "unknown",
    "Derived readiness": "unknown",
}
NON_RUNTIME_STATUS = {
    "Catalog status": "not_applicable_audit_metadata",
    "Compatibility status": "not_applicable_audit_metadata",
    "Configuration status": "not_applicable_audit_metadata",
    "Health status": "not_applicable_audit_metadata",
    "Authority posture": "not_applicable_audit_metadata",
    "Resource/budget status": "not_applicable_audit_metadata",
    "Cost posture": "not_applicable_audit_metadata",
    "Safe-disable status": "not_applicable_audit_metadata",
    "Freshness status": "not_applicable_audit_metadata",
    "Derived readiness": "not_applicable_audit_metadata",
}
SHARED_GATE_FRAGMENTS = (
    "PolicyEngine and exact current policy decision",
    "exact LocalApprovalAuthority scope where required",
    "current exact AuthorityLease",
    "exact capability, adapter, provider, target, mission, and run",
    "TTL and deadline",
    "budgets as applicable",
    "kill switch and safe-disable",
    "request fingerprint, idempotency, replay, and prior-start posture",
    "Approval refs are identifiers only",
    "any repo-local harness script is test-only and cannot bypass policy, approval, lease, budget, readiness, kill-switch, safe-disable, idempotency, or receipt gates",
)

FORBIDDEN_AUTHORITY_PATTERNS = (
    re.compile(r"\bmatrix\s+is\s+(?:globally\s+)?authorized\b", re.IGNORECASE),
    re.compile(r"\bmatrix\s+execution\s+is\s+enabled\b", re.IGNORECASE),
    re.compile(
        r"\bmatrix\s+(?:is\s+)?(?:callable|connected|enabled)\s*[:=]\s*(?:true|yes)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bfull machine access[^\n]{0,60}(?:authorizes|enables|grants)[^\n]{0,30}matrix\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bapproval (?:identifier|ref)\s+(?:alone\s+)?(?:authorizes|grants)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bmessages-live-send-adapter[^\n]{0,60}(?:proves|implements|authorizes)[^\n]{0,30}matrix\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:lane|capability|adapter|operation)\s+is\s+ready\s+and\s+may\s+execute\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bmatrix\s+may\s+execute\b", re.IGNORECASE),
    re.compile(r"\bmatrix\s+can\s+execute\b", re.IGNORECASE),
    re.compile(r"\bmatrix\s+is\s+(?:ready|supported)\b", re.IGNORECASE),
    re.compile(r"\bmatrix\s+runtime\s+is\s+available\b", re.IGNORECASE),
    re.compile(r"\bmatrix\s+is\s+(?:public|production)[ -]ready\b", re.IGNORECASE),
    re.compile(r"\bmobile implementation (?:is|remains) in scope\b", re.IGNORECASE),
)
SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?:[\"']?\b(?:password|secret|token|api[ _-]?key|client[ _-]?secret|authorization|"
    r"private[ _-]?key|(?:access|refresh)[ _-]?token|credential|"
    r"recovery[ _-]?(?:key|material))\b[\"']?)\s*[:=]\s*[^\s|]+",
    re.IGNORECASE,
)
BEARER_MATERIAL_PATTERN = re.compile(r"\bbearer\s+[A-Za-z0-9._~+/-]{8,}", re.IGNORECASE)
HIGH_SIGNAL_SECRET_PATTERN = re.compile(
    r"(?:\bsk-(?:proj|live|test)-[A-Za-z0-9_-]{8,}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|\bAKIA[A-Z0-9]{12,}|"
    r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,})",
    re.IGNORECASE,
)
RAW_FIELD_PATTERN = re.compile(
    r"(?:[\"']?\b(?:message[ _-]?(?:body|content)|"
    r"raw[ _-]?(?:message|log|prompt|response)|"
    r"(?:prompt|response)[ _-]?content|provider[ _-]?payload|"
    r"(?:account|room|event|device)[ _-]?id|homeserver[ _-]?(?:url|address)|"
    r"hostname|username|serial)\b[\"']?)\s*[:=]",
    re.IGNORECASE,
)
ABSOLUTE_LOCAL_PATH_PATTERN = re.compile(
    r"(?:^|[\s(`'\"])(?:file:(?://)?/|/(?:Users|home|root|private|tmp|var|etc|"
    r"System|Library|Applications|opt|usr|Volumes|srv|mnt|proc|dev|run|bin|sbin|"
    r"workspace|build|runner|github)"
    r"(?:/|\b)|~/|\.\./|[A-Za-z]:\\Users\\|\\\\)",
    re.MULTILINE,
)


def _read(path: Path, failures: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        try:
            display_path = path.relative_to(ROOT)
        except ValueError:
            display_path = path.name
        failures.append(f"missing or unreadable {display_path}: {exc}")
        return ""


def _normalized(text: str) -> str:
    return " ".join(re.sub(r"-\s*\n\s*", "-", text).split())


def _require_fragments(
    label: str,
    text: str,
    fragments: tuple[str, ...],
    failures: list[str],
) -> None:
    normalized = _normalized(text)
    for fragment in fragments:
        if _normalized(fragment) not in normalized:
            failures.append(f"{label} missing required fragment: {fragment}")


def _render_state_before(text: str, position: int) -> tuple[bool, bool, bool]:
    active_fence: tuple[str, int] | None = None
    in_html_code = False
    in_comment = False
    for line in text[:position].splitlines():
        stripped = line.lstrip()
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue
        if active_fence is not None:
            fence_char, minimum = active_fence
            closing = re.match(rf"^{re.escape(fence_char)}{{{minimum},}}\s*$", stripped)
            if closing:
                active_fence = None
            continue
        if in_html_code:
            if re.search(r"</(?:pre|code)>", stripped, re.IGNORECASE):
                in_html_code = False
            continue
        if "<!--" in line:
            if "-->" not in line.split("<!--", 1)[1]:
                in_comment = True
            continue
        fence = re.match(r"^(`{3,}|~{3,})", stripped)
        if fence:
            token = fence.group(1)
            active_fence = (token[0], len(token))
            continue
        if re.search(r"<(?:pre|code)(?:\s|>)", stripped, re.IGNORECASE):
            if not re.search(r"</(?:pre|code)>", stripped, re.IGNORECASE):
                in_html_code = True
    return active_fence is not None, in_html_code, in_comment


def _contains_code_wrapper(text: str) -> bool:
    return bool(
        re.search(r"^\s*(?:`{3,}|~{3,})", text, re.MULTILINE)
        or re.search(r"</?(?:pre|code)(?:\s|>)", text, re.IGNORECASE)
    )


def _extract_marked(
    text: str,
    markers: tuple[str, str],
    label: str,
    failures: list[str],
    *,
    required_fenced: bool = False,
) -> str:
    start, end = markers
    if text.count(start) != 1 or text.count(end) != 1:
        failures.append(f"{label} markers must each appear exactly once")
        return ""
    start_index = text.index(start)
    end_index = text.index(end)
    if end_index <= start_index:
        failures.append(f"{label} marker ordering is invalid")
        return ""
    for marker, position in ((start, start_index), (end, end_index)):
        inside_fence, inside_html_code, inside_outer_comment = _render_state_before(
            text,
            position,
        )
        if inside_fence != required_fenced or inside_html_code or inside_outer_comment:
            failures.append(f"{label} marker is not rendered: {marker}")
            return ""
    return text[start_index + len(start) : end_index]


def _table_rows(body: str, prefix: str) -> list[tuple[str, ...]]:
    rows: list[tuple[str, ...]] = []
    for line in body.splitlines():
        if not line.startswith(prefix):
            continue
        rows.append(
            tuple(cell.strip().strip("`") for cell in line.strip("|").split("|"))
        )
    return rows


def _extract_ledger(text: str, failures: list[str]) -> list[list[str]]:
    body = _extract_marked(text, MILESTONE_MARKERS, "milestone ledger", failures)
    if _contains_code_wrapper(body) or "<!--" in body or "-->" in body:
        failures.append("milestone ledger rows must be rendered text")
    return [list(row) for row in _table_rows(body, "| MSG-MX-")]


def _extract_lane_ledger(text: str, failures: list[str]) -> list[list[str]]:
    body = _extract_marked(text, LANE_MARKERS, "planned lane ledger", failures)
    if _contains_code_wrapper(body) or "<!--" in body or "-->" in body:
        failures.append("planned lane ledger rows must be rendered text")
    return [list(row) for row in _table_rows(body, "| `planned-lane-ref:")]


def _extract_sections(
    text: str,
    failures: list[str] | None = None,
) -> list[tuple[str, str]]:
    local_failures = failures if failures is not None else []
    body = _extract_marked(text, SECTION_MARKERS, "milestone sections", local_failures)
    if not body:
        return []
    if _contains_code_wrapper(body) or "<!--" in body:
        local_failures.append(
            "milestone sections must be rendered text, not fences or comments"
        )
    matches = list(re.finditer(r"^### (MSG-MX-\d{3})\s*$", body, re.MULTILINE))
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections.append((match.group(1), body[match.end() : end]))
    return sections


def _status_values(
    milestone: str,
    body: str,
    failures: list[str],
) -> dict[str, str]:
    values: dict[str, str] = {}
    for field in STATUS_FIELDS:
        matches = re.findall(
            rf"^- {re.escape(field)}: `([^`]+)`\.$",
            body,
            re.MULTILINE,
        )
        if len(matches) != 1:
            failures.append(
                f"{milestone} must contain one exact, value-only {field} field"
            )
            continue
        values[field] = matches[0]
    for field in DETAIL_FIELDS:
        count = len(re.findall(rf"^- {re.escape(field)}:", body, re.MULTILINE))
        if count != 1:
            failures.append(f"{milestone} must contain exactly one {field} field")
    return values


def _scan_security(label: str, text: str, failures: list[str]) -> None:
    for pattern in FORBIDDEN_AUTHORITY_PATTERNS:
        if pattern.search(text):
            failures.append(
                f"{label} contains forbidden authority claim: {pattern.pattern}"
            )
    if SECRET_ASSIGNMENT_PATTERN.search(text):
        failures.append(f"{label} contains secret or credential material")
    if BEARER_MATERIAL_PATTERN.search(text):
        failures.append(f"{label} contains bearer credential material")
    if HIGH_SIGNAL_SECRET_PATTERN.search(text):
        failures.append(f"{label} contains high-signal secret material")
    if RAW_FIELD_PATTERN.search(text):
        failures.append(f"{label} contains an unsafe raw-content field")
    if ABSOLUTE_LOCAL_PATH_PATTERN.search(text):
        failures.append(f"{label} contains an absolute or traversing local path")


def _verify_evidence_paths(text: str, failures: list[str]) -> None:
    rows = re.findall(
        r"^\| `(evidence-ref:msg-mx-000:[^`]+)` \| ([^|]+) \|$",
        text,
        re.MULTILINE,
    )
    parsed = tuple(
        (evidence_ref, tuple(re.findall(r"`([^`]+)`", cell)))
        for evidence_ref, cell in rows
    )
    if parsed != EXPECTED_EVIDENCE_PATHS:
        failures.append(
            "baseline evidence table must contain exactly six rendered rows"
        )
        return
    root = ROOT.resolve()
    for _, refs in parsed:
        for ref in refs:
            path = ROOT / ref
            resolved = path.resolve()
            if (
                path.is_symlink()
                or not path.is_file()
                or not resolved.is_relative_to(root)
                or ".git" in resolved.parts
            ):
                failures.append(f"baseline evidence path missing or unsafe: {ref}")


def _verify_map(text: str, failures: list[str]) -> None:
    map_digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if map_digest != AUTHORITY_MAP_SHA256:
        failures.append("authority map differs from the immutable historical baseline")
    _require_fragments(
        "authority map",
        text,
        (
            BASELINE_SHA,
            "planning audit accepted on merge; no runtime authority",
            "Capability declaration",
            "Runtime availability",
            "Invocation authority",
            "Execution evidence",
            "lane-ref:messages-live-send-adapter",
            "is not Matrix implementation, readiness, or authority",
            "route is a generic authority matrix, not a Matrix-protocol route",
            "desktop-only baseline",
        ),
        failures,
    )
    _require_fragments(
        "shared future runtime gate", text, SHARED_GATE_FRAGMENTS, failures
    )

    rows = _extract_ledger(text, failures)
    actual_rows = tuple(tuple(row) for row in rows)
    if actual_rows != EXPECTED_MILESTONE_ROWS:
        failures.append("milestone ledger differs from the immutable baseline")
    for row in rows:
        if len(row) != 7:
            failures.append(f"{row[0]} milestone ledger row must have seven cells")

    lane_rows = _extract_lane_ledger(text, failures)
    lane_body = _extract_marked(text, LANE_MARKERS, "planned lane ledger", failures)
    lane_digest = hashlib.sha256(lane_body.encode("utf-8")).hexdigest()
    if lane_digest != LANE_LEDGER_SHA256:
        failures.append(
            "planned lane ledger full bindings differ from immutable baseline"
        )
    expected_lanes = [
        (f"planned-lane-ref:matrix:{suffix}", milestone)
        for milestone, suffixes in EXPECTED_LANE_REFS.items()
        for suffix in suffixes
    ]
    actual_lanes = [(row[0], row[1]) for row in lane_rows if len(row) >= 2]
    if actual_lanes != expected_lanes:
        failures.append("planned lane ledger membership, ownership, or order drifted")
    for row in lane_rows:
        if len(row) != 17:
            failures.append(f"{row[0]} planned lane row must have seventeen cells")
            continue
        if not all(row[index] for index in (2, 3, 4, 15, 16)):
            failures.append(f"{row[0]} planned lane binding or evidence is empty")
        if row[5:15] != [
            "unsupported",
            "unknown",
            "not_configured",
            "unknown",
            "blocked",
            "unknown",
            "unknown",
            "unknown",
            "unknown",
            "unknown",
        ]:
            failures.append(f"{row[0]} planned lane does not fail closed")
        if row[15] != "self-bound-profile":
            failures.append(f"{row[0]} planned lane gate profile is not self-bound")
        expected_evidence_prefix = f"evidence-ref:{row[1].lower()}:"
        if not row[16].startswith(expected_evidence_prefix):
            failures.append(f"{row[0]} evidence is not bound to {row[1]}")

    sections = _extract_sections(text, failures)
    section_ids = [milestone for milestone, _ in sections]
    all_section_ids = re.findall(r"^### (MSG-MX-\d{3})\s*$", text, re.MULTILINE)
    if section_ids != list(EXPECTED_MILESTONES) or all_section_ids != section_ids:
        failures.append(
            f"milestone sections must be rendered, ordered, and unique: {section_ids}"
        )
    ledger_by_id = {row[0]: row for row in rows if len(row) == 7}
    for milestone, body in sections:
        values = _status_values(milestone, body, failures)
        ledger = ledger_by_id.get(milestone)
        if ledger and values:
            comparisons = {
                "Declaration status": ledger[1],
                "Program status": ledger[2],
                "Implementation status": ledger[3],
                "Authority posture": ledger[4],
                "Derived readiness": ledger[5],
            }
            for field, expected in comparisons.items():
                if values.get(field) != expected:
                    failures.append(
                        f"{milestone} {field} disagrees with milestone ledger"
                    )
        index = int(milestone.rsplit("-", 1)[1])
        if 4 <= index <= 10:
            for field, expected in RUNTIME_STATUS.items():
                if values.get(field) != expected:
                    failures.append(
                        f"{milestone} {field} must preserve canonical fail-closed value {expected}"
                    )
        else:
            snapshot = values.get("Availability snapshot posture", "")
            if snapshot not in {
                "not_created_no_runtime_lane",
                "not_created_no_new_runtime_lane",
            }:
                failures.append(f"{milestone} must not claim a runtime snapshot")
            for field, expected in NON_RUNTIME_STATUS.items():
                if values.get(field) != expected:
                    failures.append(
                        f"{milestone} {field} must remain explicit audit metadata"
                    )

    _verify_evidence_paths(text, failures)
    _scan_security("authority map", text, failures)


def _rendered_table_row(text: str, token: str) -> list[str]:
    rows: list[str] = []
    active_fence: tuple[str, int] | None = None
    in_html_code = False
    in_comment = False
    for line in text.splitlines():
        stripped = line.lstrip()
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue
        if active_fence is not None:
            fence_char, minimum = active_fence
            if re.match(rf"^{re.escape(fence_char)}{{{minimum},}}\s*$", stripped):
                active_fence = None
            continue
        if in_html_code:
            if re.search(r"</(?:pre|code)>", stripped, re.IGNORECASE):
                in_html_code = False
            continue
        if "<!--" in line:
            if "-->" not in line.split("<!--", 1)[1]:
                in_comment = True
            continue
        fence = re.match(r"^(`{3,}|~{3,})", stripped)
        if fence:
            token_value = fence.group(1)
            active_fence = (token_value[0], len(token_value))
            continue
        if re.search(r"<(?:pre|code)(?:\s|>)", stripped, re.IGNORECASE):
            if not re.search(r"</(?:pre|code)>", stripped, re.IGNORECASE):
                in_html_code = True
            continue
        if line.startswith("|") and token.casefold() in line.casefold():
            rows.append(line)
    return rows


def _verify_bindings(
    board: str,
    truth: str,
    index: str,
    failures: list[str],
) -> None:
    overlay = _extract_marked(
        board,
        BOARD_MARKERS,
        "current board overlay",
        failures,
        required_fenced=True,
    )
    rendered_map_line = f"Baseline authority map: `{MAP_REF}`"
    if (
        overlay.count(MAP_REF) != 1
        or overlay.splitlines().count(rendered_map_line) != 1
    ):
        failures.append(
            "current board overlay must render the baseline map exactly once"
        )
    phase_matches = re.findall(
        r"^Current phase: `(MSG-MX-\d{3})`$", overlay, re.MULTILINE
    )
    if len(phase_matches) != 1 or phase_matches[0] not in EXPECTED_MILESTONES:
        failures.append("current board overlay must expose one valid current phase")
    status_matches = re.findall(
        r"^Current program status: `([a-z0-9_]+)`$",
        overlay,
        re.MULTILINE,
    )
    if len(status_matches) != 1:
        failures.append("current board overlay must expose one safe current status")
    evidence_matches = re.findall(
        r"^Current evidence ref: `(evidence-ref:msg-mx-[a-z0-9:-]+)`$",
        overlay,
        re.MULTILINE,
    )
    if len(evidence_matches) != 1:
        failures.append(
            "current board overlay must expose one safe current evidence ref"
        )
    mutable_prefixes = (
        "Current phase:",
        "Current program status:",
        "Current evidence ref:",
    )
    overlay_lines = overlay.splitlines()
    for prefix in mutable_prefixes:
        if sum(line.startswith(prefix) for line in overlay_lines) != 1:
            failures.append(
                f"current board overlay must contain one canonical {prefix} line"
            )
    validated_projection_lines: set[str] = set()
    if len(phase_matches) == 1:
        validated_projection_lines.add(f"Current phase: `{phase_matches[0]}`")
    if len(status_matches) == 1:
        validated_projection_lines.add(f"Current program status: `{status_matches[0]}`")
    if len(evidence_matches) == 1:
        validated_projection_lines.add(f"Current evidence ref: `{evidence_matches[0]}`")
    static_overlay = "\n".join(
        line for line in overlay_lines if line not in validated_projection_lines
    )
    static_digest = hashlib.sha256(static_overlay.encode("utf-8")).hexdigest()
    if static_digest != BOARD_STATIC_SHA256:
        failures.append("current board immutable historical baseline drifted")
    if len(phase_matches) == len(status_matches) == len(evidence_matches) == 1:
        phase = phase_matches[0]
        status = status_matches[0]
        evidence_ref = evidence_matches[0]
        if status in SAFE_BLOCKED_CURRENT_STATUS:
            pass
        elif ACCEPTED_CURRENT_SUCCESS.get(phase) != (status, evidence_ref):
            failures.append("current board success lacks accepted phase evidence")
        expected_evidence_prefix = f"evidence-ref:{phase.lower()}:"
        if not evidence_ref.startswith(expected_evidence_prefix):
            failures.append(
                "current board evidence ref is not bound to its current phase"
            )
    _require_fragments(
        "current board historical baseline",
        overlay,
        (
            BASELINE_SHA,
            "MSG-MX-000 is accepted for a planning audit",
            "MSG-MX-004 through MSG-MX-010 are",
            "blocked_pending_separate_exact_authority",
            "Approval refs grant nothing",
        ),
        failures,
    )

    truth_rows = _rendered_table_row(
        truth,
        "MSG-MX-000 accepts a planning-only Messenger Matrix baseline",
    )
    if len(truth_rows) != 1 or truth_rows[0].count(MAP_REF) != 1:
        failures.append(
            "product truth must contain one rendered historical MSG-MX-000 row"
        )
        truth_row = ""
    else:
        truth_row = truth_rows[0]
        truth_digest = hashlib.sha256(truth_row.encode("utf-8")).hexdigest()
        if truth_digest != TRUTH_ROW_SHA256:
            failures.append("product truth historical MSG-MX-000 row drifted")
    index_rows = _rendered_table_row(index, "Messenger Matrix MSG-MX-000 baseline")
    if len(index_rows) != 1:
        failures.append("documentation index must contain one rendered MSG-MX-000 row")
        index_row = ""
    else:
        index_row = index_rows[0]
        index_digest = hashlib.sha256(index_row.encode("utf-8")).hexdigest()
        if index_digest != INDEX_ROW_SHA256:
            failures.append("documentation index historical MSG-MX-000 row drifted")
    for ref in (MAP_REF, VERIFIER_REF, TEST_REF):
        if index_row.count(ref) != 1:
            failures.append(f"documentation index row must contain exactly one {ref}")

    _scan_security("current board overlay", overlay, failures)
    matrix_truth_rows = _rendered_table_row(truth, "matrix")
    if truth_row and truth_row not in matrix_truth_rows:
        failures.append(
            "product truth baseline row is not included in Matrix claim scan"
        )
    for row_number, row in enumerate(matrix_truth_rows, start=1):
        _scan_security(f"product truth Matrix row {row_number}", row, failures)
    _scan_security("documentation index row", index_row, failures)


def verify() -> list[str]:
    failures: list[str] = []
    authority_map = _read(MAP_PATH, failures)
    board = _read(BOARD_PATH, failures)
    truth = _read(TRUTH_PATH, failures)
    index = _read(INDEX_PATH, failures)
    if authority_map:
        _verify_map(authority_map, failures)
    if board and truth and index:
        _verify_bindings(board, truth, index, failures)
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("MSG-MX-000 baseline authority gate verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
