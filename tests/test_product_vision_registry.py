from __future__ import annotations

import copy
import json

import pytest

from scripts import verify_product_vision_registry as vision


def _payload() -> dict:
    return json.loads(vision.REGISTRY.read_text(encoding="utf-8"))


def _queue_payload() -> dict:
    return json.loads(vision.QUEUE.read_text(encoding="utf-8"))


def _item(payload: dict, item_id: str) -> dict:
    return next(item for item in payload["items"] if item["item_id"] == item_id)


def test_product_vision_registry_passes_current_repository() -> None:
    assert vision.verify() == []


def test_product_vision_registry_requires_every_product_item() -> None:
    payload = copy.deepcopy(_payload())
    payload["items"] = [item for item in payload["items"] if item["item_id"] != "Q30"]

    failures = vision.verify(payload=payload)

    assert "product vision registry item set is incomplete or extra" in failures


def test_product_vision_registry_requires_disposition_for_new_queue_item() -> None:
    queue_payload = copy.deepcopy(_queue_payload())
    new_item = copy.deepcopy(queue_payload["items"][-1])
    new_item["queue_order"] = 37
    new_item["item_id"] = "Q37"
    new_item["slug"] = "new-product"
    queue_payload["items"].append(new_item)

    failures = vision.verify(queue_payload=queue_payload, check_refs=False)

    assert "Queue V2 vision registry dispositions are incomplete or extra" in failures


def test_product_vision_registry_resolves_symbolic_queue_sources() -> None:
    payload = copy.deepcopy(_payload())
    _item(payload, "Q29")["queue_source_refs"] = ["canonical-task-ref:lost-source"]

    failures = vision.verify(payload=payload)

    assert "Q29: symbolic Queue V2 source refs are unresolved" in failures


def test_product_vision_registry_binds_each_symbolic_source_to_documents() -> None:
    payload = copy.deepcopy(_payload())
    queue_payload = copy.deepcopy(_queue_payload())
    _item(payload, "Q29")["queue_source_refs"] = [
        "canonical-task-ref:renamed-source"
    ]
    next(
        item for item in queue_payload["items"] if item["item_id"] == "Q29"
    )["source_refs"] = ["canonical-task-ref:renamed-source"]

    failures = vision.verify(
        payload=payload, queue_payload=queue_payload, check_refs=False
    )

    assert "Q29: queue source binding keys are unresolved" in failures


def test_product_vision_registry_rejects_missing_source_path() -> None:
    payload = copy.deepcopy(_payload())
    _item(payload, "Q28")["canonical_source_paths"][0] = "docs/missing-plan.md"

    failures = vision.verify(payload=payload)

    assert any(
        failure.startswith("Q28: canonical source path is unsafe or missing")
        for failure in failures
    )


@pytest.mark.parametrize(
    "bad_ref",
    ["../private-plan.md", "/private/plan.md", "docs/../private-plan.md"],
)
def test_product_vision_registry_rejects_unsafe_source_path(bad_ref: str) -> None:
    payload = copy.deepcopy(_payload())
    _item(payload, "Q28")["canonical_source_paths"][0] = bad_ref

    failures = vision.verify(payload=payload)

    assert any(
        failure.startswith("Q28: canonical source path is unsafe or missing")
        for failure in failures
    )


def test_product_vision_registry_keeps_slice_and_whole_vision_distinct() -> None:
    payload = copy.deepcopy(_payload())
    q30 = _item(payload, "Q30")
    q30["current_slice"]["outcome"] = q30["whole_vision"]["outcome"]

    failures = vision.verify(payload=payload, check_refs=False)

    assert "Q30: current slice is conflated with whole vision" in failures


def test_product_vision_registry_rejects_unsupported_completion_claim() -> None:
    payload = copy.deepcopy(_payload())
    _item(payload, "Q15")["whole_vision"]["status"] = "complete"

    failures = vision.verify(payload=payload, check_refs=False)

    assert "Q15: whole vision is complete without evidence" in failures


def test_product_vision_registry_rejects_unresolved_completion_evidence() -> None:
    payload = copy.deepcopy(_payload())
    q15 = _item(payload, "Q15")
    q15["whole_vision"]["status"] = "complete"
    q15["whole_vision"]["completion_evidence_refs"] = [
        "evidence-ref:not-accepted"
    ]

    failures = vision.verify(payload=payload, check_refs=False)

    assert "Q15: completion evidence refs are unresolved" in failures


def test_product_vision_registry_requires_archived_provenance_for_recovery() -> None:
    payload = copy.deepcopy(_payload())
    _item(payload, "Q29")["historical_source_refs"] = []

    failures = vision.verify(payload=payload, check_refs=False)

    assert "Q29: recovered vision lacks archived provenance" in failures


def test_product_vision_registry_requires_detailed_recovery_plan() -> None:
    payload = copy.deepcopy(_payload())
    _item(payload, "Q30")["canonical_source_paths"] = [
        "docs/prompts/remaining_queue_recovery/09_cross_platform_social_publishing.md"
    ]

    failures = vision.verify(payload=payload, check_refs=False)

    assert "Q30: recovered vision lacks a detailed plan" in failures


def test_product_vision_registry_detects_queue_source_drift() -> None:
    queue_payload = copy.deepcopy(_queue_payload())
    queue_q31 = next(
        item for item in queue_payload["items"] if item["item_id"] == "Q31"
    )
    queue_q31["source_refs"].append("canonical-task-ref:new-unmapped-source")

    failures = vision.verify(queue_payload=queue_payload, check_refs=False)

    assert "Q31: symbolic Queue V2 source refs are unresolved" in failures
