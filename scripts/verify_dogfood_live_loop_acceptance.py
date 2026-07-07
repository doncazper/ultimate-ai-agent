#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ultimate_ai_agent.core.authority import (  # noqa: E402
    AUTHORITY_STATE_DIR_ENV,
    AuthorityCapability,
    AuthorityDomain,
    AuthorityLease,
    AuthorityLeaseIssueRequest,
    AuthorityLeaseStore,
    TrustMode,
)
from ultimate_ai_agent.core.authority.approval_validation import (  # noqa: E402
    issue_authority_lease_with_test_approval,
)
from ultimate_ai_agent.core.control_center.dogfood_live_loop import (  # noqa: E402
    DOGFOOD_LIVE_LOOP_ACTION_REF,
    DOGFOOD_LIVE_LOOP_FIXTURE_REF,
    DogfoodLiveLoopAcceptanceReadModel,
    build_dogfood_live_loop_acceptance_read_model,
    validate_dogfood_live_loop_acceptance,
)
from ultimate_ai_agent.core.storage import FounderLoopRepository  # noqa: E402


CONTRACT = SRC / "ultimate_ai_agent/core/control_center/dogfood_live_loop.py"
DEV_CLI = ROOT / "scripts/dev/uaa_founder_loop.py"
FOCUSED_TEST = ROOT / "tests/test_dogfood_live_loop_acceptance.py"
FRONTEND_TEST = ROOT / "apps/control-center/src/App.test.tsx"
DOC = ROOT / "docs/control_center/DOGFOOD_LIVE_LOOP_ACCEPTANCE.md"
INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"
RELEASE_SURFACE = ROOT / "docs/control_center/CONTROL_CENTER_RELEASE_SURFACE.md"
TRUTH_PACKET = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"


def _workspace_write_lease() -> AuthorityLease:
    return AuthorityLease(
        lease_ref="authority-lease-ref:verifier-dogfood-workspace-write",
        mode=TrustMode.ask_before_changes,
        domains={AuthorityDomain.workspace: [AuthorityCapability.write]},
        safe_summary=(
            "Verifier lease grants Workspace write for dogfood local task commit."
        ),
    )


def _issue_workspace_write_lease(state_dir: Path) -> None:
    issue_authority_lease_with_test_approval(
        AuthorityLeaseStore(state_dir),
        AuthorityLeaseIssueRequest(
            mode=TrustMode.ask_before_changes,
            requested_domains={
                AuthorityDomain.workspace: [AuthorityCapability.write],
            },
            decision_reason_ref="decision-reason-ref:verifier-dogfood-authority-lease",
            safe_summary=(
                "Verifier session lease grants Workspace write for dogfood CLI seeding."
            ),
        ),
        idempotency_ref="idempotency-ref:verifier-dogfood-authority-lease",
        approval_ref="approval-ref:verifier:dogfood-authority-lease",
    )


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _require(path: Path, snippets: list[str], failures: list[str]) -> None:
    text = _read(path)
    for snippet in snippets:
        if snippet not in text:
            failures.append(f"{path.relative_to(ROOT)} missing {snippet!r}")


def _require_absent(path: Path, snippets: list[str], failures: list[str]) -> None:
    text = _read(path).lower()
    for snippet in snippets:
        if snippet.lower() in text:
            failures.append(
                f"{path.relative_to(ROOT)} contains forbidden snippet {snippet!r}"
            )


def _validate_live_read_model(failures: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="dogfood-live-loop-") as temp_dir:
        state_dir = Path(temp_dir) / "founder_loop"
        authority_state_dir = Path(temp_dir) / "authority"
        _issue_workspace_write_lease(authority_state_dir)
        repo = FounderLoopRepository(
            state_dir,
            active_authority_leases=[_workspace_write_lease()],
        )
        read_model = build_dogfood_live_loop_acceptance_read_model(
            repo=repo,
            seed_fixture=True,
        )
        replayed_model = build_dogfood_live_loop_acceptance_read_model(
            repo=repo,
            seed_fixture=True,
        )

        result = subprocess.run(
            [
                sys.executable,
                str(DEV_CLI),
                "--state-dir",
                str(state_dir),
                "inspect-dogfood-live-loop",
                "--seed-fixture",
            ],
            check=False,
            capture_output=True,
            text=True,
            env={**os.environ, AUTHORITY_STATE_DIR_ENV: str(authority_state_dir)},
        )

    if read_model.get("fixture_ref") != DOGFOOD_LIVE_LOOP_FIXTURE_REF:
        failures.append("Dogfood live loop fixture ref drifted")
    if read_model.get("action_ref") != DOGFOOD_LIVE_LOOP_ACTION_REF:
        failures.append("Dogfood live loop action ref drifted")
    if replayed_model.get("local_task_commit_receipt_ref") != read_model.get(
        "local_task_commit_receipt_ref"
    ):
        failures.append("Dogfood live loop seed is not replay-stable")
    if read_model.get("status") != "complete_local_dogfood_loop_proven":
        failures.append("Dogfood live loop read model is not complete")

    try:
        DogfoodLiveLoopAcceptanceReadModel(**read_model)
    except Exception as exc:
        failures.append(f"Dogfood live loop read model failed validation: {exc}")
    failures.extend(validate_dogfood_live_loop_acceptance(read_model))

    if result.returncode != 0:
        failures.append("Dogfood live loop CLI failed")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        failures.append("Dogfood live loop CLI emitted invalid JSON")
        return
    if payload.get("command_ref") != (
        "repo-local-command:founder-loop-inspect-dogfood-live-loop"
    ):
        failures.append("Dogfood live loop CLI command ref drifted")
    if payload.get("safe_refs_only") is not True:
        failures.append("Dogfood live loop CLI missing safe refs flag")
    if payload.get("raw_paths_omitted") is not True:
        failures.append("Dogfood live loop CLI missing raw path omission flag")
    failures.extend(
        validate_dogfood_live_loop_acceptance(
            payload.get("dogfood_live_loop_acceptance") or {}
        )
    )
    if str(state_dir).lower() in result.stdout.lower():
        failures.append("Dogfood live loop CLI leaked temp state path")

    frontend_text = _read(FRONTEND_TEST)
    for ref_name, ref_value in {
        "action_ref": read_model.get("action_ref"),
        "run_ref": read_model.get("run_ref"),
        "primary_proof_ref": read_model.get("primary_proof_ref"),
        "local_task_commit_proof_ref": read_model.get("local_task_commit_proof_ref"),
        "local_task_commit_receipt_ref": read_model.get(
            "local_task_commit_receipt_ref"
        ),
        "local_task_ref": read_model.get("local_task_ref"),
        "evidence_ref": next(iter(read_model.get("evidence_refs") or []), None),
        "memory_candidate_ref": next(
            iter(read_model.get("memory_candidate_refs") or []),
            None,
        ),
    }.items():
        if not isinstance(ref_value, str) or not ref_value:
            failures.append(f"Dogfood live loop missing generated {ref_name}")
        elif ref_value not in frontend_text:
            failures.append(
                f"Frontend dogfood fixture missing backend generated {ref_name}"
            )


def verify() -> list[str]:
    failures: list[str] = []
    for path in [
        CONTRACT,
        DEV_CLI,
        FOCUSED_TEST,
        FRONTEND_TEST,
        DOC,
        INDEX,
        RELEASE_SURFACE,
        TRUTH_PACKET,
    ]:
        if not path.exists():
            failures.append(f"missing {path.relative_to(ROOT)}")

    _require(
        CONTRACT,
        [
            "DogfoodLiveLoopAcceptanceReadModel",
            "seed_dogfood_live_loop_fixture",
            "validate_dogfood_live_loop_acceptance",
            "DOGFOOD_LIVE_LOOP_BLOCKED_AUTHORITY_REFS",
            "provider_model_call_enabled: bool = False",
            "connector_write_enabled: bool = False",
            "production_authority_enabled: bool = False",
        ],
        failures,
    )
    _require(
        DEV_CLI,
        [
            "inspect-dogfood-live-loop",
            "repo-local-command:founder-loop-inspect-dogfood-live-loop",
            "--seed-fixture",
            "build_dogfood_live_loop_acceptance_read_model",
        ],
        failures,
    )
    _require(
        FOCUSED_TEST,
        [
            "test_dogfood_live_loop_acceptance_seeds_one_complete_local_loop",
            "test_dogfood_live_loop_fixture_blocks_preexisting_non_dogfood_receipt",
            "test_dogfood_live_loop_validator_rejects_incomplete_or_nondeterministic_refs",
            "test_dogfood_live_loop_cli_inspects_full_loop_with_safe_refs",
        ],
        failures,
    )
    _require(
        FRONTEND_TEST,
        [
            "renders one coherent backend-owned dogfood loop across shared surfaces",
            "proof-ref:local-task-commit:founder-action-local-task-create-scorecard",
            "receipt:founder-loop-local-task:founder-action-local-task-create-scorecard",
        ],
        failures,
    )
    _require(
        DOC,
        [
            "Dogfood Live Loop Acceptance",
            "inspect-dogfood-live-loop --seed-fixture",
            "scripts/verify_dogfood_live_loop_acceptance.py",
            "No broad authority is added",
        ],
        failures,
    )
    _require(
        INDEX,
        ["Dogfood Live Loop Acceptance", "scripts/verify_dogfood_live_loop_acceptance.py"],
        failures,
    )
    _require(
        RELEASE_SURFACE,
        ["Dogfood Live Loop Acceptance"],
        failures,
    )
    _require(
        TRUTH_PACKET,
        ["Dogfood Live Loop Acceptance"],
        failures,
    )
    _require_absent(
        DOC,
        [
            "production ready",
            "unrestricted browsing",
            "broad autonomy enabled",
        ],
        failures,
    )

    _validate_live_read_model(failures)
    return failures


def main() -> int:
    failures = verify()
    if failures:
        print("Dogfood live loop acceptance verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Dogfood live loop acceptance verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
