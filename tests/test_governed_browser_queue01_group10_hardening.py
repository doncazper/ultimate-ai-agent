from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from tests.test_governed_browser_queue01_group10 import (
    _exact,
    _financial_context,
    _service,
)
from ultimate_ai_agent.core.governed_browser import GovernedFinancialOperation


def _raising_clock() -> datetime:
    raise RuntimeError("unavailable")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("amount_minor_units", "1250"),
        ("amount_minor_units", 1250.0),
        ("amount_minor_units", None),
        ("amount_minor_units", True),
        ("spend_limit_minor_units", "1500"),
        ("spend_limit_minor_units", 1500.0),
        ("spend_limit_minor_units", None),
        ("spend_limit_minor_units", False),
    ],
)
def test_malformed_monetary_amounts_fail_with_governed_validation(
    field: str,
    value: object,
) -> None:
    with pytest.raises(ValueError, match="GOVERNED_FINANCIAL_AMOUNT_INVALID"):
        _financial_context(
            operation=GovernedFinancialOperation.purchase,
            suffix=f"malformed-{field}",
            **{field: value},
        )


@pytest.mark.parametrize(
    ("clock", "reason_ref"),
    [
        (_raising_clock, "reason-ref:governed-financial:trusted-clock-failed"),
        (
            lambda: datetime(2026, 7, 18, 12, 0, 0),
            "reason-ref:governed-financial:trusted-clock-invalid",
        ),
    ],
)
def test_invalid_clock_is_content_free_preflight_denial(
    tmp_path: Path,
    clock,
    reason_ref: str,
) -> None:  # type: ignore[no-untyped-def]
    request, recipe, registry = _financial_context(
        operation=GovernedFinancialOperation.checkout_payment,
        suffix=reason_ref.rsplit(":", 1)[-1],
    )
    service, _ = _service(
        tmp_path,
        request=request,
        registry=registry,
        clock=clock,
    )

    result = service.prepare(_exact(request, recipe))

    assert result.receipt.status == "preflight_blocked"
    assert result.receipt.reason_refs == [reason_ref]
    assert result.receipt.content_free is True
    assert result.receipt.financial_effect_performed is False
    assert result.contract is None


def test_receipt_and_ledger_never_record_target_or_payment_material(
    tmp_path: Path,
) -> None:
    secret_marker = "private-financial-target-marker"
    request, recipe, registry = _financial_context(
        operation=GovernedFinancialOperation.purchase,
        suffix="redaction",
        target_descriptor_ref=f"financial-target-descriptor-ref:{secret_marker}",
    )
    service, _ = _service(tmp_path, request=request, registry=registry)

    result = service.prepare(_exact(request, recipe))

    serialized = json.dumps(result.model_dump(mode="json"), sort_keys=True)
    ledger = (tmp_path / "transactions.sqlite3").read_bytes()
    assert secret_marker not in serialized
    assert secret_marker.encode() not in ledger
    assert request.binding.origin.encode() not in ledger
    assert result.receipt.raw_payment_data_recorded is False
    assert result.receipt.payment_handle_resolved is False
    assert result.receipt.checkout_opened is False
    assert result.receipt.financial_effect_performed is False
    assert result.receipt.network_call_performed is False
    assert result.receipt.external_mutation_performed is False
