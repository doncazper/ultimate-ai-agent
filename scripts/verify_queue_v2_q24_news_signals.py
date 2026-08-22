#!/usr/bin/env python3
"""Verify the bounded Q24 News and Signals implementation."""

from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.news_signals import (  # noqa: E402
    NewsSignalArtifact,
    NewsSignalSource,
    build_news_signals_summary,
)


REQUIRED_FILES = (
    "src/ultimate_ai_agent/core/news_signals/read_model.py",
    "src/ultimate_ai_agent/api/founder_loop.py",
    "scripts/inspect_news_signals.py",
    "tests/test_queue_v2_q24_news_signals.py",
    "docs/control_center/NEWS_AND_SIGNALS_MODULE_PLAN.md",
    "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md",
    "apps/control-center/src/components/NewsSignalsPreviewPanel.tsx",
)
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
REQUIRED_MARKERS = {
    "docs/control_center/NEWS_AND_SIGNALS_MODULE_PLAN.md": (
        "backend-owned",
        "already-redacted",
        "external content remains untrusted",
    ),
    "apps/control-center/src/components/NewsSignalsPreviewPanel.tsx": (
        "Backend-owned read model",
        "No graduated news source",
        "external content is untrusted",
    ),
    "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md": (
        "Q24 News and Signals",
    ),
}
DENIED_AUTHORITY_FRAGMENTS = (
    '"live_fetch_enabled": True',
    '"authenticated_source_enabled": True',
    '"background_polling_enabled": True',
    '"model_summarization_enabled": True',
    '"connector_write_enabled": True',
    '"action_authority_granted": True',
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
    source = NewsSignalSource(
        source_ref="source-ref:q24:verifier",
        source_kind="local",
        safe_label="Verifier source",
        state="ready",
        observed_at="2026-08-22T16:00:00Z",
    )
    artifact = NewsSignalArtifact(
        artifact_ref="signal-ref:q24:verifier",
        source_ref=source.source_ref,
        source_revision_ref="source-revision-ref:q24:verifier-v1",
        content_digest_ref="content-digest-ref:q24:verifier",
        cluster_ref="cluster-ref:q24:verifier",
        claim_ref="claim-ref:q24:verifier",
        title="Verifier redacted artifact",
        safe_summary="Bounded summary from an already-redacted local artifact.",
        source_label=source.safe_label,
        topic_ref="topic-ref:q24:verifier",
        published_at="2026-08-22T15:30:00Z",
        observed_at="2026-08-22T16:00:00Z",
        confidence_percent=90,
        evidence_class="primary",
        provenance_refs=("provenance-ref:q24:verifier",),
    )
    summary = build_news_signals_summary(
        sources=(source,),
        artifacts=(artifact,),
        now=datetime(2026, 8, 22, 16, 0, tzinfo=timezone.utc),
    )
    failures: list[str] = []
    if summary["status"] != "ready" or len(summary["items"]) != 1:
        failures.append("backend-owned artifact projection was not ready")
    for flag in (
        "live_fetch_enabled",
        "authenticated_source_enabled",
        "background_polling_enabled",
        "model_summarization_enabled",
        "connector_write_enabled",
        "action_authority_granted",
    ):
        if summary[flag] is not False:
            failures.append(f"blocked Q24 authority flag was enabled: {flag}")
    if summary["morning_briefing_projection"]["candidate_refs"] != [
        "signal-ref:q24:verifier"
    ]:
        failures.append("eligible signal was not projected into briefing candidates")
    return failures


def verify() -> list[str]:
    failures = [
        f"missing Q24 artifact: {path}"
        for path in REQUIRED_FILES
        if not (ROOT / path).is_file()
    ]
    core_path = ROOT / REQUIRED_FILES[0]
    if core_path.is_file():
        for name in sorted(_prohibited_imports(core_path)):
            failures.append(f"forbidden Q24 runtime import: {name}")
        source = core_path.read_text(encoding="utf-8")
        for fragment in DENIED_AUTHORITY_FRAGMENTS:
            if fragment in source:
                failures.append(f"denied Q24 authority fragment: {fragment}")
    for relative_path, markers in REQUIRED_MARKERS.items():
        path = ROOT / relative_path
        if not path.is_file():
            failures.append(f"missing Q24 artifact: {relative_path}")
            continue
        content = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in content:
                failures.append(f"missing Q24 marker in {relative_path}: {marker}")
    failures.extend(_operational_failures())
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("Q24 News and Signals verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
