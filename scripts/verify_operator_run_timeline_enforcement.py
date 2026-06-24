#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.inspect_operator_run_timeline import (  # noqa: E402
    load_operator_run_timeline,
)
from scripts.verification.repo import print_failures_or_success  # noqa: E402


SUCCESS_MESSAGE = "Operator Run Timeline enforcement verification passed."
RAW_CONTENT_FRAGMENTS = (
    "raw prompt",
    "raw_prompt",
    "raw response",
    "raw_response",
    "provider payload",
    "provider_payload",
    "raw provider",
    "raw_provider",
    "prompt body",
    "response body",
    "provider exchange body",
)
DENIED_CONTENT_FLAGS = (
    "prompt_content_stored",
    "response_content_stored",
    "provider_exchange_content_stored",
)
DENIED_AUTHORITY_FLAGS = (
    "provider_model_authority_allowed",
    "provider_sdk_call_enabled",
    "runtime_model_calls_enabled",
    "frontier_ai_routing_allowed",
)
PROVIDER_MISSING_REFS = {
    "provider-ref:not-invoked",
    "model-profile-ref:not-invoked",
}


def verify(timeline: dict[str, Any] | None = None) -> list[str]:
    payload = timeline or load_operator_run_timeline()
    failures: list[str] = []
    _append_timeline_failures(failures, payload)
    _append_usage_summary_failures(
        failures,
        _dict(payload.get("frontier_ai_usage_summary")),
    )
    run_events = payload.get("run_events")
    if not isinstance(run_events, list) or not run_events:
        failures.append("operator run timeline must include run events")
    else:
        for index, event in enumerate(run_events):
            _append_run_event_failures(failures, _dict(event), index)
    _append_raw_string_failures(failures, payload)
    return failures


def _append_timeline_failures(
    failures: list[str],
    payload: dict[str, Any],
) -> None:
    if payload.get("contract_ref") != "contract-ref:operator-run-timeline:v1":
        failures.append("operator run timeline contract ref drifted")
    for field_name in [
        "safe_refs_only",
        "redacted_summaries_only",
    ]:
        if payload.get(field_name) is not True:
            failures.append(f"operator run timeline must keep {field_name} true")
    for field_name in [
        "action_execution_enabled",
        "connector_write_enabled",
        "runtime_model_calls_enabled",
        "provider_sdk_call_enabled",
        "provider_model_authority_allowed",
        *DENIED_CONTENT_FLAGS,
    ]:
        if payload.get(field_name) is True:
            failures.append(f"operator run timeline enabled denied field {field_name}")


def _append_usage_summary_failures(
    failures: list[str],
    usage: dict[str, Any],
) -> None:
    if usage.get("contract_ref") != "contract-ref:frontier-ai-cost-usage-telemetry:v1":
        failures.append("frontier AI usage summary contract ref drifted")
    for field_name in [
        "provider_model_authority_allowed",
        "provider_sdk_call_enabled",
        "runtime_model_calls_enabled",
        *DENIED_CONTENT_FLAGS,
    ]:
        if usage.get(field_name) is True:
            failures.append(f"frontier AI usage summary enabled denied field {field_name}")
    if not _list(usage.get("cost_event_refs")):
        failures.append("frontier AI usage summary missing cost telemetry refs")
    if not _list(usage.get("cost_receipt_refs")):
        failures.append("frontier AI usage summary missing cost receipt refs")
    if not _list(usage.get("cost_blocked_state_refs")):
        failures.append("frontier AI usage summary missing cost authority blockers")
    if usage.get("unknown_paid_cost_requires_approval_before_routing") is not True:
        failures.append("unknown paid cost must require approval before routing")


def _append_run_event_failures(
    failures: list[str],
    event: dict[str, Any],
    index: int,
) -> None:
    event_ref = str(event.get("event_ref") or f"event-index:{index}")
    for field_name in [*DENIED_CONTENT_FLAGS, "provider_model_authority_allowed"]:
        if event.get(field_name) is True:
            failures.append(f"{event_ref} enabled denied field {field_name}")
    cost_usage = _dict(event.get("cost_usage"))
    if not cost_usage:
        failures.append(f"{event_ref} missing cost telemetry")
        return
    _append_cost_usage_failures(failures, cost_usage, event_ref)


def _append_cost_usage_failures(
    failures: list[str],
    cost_usage: dict[str, Any],
    event_ref: str,
) -> None:
    if cost_usage.get("contract_ref") != "contract-ref:frontier-ai-cost-usage-telemetry:v1":
        failures.append(f"{event_ref} cost usage contract ref drifted")
    for ref_field in [
        "cost_event_ref",
        "cost_estimate_ref",
        "captured_usage_ref",
        "budget_decision_ref",
        "provider_ref",
        "model_profile_ref",
    ]:
        if not cost_usage.get(ref_field):
            failures.append(f"{event_ref} missing {ref_field}")
    for field_name in [*DENIED_CONTENT_FLAGS, *DENIED_AUTHORITY_FLAGS]:
        if cost_usage.get(field_name) is True:
            failures.append(f"{event_ref} cost usage enabled denied field {field_name}")

    cost_receipt_refs = _list(cost_usage.get("cost_receipt_refs"))
    cost_blocked_refs = set(_list(cost_usage.get("cost_blocked_state_refs")))
    if not cost_receipt_refs:
        failures.append(f"{event_ref} frontier cost telemetry missing receipt refs")
    if cost_usage.get("frontier_usage_claimed") is True and not cost_receipt_refs:
        failures.append(f"{event_ref} frontier usage claimed without cost receipts")

    unknown_paid_cost = (
        cost_usage.get("unknown_cost") is True
        or cost_usage.get("cost_state_label") == "Unknown paid cost"
    )
    if unknown_paid_cost:
        if cost_usage.get("approval_required_for_unknown_paid_cost") is not True:
            failures.append(f"{event_ref} unknown paid cost is not approval-bound")
        if "blocked-state:unknown-paid-cost-requires-approval" not in cost_blocked_refs:
            failures.append(f"{event_ref} unknown paid cost missing blocked-state ref")

    estimated_cost = _number(cost_usage.get("estimated_cost_usd"))
    max_approved_cost = _number(cost_usage.get("max_approved_cost_usd"))
    if (
        estimated_cost is not None
        and max_approved_cost is not None
        and estimated_cost > max_approved_cost
        and "blocked-state:frontier-ai-cost-budget-exceeded" not in cost_blocked_refs
    ):
        failures.append(f"{event_ref} estimated cost above budget is not blocked")

    provider_ref = str(cost_usage.get("provider_ref") or "")
    model_ref = str(cost_usage.get("model_profile_ref") or "")
    provider_ref_missing = provider_ref in PROVIDER_MISSING_REFS or model_ref in PROVIDER_MISSING_REFS
    if provider_ref_missing:
        if cost_usage.get("provider_authority_state_label") != "No provider authority":
            failures.append(f"{event_ref} missing provider refs must show no authority")
        if "blocked-state:frontier-provider-model-ref-missing" not in cost_blocked_refs:
            failures.append(f"{event_ref} missing provider refs are not blocked")
    elif not cost_receipt_refs:
        failures.append(f"{event_ref} provider/model scope present without cost receipt refs")


def _append_raw_string_failures(
    failures: list[str],
    value: Any,
) -> None:
    for text in _walk_strings(value):
        lowered = text.lower()
        for fragment in RAW_CONTENT_FRAGMENTS:
            if fragment in lowered:
                failures.append(f"operator run evidence includes unsafe content fragment: {fragment}")
                return


def _walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        strings: list[str] = []
        for item in value:
            strings.extend(_walk_strings(item))
        return strings
    if isinstance(value, dict):
        strings = []
        for item in value.values():
            strings.extend(_walk_strings(item))
        return strings
    return []


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _number(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def main() -> int:
    failures = verify()
    print_failures_or_success(failures, SUCCESS_MESSAGE)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
