#!/usr/bin/env python3
"""Inspect the Q24 backend-owned News and Signals read model."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.news_signals import (  # noqa: E402
    NewsSignalArtifact,
    NewsSignalSource,
    NewsSignalsRepository,
    build_news_signals_summary,
)


def _synthetic_summary() -> dict[str, object]:
    source = NewsSignalSource(
        source_ref="source-ref:q24:synthetic-demo",
        source_kind="local",
        safe_label="Synthetic local source",
        state="ready",
        observed_at="2026-08-22T16:00:00Z",
        reason_refs=("reason-ref:q24:synthetic-demo-only",),
    )
    artifact = NewsSignalArtifact(
        artifact_ref="signal-ref:q24:synthetic-demo",
        source_ref=source.source_ref,
        source_revision_ref="source-revision-ref:q24:synthetic-demo-v1",
        content_digest_ref="content-digest-ref:q24:synthetic-demo",
        cluster_ref="cluster-ref:q24:synthetic-demo",
        claim_ref="claim-ref:q24:synthetic-demo",
        title="Synthetic source artifact demonstrates the bounded read model",
        safe_summary=(
            "Synthetic metadata demonstrates ranking and briefing eligibility."
        ),
        source_label=source.safe_label,
        topic_ref="topic-ref:q24:governed-agents",
        published_at="2026-08-22T15:30:00Z",
        observed_at="2026-08-22T16:00:00Z",
        confidence_percent=90,
        evidence_class="primary",
        claim_stance="supports",
        provenance_refs=("provenance-ref:q24:synthetic-demo",),
    )
    return build_news_signals_summary(
        sources=(source,),
        artifacts=(artifact,),
        now=datetime(2026, 8, 22, 16, 0, tzinfo=timezone.utc),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect safe-ref News and Signals state without fetching sources."
        )
    )
    parser.add_argument(
        "--synthetic-demo",
        action="store_true",
        help="Inspect a deterministic in-memory synthetic artifact.",
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        help="Inspect a specific local state directory without printing its path.",
    )
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    summary = (
        _synthetic_summary()
        if args.synthetic_demo
        else (
            NewsSignalsRepository(args.state_dir).summary(limit=args.limit)
            if args.state_dir is not None
            else NewsSignalsRepository.from_env().summary(limit=args.limit)
        )
    )
    payload = {
        "schema_version": "uaa-news-signals-inspection.v1",
        "command_ref": "repo-local-command:inspect-news-signals",
        "summary": summary,
        "raw_paths_included": False,
        "raw_source_content_included": False,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
