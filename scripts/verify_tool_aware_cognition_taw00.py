#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.evals.tool_aware_baseline import (  # noqa: E402
    TAW00_ACCEPTANCE_EVIDENCE_CONTRACT_COMPLETE,
    TAW00FounderDogfoodProfile,
    TAW00Protocol,
    SourceProjection,
    durable_payload_has_forbidden_fields,
    founder_dogfood_readiness,
    protocol_readiness,
)

PROTOCOL = ROOT / "docs/evals/tool_aware_cognition_taw00_protocol_v1.json"
FOUNDER_DOGFOOD_PROFILE = (
    ROOT / "docs/evals/tool_aware_cognition_q22_founder_dogfood_v1.json"
)
LEDGER = ROOT / "docs/evals/tool_aware_cognition_taw00_convergence_ledger_v1.json"
SOURCE_PROJECTION = (
    ROOT / "docs/evals/tool_aware_cognition_taw00_source_projection_v1.json"
)
SCHEMA = ROOT / "docs/schemas/tool_aware_cognition_taw00.schema.json"

EXPECTED_REQUIREMENTS = {
    "requirement-ref:taw00:capability-lab-reuse",
    "requirement-ref:taw00:development-corpus",
    "requirement-ref:taw00:holdout-commitment",
    "requirement-ref:taw00:blind-scoring",
    "requirement-ref:taw00:statistics",
    "requirement-ref:taw00:candidate-lock",
    "requirement-ref:taw00:supported-matrices",
    "requirement-ref:taw00:independent-custody",
    "requirement-ref:taw00:accepted-current-baseline",
    "requirement-ref:taw00:routing-or-prompt-change",
}
FACILITY_FILES = (
    "docs/evals/tool_aware_cognition_q22_founder_dogfood_v1.json",
    "src/ultimate_ai_agent/core/evals/tool_aware_baseline.py",
    "src/ultimate_ai_agent/core/evals/tool_aware_corpus.py",
    "src/ultimate_ai_agent/core/evals/tool_aware_evidence.py",
    "src/ultimate_ai_agent/core/evals/tool_aware_statistics.py",
    "scripts/run_tool_aware_baseline.py",
    "scripts/run_tool_aware_holdout_custodian.py",
    "scripts/run_tool_aware_holdout_opening.py",
)
FORBIDDEN_RUNTIME_TOKENS = (
    "import requests",
    "import httpx",
    "import openai",
    "shell=true",
    "os.system(",
    "urllib.request",
    "playwright",
    "selenium",
)
EXPECTED_SOURCE_ROOT_PATH_REFS = tuple(
    f"repo-path-ref:{path}"
    for path in sorted(
        (
            "pyproject.toml",
            "uv.lock",
            "ultimate_ai_agent_prompt_registry_v0_5_2.json",
            "src/ultimate_ai_agent/api/app.py",
            "src/ultimate_ai_agent/api/control_center.py",
            "src/ultimate_ai_agent/api/manifest.py",
            "src/ultimate_ai_agent/core/approvals/authority.py",
            "src/ultimate_ai_agent/core/capabilities/catalog.py",
            "src/ultimate_ai_agent/core/capabilities/context.py",
            "src/ultimate_ai_agent/core/capabilities/discovery.py",
            "src/ultimate_ai_agent/core/capabilities/executor.py",
            "src/ultimate_ai_agent/core/capabilities/models.py",
            "src/ultimate_ai_agent/core/capabilities/policy.py",
            "src/ultimate_ai_agent/core/capabilities/registry.py",
            "src/ultimate_ai_agent/core/capabilities/selection.py",
            "src/ultimate_ai_agent/core/chat/operator_surface.py",
            "src/ultimate_ai_agent/core/decision_router/contracts.py",
            "src/ultimate_ai_agent/core/decision_router/executor_fence.py",
            "src/ultimate_ai_agent/core/decision_router/harness_binding.py",
            "src/ultimate_ai_agent/core/decision_router/parallel_preflight.py",
            "src/ultimate_ai_agent/core/decision_router/prepared_turn.py",
            "src/ultimate_ai_agent/core/decision_router/route_binding.py",
            "src/ultimate_ai_agent/core/decision_router/turn_classifier.py",
            "src/ultimate_ai_agent/core/decision_router/turn_contracts.py",
            "src/ultimate_ai_agent/core/execution/policy.py",
            "src/ultimate_ai_agent/core/prompt_compiler/compiler.py",
            "src/ultimate_ai_agent/core/prompt_compiler/contracts.py",
            "src/ultimate_ai_agent/core/prompt_compiler/schema_validation.py",
        )
    )
)


def _load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _git_bytes(revision_ref: str, path_ref: str) -> bytes:
    revision = revision_ref.removeprefix("git-sha:")
    relative = path_ref.removeprefix("repo-path-ref:")
    if not path_ref.startswith("repo-path-ref:") or ".." in Path(relative).parts:
        raise ValueError("source projection path ref is invalid")
    completed = subprocess.run(  # noqa: S603
        ["git", "-C", str(ROOT), "show", f"{revision}:{relative}"],
        check=True,
        capture_output=True,
    )
    return completed.stdout


def verify(
    *,
    protocol_payload: object | None = None,
    founder_dogfood_payload: object | None = None,
    ledger_payload: object | None = None,
    source_projection_payload: object | None = None,
    check_files: bool = True,
) -> list[str]:
    failures: list[str] = []
    validator: Draft202012Validator | None = None
    try:
        schema = _load(SCHEMA)
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"TAW-00 schema is invalid: {exc}")

    try:
        raw_protocol = (
            protocol_payload if protocol_payload is not None else _load(PROTOCOL)
        )
        if validator is not None:
            failures.extend(
                f"TAW-00 protocol schema validation failed: {error.message}"
                for error in validator.iter_errors(raw_protocol)
            )
        if durable_payload_has_forbidden_fields(raw_protocol):
            failures.append("TAW-00 protocol contains forbidden durable fields")
        protocol = TAW00Protocol.model_validate(raw_protocol)
        readiness = protocol_readiness(protocol)
        if readiness["status"] != "blocked":
            failures.append(
                "checked-in protocol must remain blocked until external inputs exist"
            )
        if protocol.status != "pending_configuration_freeze":
            failures.append("checked-in protocol must not claim a locked configuration")
        if not TAW00_ACCEPTANCE_EVIDENCE_CONTRACT_COMPLETE:
            failures.append("TAW-00 typed acceptance evidence contract is incomplete")
    except Exception as exc:  # noqa: BLE001
        failures.append(f"TAW-00 protocol validation failed: {exc}")

    try:
        founder_payload = (
            founder_dogfood_payload
            if founder_dogfood_payload is not None
            else _load(FOUNDER_DOGFOOD_PROFILE)
        )
        if validator is not None:
            failures.extend(
                "TAW-00 founder dogfood schema validation failed: " + error.message
                for error in validator.iter_errors(founder_payload)
            )
        if durable_payload_has_forbidden_fields(founder_payload):
            failures.append("TAW-00 founder dogfood profile contains forbidden fields")
        founder_profile = TAW00FounderDogfoodProfile.model_validate(founder_payload)
        founder_report = founder_dogfood_readiness(founder_profile)
        if founder_report["status"] != "accepted_for_bounded_implementation":
            failures.append(
                "TAW-00 founder dogfood profile is not implementation-ready"
            )
        if founder_report["independent_promotion_ready"] is not False:
            failures.append("TAW-00 founder dogfood profile overclaims promotion")
        if any(
            founder_report[field] is not False
            for field in (
                "runtime_model_calls_added",
                "provider_calls_added",
                "authority_added",
            )
        ):
            failures.append("TAW-00 founder dogfood profile grants runtime authority")
    except Exception as exc:  # noqa: BLE001
        failures.append(f"TAW-00 founder dogfood validation failed: {exc}")

    try:
        ledger = ledger_payload if ledger_payload is not None else _load(LEDGER)
        if not isinstance(ledger, dict):
            raise ValueError("ledger must be an object")
        requirements = ledger.get("requirements")
        if not isinstance(requirements, list):
            raise ValueError("ledger requirements must be a list")
        refs = [
            item.get("requirement_ref")
            for item in requirements
            if isinstance(item, dict)
        ]
        if set(refs) != EXPECTED_REQUIREMENTS or len(refs) != len(
            EXPECTED_REQUIREMENTS
        ):
            failures.append("TAW-00 convergence ledger requirement coverage drifted")
        if set(ledger) != {
            "ledger_ref",
            "protocol_ref",
            "status",
            "requirements",
            "routing_changes_added",
            "prompt_changes_added",
            "runtime_model_calls_added",
            "authority_added",
            "next_safe_action",
        }:
            failures.append("TAW-00 convergence ledger shape drifted")
        if (
            ledger.get("status")
            != "founder_dogfood_implementation_accepted_independent_promotion_pending"
        ):
            failures.append("TAW-00 convergence ledger overclaims completion")
        for item in requirements:
            if not isinstance(item, dict) or set(item) != {
                "requirement_ref",
                "state",
                "evidence_refs",
            }:
                failures.append("TAW-00 convergence ledger requirement shape drifted")
                continue
            if item.get("state") not in {
                "implemented",
                "scaffolded",
                "blocked",
                "not_started",
            }:
                failures.append("TAW-00 convergence ledger requirement state drifted")
            if not isinstance(item.get("evidence_refs"), list):
                failures.append("TAW-00 convergence ledger evidence refs drifted")
        for flag in (
            "routing_changes_added",
            "prompt_changes_added",
            "runtime_model_calls_added",
            "authority_added",
        ):
            if ledger.get(flag) is not False:
                failures.append(f"TAW-00 convergence ledger enables {flag}")
        if durable_payload_has_forbidden_fields(ledger):
            failures.append(
                "TAW-00 convergence ledger contains forbidden durable fields"
            )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"TAW-00 convergence ledger validation failed: {exc}")

    try:
        raw_projection = (
            source_projection_payload
            if source_projection_payload is not None
            else _load(SOURCE_PROJECTION)
        )
        if validator is not None:
            failures.extend(
                f"TAW-00 source projection schema validation failed: {error.message}"
                for error in validator.iter_errors(raw_projection)
            )
        projection = SourceProjection.model_validate(raw_projection)
        path_refs = tuple(item.path_ref for item in projection.entries)
        if path_refs != EXPECTED_SOURCE_ROOT_PATH_REFS:
            failures.append("source projection root inventory drifted")
        for entry in projection.entries:
            content = _git_bytes(projection.source_revision_ref, entry.path_ref)
            digest = f"sha256:{hashlib.sha256(content).hexdigest()}"
            if entry.content_digest_ref != digest:
                failures.append(f"source projection digest drift: {entry.path_ref}")
    except (
        OSError,
        KeyError,
        ValueError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
    ) as exc:
        failures.append(f"TAW-00 source projection validation failed: {exc}")

    if check_files:
        for relative in FACILITY_FILES:
            text = (ROOT / relative).read_text(encoding="utf-8").lower()
            for token in FORBIDDEN_RUNTIME_TOKENS:
                if token in text:
                    failures.append(
                        f"{relative} contains forbidden runtime token {token}"
                    )
    return failures


def main() -> int:
    failures = verify()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("TAW-00 fail-closed acceptance contract verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
