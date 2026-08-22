#!/usr/bin/env python3
"""Inspect ECO-010 deterministic proposal intelligence without committing work."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ultimate_ai_agent.core.ecosystem.proposals import (
    ProposalCandidateKind,
    ProposalExtractionRequest,
    ProposalFact,
    ProposalSourceRevisionBinding,
    extract_proposal_candidates,
)


def _synthetic_request() -> ProposalExtractionRequest:
    requested_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    facts = tuple(
        ProposalFact(
            workspace_ref="workspace-ref:eco-010:synthetic",
            fact_ref=f"proposal-fact-ref:eco-010:{kind.value}",
            source_artifact_ref=f"source-artifact-ref:eco-010:{kind.value}",
            source_revision_ref=f"source-revision-ref:eco-010:{kind.value}:v1",
            candidate_kind=kind,
            safe_summary=f"Synthetic cited {kind.value} candidate for review.",
            evidence_refs=(f"evidence-ref:eco-010:{kind.value}",),
            subject_ref=f"subject-ref:eco-010:{kind.value}",
            participant_refs=("person-ref:eco-010:participant",)
            if kind == ProposalCandidateKind.meeting
            else (),
            occurred_at="2026-08-23T16:00:00Z"
            if kind in {ProposalCandidateKind.event, ProposalCandidateKind.meeting}
            else None,
            confidence_percent=85,
        )
        for kind in ProposalCandidateKind
    )
    return ProposalExtractionRequest(
        workspace_ref="workspace-ref:eco-010:synthetic",
        facts=facts,
        source_revision_bindings=tuple(
            ProposalSourceRevisionBinding(
                source_artifact_ref=fact.source_artifact_ref,
                current_source_revision_ref=fact.source_revision_ref,
            )
            for fact in facts
        ),
        requested_at=requested_at,
    )


def _load_request(path: Path) -> ProposalExtractionRequest:
    try:
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("ECO_PROPOSAL_INPUT_JSON_INVALID") from exc
    try:
        return ProposalExtractionRequest.model_validate(payload)
    except ValidationError as exc:
        raise ValueError("ECO_PROPOSAL_INPUT_CONTRACT_INVALID") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect deterministic cited proposal candidates. This command "
            "performs no source read, model call, ChangeSet, approval, or write."
        )
    )
    parser.add_argument(
        "--input-json",
        type=Path,
        help="Optional local JSON request; the path is never included in output.",
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    try:
        request = (
            _load_request(args.input_json) if args.input_json else _synthetic_request()
        )
        result = extract_proposal_candidates(request)
    except ValueError as exc:
        print(json.dumps({"status": "blocked", "code": str(exc)}, sort_keys=True))
        return 2
    print(
        json.dumps(
            result,
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
