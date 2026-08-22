#!/usr/bin/env python3
"""Verify the bounded ECO-009 calendar metadata snapshot adapter."""

from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.connectors.read_only_platform import (  # noqa: E402
    CalendarMetadataSnapshotAdapter,
    CalendarMetadataSnapshotRow,
    ConnectorReadPlatform,
    ConnectorReadRequest,
    ConnectorReadStatus,
    build_eco009_connector_read_platform_posture,
)


REQUIRED_FILES = (
    "src/ultimate_ai_agent/core/connectors/read_only_platform.py",
    "tests/test_eco_009_read_only_connectors.py",
    "tests/test_eco_009_verifier.py",
    "scripts/inspect_eco_009_read_only_connectors.py",
    "docs/architecture/ECO_009_EXACT_READ_ONLY_CONNECTOR_PLATFORM.md",
    "docs/implementation/UAA_COHERENT_APP_ECOSYSTEM_IMPLEMENTATION_PLAN.md",
    "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
    "apps/control-center/src/api/types.ts",
    "apps/control-center/src/components/ConnectorReadPlatformCard.tsx",
    "apps/control-center/src/components/SourceInboxSurfacePanel.tsx",
)
REQUIRED_MARKERS = {
    "src/ultimate_ai_agent/core/storage/founder_loop.py": (
        '"connector_read_platform": connector_read_platform',
    ),
    "apps/control-center/src/components/ConnectorReadPlatformCard.tsx": (
        "ECO-009 connector read platform",
        "caller-supplied redacted snapshot only",
        "Live account",
        "Connector writes",
    ),
    "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md": (
        "ECO-009 accepts one exact local calendar metadata snapshot adapter",
    ),
}
PROHIBITED_IMPORTS = {
    "browserbase",
    "firecrawl",
    "http.client",
    "httpx",
    "playwright",
    "requests",
    "selenium",
    "subprocess",
    "urllib.request",
    "urllib3",
}
DENIED_AUTHORITY_FRAGMENTS = (
    "external_read_performed: Literal[True]",
    "network_access_performed: Literal[True]",
    "account_auth_performed: Literal[True]",
    "connector_write_performed: Literal[True]",
    "raw_content_included: Literal[True]",
    "model_call_enabled: Literal[True]",
    "model_call_performed: Literal[True]",
    "production_authority_granted: Literal[True]",
)


def _prohibited_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    findings: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [item.name for item in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [
                node.module,
                *(f"{node.module}.{item.name}" for item in node.names),
            ]
        else:
            continue
        for name in names:
            findings.update(
                item
                for item in PROHIBITED_IMPORTS
                if name == item or name.startswith(f"{item}.")
            )
    return findings


def _operational_failures() -> list[str]:
    failures: list[str] = []
    observed_at = datetime(2026, 8, 22, 16, 0, tzinfo=timezone.utc)
    platform = ConnectorReadPlatform()
    platform.register_calendar_snapshot(
        CalendarMetadataSnapshotAdapter(
            source_ref="connector-source-ref:eco-009:verifier",
            workspace_ref="workspace-ref:eco-009:verifier",
            rows=(
                CalendarMetadataSnapshotRow(
                    event_ref="calendar-event-ref:eco-009:verifier",
                    starts_at=observed_at,
                    ends_at=observed_at + timedelta(hours=1),
                    availability_ref="availability-ref:busy",
                    provenance_ref="provenance-ref:eco-009:verifier",
                    source_revision_ref="source-revision-ref:eco-009:verifier-v1",
                ),
            ),
            provenance_ref="provenance-ref:eco-009:verifier",
        )
    )
    outcome = platform.read(
        ConnectorReadRequest(
            request_ref="request-ref:eco-009:verifier",
            workspace_ref="workspace-ref:eco-009:verifier",
            source_ref="connector-source-ref:eco-009:verifier",
            field_refs=("event_ref", "starts_at", "ends_at"),
            starts_at=observed_at,
            ends_at=observed_at + timedelta(days=1),
        ),
        now=observed_at,
    )
    if outcome.status != ConnectorReadStatus.completed or len(outcome.items) != 1:
        failures.append("bounded snapshot read did not complete")
    if any(
        (
            outcome.external_read_performed,
            outcome.network_access_performed,
            outcome.account_auth_performed,
            outcome.connector_write_performed,
            outcome.raw_content_included,
            outcome.model_call_performed,
            outcome.production_authority_granted,
        )
    ):
        failures.append("snapshot read claimed blocked authority")
    posture = build_eco009_connector_read_platform_posture(platform)
    if posture["status"] != "snapshot_source_ready":
        failures.append("configured platform posture was not ready")
    for flag in (
        "live_account_connected",
        "network_access_enabled",
        "account_auth_enabled",
        "background_sync_enabled",
        "raw_content_enabled",
        "connector_write_enabled",
        "production_authority_enabled",
    ):
        if posture[flag] is not False:
            failures.append(f"blocked posture flag was enabled: {flag}")
    return failures


def verify() -> list[str]:
    failures = [
        f"missing ECO-009 artifact: {path}"
        for path in REQUIRED_FILES
        if not (ROOT / path).is_file()
    ]
    core_path = ROOT / REQUIRED_FILES[0]
    if core_path.is_file():
        for name in sorted(_prohibited_imports(core_path)):
            failures.append(f"forbidden ECO-009 runtime import: {name}")
        source = core_path.read_text(encoding="utf-8")
        for fragment in DENIED_AUTHORITY_FRAGMENTS:
            if fragment in source:
                failures.append(f"denied ECO-009 authority fragment: {fragment}")
    for relative_path, markers in REQUIRED_MARKERS.items():
        path = ROOT / relative_path
        if not path.is_file():
            failures.append(f"missing ECO-009 artifact: {relative_path}")
            continue
        content = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in content:
                failures.append(f"missing ECO-009 marker in {relative_path}: {marker}")
    failures.extend(_operational_failures())
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("ECO-009 exact read-only connector verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
