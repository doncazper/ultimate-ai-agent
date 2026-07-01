import pytest

from ultimate_ai_agent.core.agent_runtime import (
    AgentRuntimeImportedVendorTrace,
    AgentRuntimeReceiptPlan,
    AgentRuntimeTraceEvent,
    AgentRuntimeTraceSpan,
    AgentRuntimeTraceStatus,
)


def test_trace_span_is_uaa_canonical_and_safe_ref_only() -> None:
    event = AgentRuntimeTraceEvent(
        event_ref="agent-runtime-event:test",
        trace_ref="agent-runtime-trace:test",
        safe_summary="Policy checked safe refs.",
        status=AgentRuntimeTraceStatus.no_effect_completed,
        policy_status_ref="policy-status-ref:agent-runtime:test",
        approval_status_ref="approval-status-ref:agent-runtime:test",
        blocked_authority_refs=["blocked-authority-ref:no-provider-runtime"],
    )
    span = AgentRuntimeTraceSpan(
        trace_ref="agent-runtime-trace:test",
        span_ref="agent-runtime-span:test",
        capability_ref="cap:agent-runtime:test",
        safe_summary="UAA canonical trace for a contract-only runtime adapter.",
        result_status=AgentRuntimeTraceStatus.no_effect_completed,
        policy_status_ref="policy-status-ref:agent-runtime:test",
        approval_status_ref="approval-status-ref:agent-runtime:test",
        events=[event],
        evidence_refs=["evidence-ref:agent-runtime:test"],
        receipt_refs=["receipt-ref:agent-runtime:test"],
        blocked_authority_refs=["blocked-authority-ref:no-provider-runtime"],
    )

    assert span.uaa_canonical is True
    assert span.events[0].event_ref == "agent-runtime-event:test"


def test_trace_span_requires_blocked_authority_refs_and_uaa_canonical_status() -> None:
    with pytest.raises(ValueError, match="AGENT_RUNTIME_BLOCKED_AUTHORITY_REFS_REQUIRED"):
        AgentRuntimeTraceSpan(
            trace_ref="agent-runtime-trace:test",
            span_ref="agent-runtime-span:test",
            capability_ref="cap:agent-runtime:test",
            safe_summary="Missing blocked authority refs.",
            policy_status_ref="policy-status-ref:agent-runtime:test",
            approval_status_ref="approval-status-ref:agent-runtime:test",
        )

    with pytest.raises(ValueError, match="AGENT_RUNTIME_UAA_TRACE_CANONICAL_REQUIRED"):
        AgentRuntimeTraceSpan(
            trace_ref="agent-runtime-trace:test",
            span_ref="agent-runtime-span:test",
            capability_ref="cap:agent-runtime:test",
            safe_summary="Non-canonical trace.",
            policy_status_ref="policy-status-ref:agent-runtime:test",
            approval_status_ref="approval-status-ref:agent-runtime:test",
            blocked_authority_refs=["blocked-authority-ref:no-provider-runtime"],
            uaa_canonical=False,
        )


def test_imported_vendor_trace_is_evidence_only() -> None:
    trace = AgentRuntimeImportedVendorTrace(
        import_ref="agent-runtime-vendor-trace-import:test",
        uaa_trace_ref="agent-runtime-trace:test",
        vendor_trace_ref="vendor-trace-ref:agent-runtime:test",
        safe_summary="Imported vendor trace as subordinate evidence.",
        evidence_refs=["evidence-ref:agent-runtime:test"],
    )

    assert trace.imported_as_evidence_only is True
    assert trace.authority_granted is False

    with pytest.raises(ValueError, match="VENDOR_TRACE_AUTHORITY_DENIED"):
        AgentRuntimeImportedVendorTrace(
            import_ref="agent-runtime-vendor-trace-import:test",
            uaa_trace_ref="agent-runtime-trace:test",
            vendor_trace_ref="vendor-trace-ref:agent-runtime:test",
            safe_summary="Unsafe vendor trace.",
            authority_granted=True,
        )


def test_receipt_plan_keeps_vendor_trace_noncanonical() -> None:
    receipt = AgentRuntimeReceiptPlan(
        receipt_plan_ref="agent-runtime-receipt-plan:test",
        trace_ref="agent-runtime-trace:test",
        safe_summary="UAA receipt plan for contract-only agent runtime.",
        evidence_refs=["evidence-ref:agent-runtime:test"],
        blocked_authority_refs=["blocked-authority-ref:no-execution"],
    )

    assert receipt.uaa_receipt_required is True
    assert receipt.vendor_trace_receipt_is_canonical is False
    assert receipt.execution_performed is False

    with pytest.raises(ValueError, match="AGENT_RUNTIME_RECEIPT_AUTHORITY_DENIED"):
        AgentRuntimeReceiptPlan(
            receipt_plan_ref="agent-runtime-receipt-plan:test",
            trace_ref="agent-runtime-trace:test",
            safe_summary="Unsafe receipt plan.",
            vendor_trace_receipt_is_canonical=True,
        )


def test_trace_contract_rejects_raw_content_markers_in_safe_summary() -> None:
    with pytest.raises(ValueError, match="forbidden raw-content marker"):
        AgentRuntimeTraceEvent(
            event_ref="agent-runtime-event:test",
            trace_ref="agent-runtime-trace:test",
            safe_summary="Contains /Users/example/raw/path",
            policy_status_ref="policy-status-ref:agent-runtime:test",
            approval_status_ref="approval-status-ref:agent-runtime:test",
            blocked_authority_refs=["blocked-authority-ref:no-provider-runtime"],
        )
