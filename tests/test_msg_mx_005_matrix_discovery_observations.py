from __future__ import annotations

import os
from datetime import timedelta
from types import SimpleNamespace

import pytest

from ultimate_ai_agent.core.communications.matrix_session.observations import (
    MatrixDiscoveryObservationStore,
)
from ultimate_ai_agent.core.communications.matrix_session import (
    MatrixSessionOperation,
    matrix_session_lane,
)
from ultimate_ai_agent.core.communications.matrix_session.target_policy import (
    matrix_discovery_freshness_ref,
    matrix_homeserver_observation_ref,
    matrix_homeserver_ref,
)
from ultimate_ai_agent.core.time import utc_now


HARNESS_URL = "http://127.0.0.1:18008"
PUBLIC_URL = "https://matrix.example.org"


def _record(
    store: MatrixDiscoveryObservationStore,
    *,
    checked_at=None,
    endpoint_url: str = HARNESS_URL,
    source_url: str | None = None,
    receipt_ref: str = "receipt-ref:matrix-discovery:one",
) -> tuple[str, str, object]:
    observation_ref = matrix_homeserver_observation_ref(endpoint_url)
    freshness_ref = matrix_discovery_freshness_ref(observation_ref)
    observed_at = checked_at or utc_now()
    store.record_success(
        observation_ref=observation_ref,
        freshness_ref=freshness_ref,
        source_discovery_origin_ref=matrix_homeserver_ref(source_url or endpoint_url),
        dispatch_receipt_ref=receipt_ref,
        checked_at=observed_at,
    )
    return observation_ref, freshness_ref, observed_at


def _dispatch_receipt(
    observation_ref: str,
    freshness_ref: str,
    checked_at,
    *,
    receipt_ref: str = "receipt-ref:matrix-discovery:one",
    status: str = "succeeded",
):
    lane = matrix_session_lane(MatrixSessionOperation.discovery_read)
    return SimpleNamespace(
        receipt_ref=receipt_ref,
        status=status,
        adapter_ref=lane.adapter_ref,
        capability_ref=lane.capability_ref,
        created_at=checked_at,
        evidence_refs=[observation_ref, freshness_ref],
        raw_paths_included=False,
        raw_prompt_included=False,
        raw_response_included=False,
        raw_provider_payload_included=False,
    )


def test_observation_store_requires_prior_matching_current_receipt(tmp_path) -> None:
    store = MatrixDiscoveryObservationStore(tmp_path / "observations")
    observation_ref = matrix_homeserver_observation_ref(HARNESS_URL)
    freshness_ref = matrix_discovery_freshness_ref(observation_ref)
    assert store.validate_current(
        observation_ref=observation_ref,
        freshness_ref=freshness_ref,
        endpoint_url=HARNESS_URL,
        dispatch_receipts=[],
    ) == ["reason-ref:matrix-session:discovery-evidence-missing"]

    observation_ref, freshness_ref, checked_at = _record(store)
    receipts = [_dispatch_receipt(observation_ref, freshness_ref, checked_at)]
    assert (
        store.validate_current(
            observation_ref=observation_ref,
            freshness_ref=freshness_ref,
            endpoint_url=HARNESS_URL,
            dispatch_receipts=receipts,
        )
        == []
    )
    assert store.validate_current(
        observation_ref=observation_ref,
        freshness_ref=freshness_ref,
        endpoint_url=PUBLIC_URL,
        dispatch_receipts=receipts,
    ) == ["reason-ref:matrix-session:discovery-target-mismatch"]
    assert store.validate_current(
        observation_ref=observation_ref,
        freshness_ref="freshness-ref:matrix-discovery:forged-current",
        endpoint_url=HARNESS_URL,
        dispatch_receipts=receipts,
    ) == ["reason-ref:matrix-session:discovery-freshness-mismatch"]


def test_expired_observation_fails_closed(tmp_path) -> None:
    store = MatrixDiscoveryObservationStore(tmp_path / "observations")
    observation_ref, freshness_ref, checked_at = _record(
        store,
        checked_at=utc_now() - timedelta(minutes=11),
    )
    assert store.validate_current(
        observation_ref=observation_ref,
        freshness_ref=freshness_ref,
        endpoint_url=HARNESS_URL,
        dispatch_receipts=[
            _dispatch_receipt(observation_ref, freshness_ref, checked_at)
        ],
    ) == ["reason-ref:matrix-session:discovery-stale"]


def test_delegated_target_is_bound_separately_from_discovery_origin(tmp_path) -> None:
    store = MatrixDiscoveryObservationStore(tmp_path / "observations")
    observation_ref, freshness_ref, checked_at = _record(
        store,
        endpoint_url=PUBLIC_URL,
        source_url="https://user-domain.example.org",
    )
    assert (
        store.validate_current(
            observation_ref=observation_ref,
            freshness_ref=freshness_ref,
            endpoint_url=PUBLIC_URL,
            dispatch_receipts=[
                _dispatch_receipt(observation_ref, freshness_ref, checked_at)
            ],
        )
        == []
    )


@pytest.mark.parametrize("status", ("failed", "started"))
def test_nonterminal_or_forged_dispatch_receipt_cannot_authorize_auth_read(
    tmp_path, status: str
) -> None:
    store = MatrixDiscoveryObservationStore(tmp_path / "observations")
    observation_ref, freshness_ref, checked_at = _record(store)
    receipt = _dispatch_receipt(
        observation_ref, freshness_ref, checked_at, status=status
    )
    assert store.validate_current(
        observation_ref=observation_ref,
        freshness_ref=freshness_ref,
        endpoint_url=HARNESS_URL,
        dispatch_receipts=[receipt],
    ) == ["reason-ref:matrix-session:discovery-receipt-invalid"]


def test_receipt_replay_is_idempotent_and_mismatch_fails_closed(tmp_path) -> None:
    store = MatrixDiscoveryObservationStore(tmp_path / "observations")
    checked_at = utc_now()
    first = _record(store, checked_at=checked_at)
    assert _record(store, checked_at=checked_at) == first
    with pytest.raises(ValueError, match="MATRIX_DISCOVERY_RECEIPT_REPLAY_MISMATCH"):
        _record(
            store,
            checked_at=checked_at,
            endpoint_url=PUBLIC_URL,
        )


def test_discovery_capacity_preflight_compacts_expired_observations(
    tmp_path, monkeypatch
) -> None:
    import ultimate_ai_agent.core.communications.matrix_session.observations as module

    monkeypatch.setattr(module, "MATRIX_DISCOVERY_LEDGER_MAX_RECORDS", 2)
    store = MatrixDiscoveryObservationStore(tmp_path / "observations")
    _record(
        store,
        checked_at=utc_now() - timedelta(minutes=11),
        endpoint_url="https://expired.example.org",
        receipt_ref="receipt-ref:matrix-discovery:expired",
    )
    _record(
        store,
        endpoint_url="https://current-one.example.org",
        receipt_ref="receipt-ref:matrix-discovery:current-one",
    )
    assert store.prepare_for_discovery() == []
    _record(
        store,
        endpoint_url="https://current-two.example.org",
        receipt_ref="receipt-ref:matrix-discovery:current-two",
    )
    assert store.prepare_for_discovery() == []
    _record(
        store,
        endpoint_url="https://current-three.example.org",
        receipt_ref="receipt-ref:matrix-discovery:current-three",
    )
    assert store.prepare_for_discovery() == []
    assert (
        len(
            (tmp_path / "observations" / "matrix_discovery_observations.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        )
        == 2
    )


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO unavailable")
def test_observation_ledger_rejects_fifo_substitution(tmp_path) -> None:
    state_dir = tmp_path / "observations"
    state_dir.mkdir()
    os.mkfifo(state_dir / "matrix_discovery_observations.jsonl")
    store = MatrixDiscoveryObservationStore(state_dir)
    with pytest.raises(
        ValueError, match="MATRIX_DISCOVERY_LEDGER_(OPEN_FAILED|UNSAFE)"
    ):
        _record(store)
