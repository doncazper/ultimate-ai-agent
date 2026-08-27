#!/usr/bin/env python3
"""Verify the exact approval-bound FIN-002 synthetic import commit slice."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.finance.authority import (
    FinanceMutationRequest,
    build_exact_finance_lease,
    build_finance_import_commit_capability_manifest,
)
from ultimate_ai_agent.core.finance.crypto import InMemoryFinanceCryptoBackend
from ultimate_ai_agent.core.finance.import_preview import (
    preview_synthetic_csv_fixture,
)
from ultimate_ai_agent.core.finance.import_commit import FIN002_IMPORT_SAFE_DISABLE_REF
from ultimate_ai_agent.core.finance.models import stable_finance_ref
from ultimate_ai_agent.core.finance.repository import FinanceRepository
from ultimate_ai_agent.core.finance.service import (
    FinanceKernelService,
    finance_repository_ref,
)


ROOT = Path(__file__).resolve().parent.parent
BOOK_FIXTURE_REF = "fixture-ref:finance/FIN-001:balanced-local-book:v1"
IMPORT_FIXTURE_REF = "fixture-ref:finance/FIN-002:synthetic-csv-clean:v1"
REQUIRED_DOC_PHRASES = {
    "docs/product/UAA_FINANCE_FIN002_SYNTHETIC_IMPORT_PREVIEW.md": (
        "approval-bound synthetic commit",
        "arbitrary operator-supplied financial data is rejected",
        "independent fin-000 promotion remains pending",
    ),
    "docs/implementation/UAA_FINANCE_COMPLIANCE_IMPLEMENTATION_PLAN.md": (
        "fin-002b",
        "fingerprint census",
        "no arbitrary file",
    ),
    "docs/kanban/current_board.md": (
        "fin-002b",
        "synthetic import commit",
    ),
}


def _bind_and_execute(
    service: FinanceKernelService,
    request: FinanceMutationRequest,
    *,
    now: datetime,
):
    preview = service.prepare(request, now=now)
    approvals = LocalApprovalAuthority()
    approvals.create_request(preview.approval_request)
    approvals.grant(
        preview.approval_request.approval_request_id,
        approved_by_actor_id="actor-ref:finance:fin002b-verifier",
        approval_ref=preview.expected_approval_ref,
        expires_at=now + timedelta(minutes=10),
    )
    bound = FinanceMutationRequest.model_validate(
        {
            **request.model_dump(mode="python"),
            "approval_ref": preview.expected_approval_ref,
            "exact_scope_ref": preview.exact_scope_ref,
            "action_envelope_ref": preview.action_envelope_ref,
        }
    )
    lease = build_exact_finance_lease(
        preview,
        lease_ref=stable_finance_ref(
            "authority-lease-ref:finance:fin002b-verifier",
            {"preview_ref": preview.preview_ref},
        ),
        issued_at=now - timedelta(seconds=1),
        expires_at=now + timedelta(minutes=10),
    )
    return service.execute(
        bound,
        preview=preview,
        approval_authority=approvals,
        lease_provider=lambda: [lease],
        clock=lambda: now,
    )


def verify() -> list[str]:
    failures: list[str] = []
    capability = build_finance_import_commit_capability_manifest()
    if (
        not capability.approval_required
        or not capability.single_writer_required
        or capability.connector_write_allowed
        or capability.provider_runtime_allowed
        or capability.browser_runtime_allowed
    ):
        failures.append("FIN002B exact capability authority posture drifted")

    with TemporaryDirectory(prefix="uaa-fin002b-verify-") as directory:
        repository_root = Path(directory) / "protected-book"
        service = FinanceKernelService(
            FinanceRepository(
                repository_root,
                crypto_backend=InMemoryFinanceCryptoBackend(),
            )
        )
        now = datetime.now(UTC)
        create_request = FinanceMutationRequest(
            operation="create",
            repository_ref=finance_repository_ref(repository_root),
            fixture_ref=BOOK_FIXTURE_REF,
            expected_revision=0,
            request_ref="request-ref:finance:fin002b-verifier-create",
            idempotency_ref="idempotency-ref:finance:fin002b-verifier-create",
        )
        _bind_and_execute(service, create_request, now=now)
        preview = preview_synthetic_csv_fixture(IMPORT_FIXTURE_REF)
        import_request = FinanceMutationRequest(
            operation="import_commit",
            repository_ref=finance_repository_ref(repository_root),
            fixture_ref=preview.fixture_ref,
            import_preview_ref=preview.preview_ref,
            import_profile_ref=preview.profile_ref,
            import_fixture_manifest_ref=preview.import_fixture_manifest_ref,
            import_candidate_refs=tuple(
                item.candidate_ref for item in preview.candidates
            ),
            import_source_fingerprint_refs=tuple(
                item.source_fingerprint_ref for item in preview.observations
            ),
            expected_revision=1,
            request_ref="request-ref:finance:fin002b-verifier-commit",
            idempotency_ref="idempotency-ref:finance:fin002b-verifier-commit",
            safe_disable_ref=FIN002_IMPORT_SAFE_DISABLE_REF,
        )
        proof, receipt = _bind_and_execute(service, import_request, now=now)
        snapshot = service.repository.load_snapshot(
            request_ref="request-ref:finance:fin002b-verifier-read"
        )
        if (
            receipt.phase != "committed"
            or receipt.operation != "import_commit"
            or proof.mutation_receipt_ref != receipt.receipt_ref
            or snapshot.revision != 2
            or len(snapshot.import_commits) != 1
            or len(snapshot.journal_entries) != 8
            or any(
                sum(posting.signed_amount_minor for posting in entry.postings) != 0
                for entry in snapshot.journal_entries
            )
        ):
            failures.append("FIN002B atomic balanced commit proof drifted")
        replay_proof, replay_receipt = _bind_and_execute(
            service, import_request, now=now
        )
        if (
            not replay_proof.replayed
            or not replay_receipt.replayed
            or replay_receipt.receipt_ref != receipt.receipt_ref
            or replay_proof.proof_ref != proof.proof_ref
        ):
            failures.append("FIN002B exact idempotent replay drifted")
        read_model = snapshot.redacted_read_model()
        if (
            read_model.get("raw_financial_values_included") is not False
            or read_model.get("real_financial_data_included") is not False
            or read_model["counts"].get("imported_candidates") != 2
        ):
            failures.append("FIN002B redacted read model drifted")

    for relative, phrases in REQUIRED_DOC_PHRASES.items():
        text = (ROOT / relative).read_text(encoding="utf-8").lower()
        for phrase in phrases:
            if phrase not in text:
                failures.append(
                    f"FIN002B truth phrase missing from {relative}: {phrase}"
                )
    return failures


def main() -> int:
    failures = verify()
    payload = {
        "schema_version": "uaa-finance-fin002b-verification.v1",
        "status": "failed" if failures else "verified",
        "failure_refs": [
            stable_finance_ref(
                "verification-failure-ref:finance/FIN-002B",
                {"failure": failure},
            )
            for failure in failures
        ],
        "synthetic_only": True,
        "raw_source_content_included": False,
        "real_financial_data_included": False,
        "connector_call_performed": False,
        "ocr_performed": False,
    }
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
