"""Core/CLI preparation parity before the separately scoped in-app boundary."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.finance.authority import FinanceMutationRequest
from ultimate_ai_agent.core.finance.crypto import InMemoryFinanceCryptoBackend
from ultimate_ai_agent.core.finance.operator_workflow import (
    FinancePreparedMutation,
    confirm_finance_mutation,
    prepare_finance_mutation,
)
from ultimate_ai_agent.core.finance.repository import FinanceRepository
from ultimate_ai_agent.core.finance.service import (
    FinanceKernelService,
    finance_repository_ref,
)


@pytest.fixture
def prepared(tmp_path: Path):
    root = tmp_path / "synthetic-book"
    crypto = InMemoryFinanceCryptoBackend()
    service = FinanceKernelService(FinanceRepository(root, crypto_backend=crypto))
    request = FinanceMutationRequest(
        operation="create",
        repository_ref=finance_repository_ref(root),
        fixture_ref="fixture-ref:finance/FIN-001:balanced-local-book:v1",
        expected_revision=0,
        request_ref="request-ref:finance:operator-create",
        idempotency_ref="idempotency-ref:finance:operator-create",
    )
    bundle = prepare_finance_mutation(service, request)
    return service, crypto, bundle


def _confirm(service, bundle, **overrides):
    return confirm_finance_mutation(
        service,
        bundle,
        **{
            "confirmed": True,
            "actor_ref": "actor-ref:finance:workflow-test-operator",
            "safe_disable_engaged": lambda: False,
            **overrides,
        },
    )


def _assert_no_state(service, crypto):
    assert not service.repository.root.exists()
    assert not (service.repository.root.parent / ".uaa-finance-authority").exists()
    assert crypto._keys == {}


def test_preparation_roundtrip_creates_no_book_key_or_authority(prepared):
    service, crypto, bundle = prepared
    assert bundle.request.approval_ref == bundle.preview.expected_approval_ref
    assert bundle.request.exact_scope_ref == bundle.preview.exact_scope_ref
    assert (
        FinancePreparedMutation.model_validate_json(bundle.model_dump_json()) == bundle
    )
    _assert_no_state(service, crypto)


@pytest.mark.parametrize("confirmed", [False, None, 0, 1, "true"])
def test_only_explicit_boolean_confirmation_can_start(prepared, confirmed):
    service, crypto, bundle = prepared
    with pytest.raises(ValueError, match="OPERATOR_CONFIRMATION_REQUIRED"):
        _confirm(service, bundle, confirmed=confirmed)
    _assert_no_state(service, crypto)


def test_safe_disable_precedes_authority_creation(prepared):
    service, crypto, bundle = prepared
    with pytest.raises(ValueError, match="SAFE_DISABLE_ENGAGED"):
        _confirm(service, bundle, safe_disable_engaged=lambda: True)
    _assert_no_state(service, crypto)


@pytest.mark.parametrize(
    "field", ["request_ref", "idempotency_ref", "expected_revision"]
)
def test_substituted_preparation_cannot_create_authority(prepared, field):
    service, crypto, bundle = prepared
    changed = bundle.request.model_dump(mode="python")
    changed[field] = (
        1 if field == "expected_revision" else f"{field.replace('_', '-')}:substitute"
    )
    if field == "expected_revision":
        with pytest.raises(ValidationError, match="CREATE_REQUEST_SCOPE_INVALID"):
            FinanceMutationRequest.model_validate(changed)
        _assert_no_state(service, crypto)
        return
    request = FinanceMutationRequest.model_validate(changed)
    substituted = FinancePreparedMutation(request=request, preview=bundle.preview)
    with pytest.raises(ValueError, match="PREPARED_BUNDLE_BINDING_INVALID"):
        _confirm(service, substituted)
    _assert_no_state(service, crypto)


def test_foreign_repository_cannot_receive_the_confirmed_change(prepared, tmp_path):
    service, crypto, bundle = prepared
    other = FinanceKernelService(
        FinanceRepository(tmp_path / "another-book", crypto_backend=crypto)
    )
    with pytest.raises(RuntimeError, match="REPOSITORY_REF_PATH_MISMATCH"):
        _confirm(other, bundle)
    _assert_no_state(service, crypto)
    assert not other.repository.root.exists()


@pytest.mark.parametrize(
    "field", ["mutation_performed", "operator_confirmation_required"]
)
def test_serialized_bundle_cannot_change_fixed_posture(prepared, field):
    _service, _crypto, bundle = prepared
    raw = bundle.model_dump(mode="json")
    raw[field] = not raw[field]
    with pytest.raises(ValidationError):
        FinancePreparedMutation.model_validate(raw)


def test_confirmed_create_returns_core_receipt_and_survives_reopen(prepared):
    service, crypto, bundle = prepared
    result = _confirm(service, bundle)
    assert result["receipt"]["phase"] == "committed"
    assert result["receipt"]["operation"] == "create"
    assert result["synthetic_only"] is True
    assert result["real_financial_data_included"] is False
    reopened = FinanceRepository(service.repository.root, crypto_backend=crypto)
    snapshot = reopened.load_snapshot_read_only(
        request_ref="request-ref:finance:operator-reopen"
    )
    assert snapshot.revision == 1
    assert snapshot.review_decisions == ()
    assert str(service.repository.root) not in str(result)
