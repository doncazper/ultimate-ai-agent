from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from scripts.verify_social_read_only_foundation_profile import (
    LEDGER_PATH,
    verify,
)
from ultimate_ai_agent.api.app import app
from ultimate_ai_agent.core.crm import (
    CRM_SOCIAL_RELATIONSHIP_API_REF,
    CRM_SOCIAL_RELATIONSHIP_CLI_REF,
    CRM_SOCIAL_RELATIONSHIP_PROJECTION_CONTRACT_REF,
    CrmLocalCommandCenterReadModel,
    CrmLocalStore,
    build_crm_social_relationship_projection,
)


ROOT = Path(__file__).resolve().parents[1]


def test_crm_social_projection_is_owner_backed_and_read_only(tmp_path: Path) -> None:
    crm = CrmLocalStore(tmp_path / "crm").read_model()
    projection = crm.social_relationship_projection

    assert projection.contract_ref == CRM_SOCIAL_RELATIONSHIP_PROJECTION_CONTRACT_REF
    assert projection.api_ref == CRM_SOCIAL_RELATIONSHIP_API_REF
    assert projection.cli_ref == CRM_SOCIAL_RELATIONSHIP_CLI_REF
    assert projection.backend_owned is True
    assert projection.read_only is True
    assert projection.stable_deep_links is True
    assert projection.copies_relationship_truth is False
    assert projection.live_source_access_enabled is False
    assert projection.connector_runtime_enabled is False
    assert projection.provider_model_call_enabled is False
    assert projection.publishing_enabled is False
    assert projection.external_write_enabled is False
    assert projection.production_authority_enabled is False
    assert len(projection.items) == 1

    item = projection.items[0]
    assert item.relationship_ref == "relationship-ref:crm-local:alpha"
    assert item.person_ref == "person-ref:crm-local:relationship-alpha"
    assert item.crm_deep_link_ref.startswith("control-center-deep-link-ref:crm:")
    assert item.backend_owned is True
    assert item.read_only is True
    assert item.raw_content_included is False
    assert item.connector_runtime_enabled is False
    assert item.external_action_enabled is False


def test_crm_social_projection_rejects_broken_owner_links(tmp_path: Path) -> None:
    crm = CrmLocalStore(tmp_path / "crm").read_model()
    payload = crm.model_dump(mode="python")
    payload["social_relationship_projection"]["items"][0]["person_ref"] = (
        "person-ref:crm-local:other"
    )
    with pytest.raises(ValidationError, match="CRM_SOCIAL_PERSON_LINK_MISMATCH"):
        CrmLocalCommandCenterReadModel.model_validate(payload)


def test_crm_social_projection_rejects_cross_person_selection(tmp_path: Path) -> None:
    crm = CrmLocalStore(tmp_path / "crm").read_model()
    tagged_other_person = crm.people[0].model_copy(
        update={
            "person_ref": "person-ref:crm-local:other",
            "tags": ["social-context"],
            "relationship_refs": [crm.relationships[0].relationship_ref],
        }
    )

    with pytest.raises(
        ValueError, match="CRM_SOCIAL_RELATIONSHIP_SELECTOR_OWNER_MISMATCH"
    ):
        build_crm_social_relationship_projection(
            people=[tagged_other_person],
            organizations=crm.organizations,
            relationships=crm.relationships,
        )


def test_crm_social_projection_deep_links_are_collision_resistant(
    tmp_path: Path,
) -> None:
    crm = CrmLocalStore(tmp_path / "crm").read_model()
    common = f"relationship-ref:crm-local:{'a' * 125}"
    refs = [f"{common}-one", f"{common}-two"]
    relationships = [
        crm.relationships[0].model_copy(update={"relationship_ref": relationship_ref})
        for relationship_ref in refs
    ]
    person = crm.people[0].model_copy(
        update={"tags": ["social-context"], "relationship_refs": refs}
    )

    projection = build_crm_social_relationship_projection(
        people=[person],
        organizations=crm.organizations,
        relationships=relationships,
    )

    assert len({item.crm_deep_link_ref for item in projection.items}) == 2


def test_crm_social_projection_rejects_duplicate_canonical_refs(
    tmp_path: Path,
) -> None:
    crm = CrmLocalStore(tmp_path / "crm").read_model()
    duplicate = crm.relationships[0].model_copy(
        update={"safe_summary": "A different safe summary for the duplicate."}
    )

    with pytest.raises(ValueError, match="CRM_SOCIAL_RELATIONSHIP_REF_DUPLICATE"):
        build_crm_social_relationship_projection(
            people=crm.people,
            organizations=crm.organizations,
            relationships=[crm.relationships[0], duplicate, *crm.relationships[1:]],
        )


def test_crm_social_projection_truncates_with_truthful_coverage(
    tmp_path: Path,
) -> None:
    crm = CrmLocalStore(tmp_path / "crm").read_model()
    refs = [f"relationship-ref:crm-local:social-{index:03d}" for index in range(55)]
    relationships = [
        crm.relationships[0].model_copy(update={"relationship_ref": relationship_ref})
        for relationship_ref in refs
    ]
    person = crm.people[0].model_copy(
        update={"tags": ["social-context"], "relationship_refs": refs}
    )

    projection = build_crm_social_relationship_projection(
        people=[person],
        organizations=crm.organizations,
        relationships=relationships,
    )

    assert projection.total_item_count == 55
    assert projection.returned_item_count == 50
    assert len(projection.items) == 50
    assert projection.truncated is True


def test_crm_social_projection_bounds_provenance_with_truthful_counts(
    tmp_path: Path,
) -> None:
    crm = CrmLocalStore(tmp_path / "crm").read_model()
    evidence_refs = [
        f"evidence-ref:crm-local:social-{index:03d}" for index in range(25)
    ]
    memory_refs = [f"memory-ref:crm-local:social-{index:03d}" for index in range(25)]
    relationship = crm.relationships[0].model_copy(
        update={
            "evidence_refs": evidence_refs,
            "memory_provenance_refs": memory_refs,
        }
    )

    projection = build_crm_social_relationship_projection(
        people=crm.people,
        organizations=crm.organizations,
        relationships=[relationship, *crm.relationships[1:]],
    )
    item = projection.items[0]

    assert len(item.evidence_refs) == 20
    assert item.evidence_ref_total_count == 25
    assert item.evidence_refs_truncated is True
    assert len(item.memory_provenance_refs) == 20
    assert item.memory_provenance_ref_total_count == 25
    assert item.memory_provenance_refs_truncated is True


def test_crm_social_projection_rejects_incomplete_serialized_inventory(
    tmp_path: Path,
) -> None:
    crm = CrmLocalStore(tmp_path / "crm").read_model()
    payload = crm.model_dump(mode="python")
    payload["social_relationship_projection"].update(
        {
            "items": [],
            "total_item_count": 0,
            "returned_item_count": 0,
            "truncated": False,
        }
    )

    with pytest.raises(
        ValidationError, match="CRM_SOCIAL_RELATIONSHIP_INVENTORY_DRIFT"
    ):
        CrmLocalCommandCenterReadModel.model_validate(payload)


def test_crm_social_projection_rejects_metadata_and_item_truth_drift(
    tmp_path: Path,
) -> None:
    crm = CrmLocalStore(tmp_path / "crm").read_model()

    metadata_drift = crm.model_dump(mode="python")
    metadata_drift["social_relationship_projection"]["owner_ref"] = "owner-ref:other"
    with pytest.raises(
        ValidationError,
        match="CRM_SOCIAL_RELATIONSHIP_OWNERSHIP_METADATA_DRIFT",
    ):
        CrmLocalCommandCenterReadModel.model_validate(metadata_drift)

    item_drift = crm.model_dump(mode="python")
    item_drift["social_relationship_projection"]["items"][0]["safe_summary"] = (
        "Altered but safe-looking relationship summary."
    )
    with pytest.raises(
        ValidationError,
        match="CRM_SOCIAL_RELATIONSHIP_ITEM_TRUTH_DRIFT",
    ):
        CrmLocalCommandCenterReadModel.model_validate(item_drift)


def test_crm_social_projection_empty_state_is_truthful(tmp_path: Path) -> None:
    crm = CrmLocalStore(tmp_path / "crm").read_model()
    people = [person.model_copy(update={"tags": []}) for person in crm.people]
    projection = build_crm_social_relationship_projection(
        people=people,
        organizations=crm.organizations,
        relationships=crm.relationships,
    )
    assert projection.items == []
    assert projection.backend_owned is True
    assert projection.live_source_access_enabled is False


def test_crm_relationship_api_and_cli_share_social_projection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    state_dir = tmp_path / "crm"
    monkeypatch.setenv("UAA_CRM_STATE_DIR", str(state_dir))
    response = TestClient(app).get("/control-center/crm/relationships")
    assert response.status_code == 200
    api_projection = response.json()["data"]["social_relationship_projection"]
    assert api_projection["contract_ref"] == (
        CRM_SOCIAL_RELATIONSHIP_PROJECTION_CONTRACT_REF
    )
    assert api_projection["items"][0]["relationship_ref"] == (
        "relationship-ref:crm-local:alpha"
    )

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/dev/uaa_crm.py",
            "inspect-social-relationships",
            "--state-dir",
            str(state_dir),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == api_projection


def test_social_foundation_promotion_ledger_is_exact_and_fail_closed() -> None:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    failures, state = verify(ledger)
    assert failures == []
    assert state == "IMPLEMENTATION_EVIDENCE_VERIFIED_PROMOTION_PENDING"
    assert ledger["external_human_identity_authority_configured"] is False
    assert ledger["promotion_status"] == "pending_independent_review"
    assert {item["decision"] for item in ledger["reviewers"]} == {"pending"}


def test_social_foundation_verifier_rejects_tamper_and_self_promotion() -> None:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))

    tampered = json.loads(json.dumps(ledger))
    tampered["subject_files"][0]["sha256"] = f"sha256:{'0' * 64}"
    failures, state = verify(tampered)
    assert state == "INVALID"
    assert "subject file manifest does not match" in " ".join(failures)

    self_promoted = json.loads(json.dumps(ledger))
    self_promoted["reviewers"][0].update(
        {
            "decision": "accepted",
            "reviewer_ref": "reviewer-ref:social-foundation:self",
            "acceptance_subject_digest": ledger["acceptance_subject_digest"],
            "receipt_ref": "receipt-ref:social-foundation:self",
        }
    )
    failures, state = verify(self_promoted)
    assert state == "INVALID"
    assert "cannot be self-asserted" in " ".join(failures)

    secret_like = json.loads(json.dumps(ledger))
    secret_like["candidate_author_ref"] = "author-ref:ghp_abcdef123456"
    failures, state = verify(secret_like)
    assert state == "INVALID"
    assert failures

    swapped_owners = json.loads(json.dumps(ledger))
    work_board_paths = swapped_owners["foundations"][0]["path_refs"]
    crm_paths = swapped_owners["foundations"][2]["path_refs"]
    work_board_paths[0], crm_paths[0] = crm_paths[0], work_board_paths[0]
    failures, state = verify(swapped_owners)
    assert state == "INVALID"
    assert "exact path_refs drifted" in " ".join(failures)


def test_social_foundation_verifier_redacts_schema_errors_and_never_crashes() -> None:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    secret_like = "sk_live_do_not_echo_abcdef123456"
    malformed = json.loads(json.dumps(ledger))
    malformed["candidate_author_ref"] = f"author-ref:{secret_like}"
    malformed["foundations"][0]["foundation_ref"] = ["not", "hashable"]
    malformed["foundations"][1]["path_refs"][0] = {"unsafe": "shape"}
    malformed["reviewers"][0]["role_ref"] = {"unsafe": "shape"}

    failures, state = verify(malformed)

    assert state == "INVALID"
    rendered = json.dumps(failures)
    assert secret_like not in rendered
    assert "SCHEMA_VALIDATION_FAILED" in rendered


def test_social_foundation_require_promoted_cli_remains_blocked() -> None:
    default = subprocess.run(
        [sys.executable, "scripts/verify_social_read_only_foundation_profile.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert default.returncode == 0, default.stdout
    assert json.loads(default.stdout)["independent_promotion_verified"] is False

    required = subprocess.run(
        [
            sys.executable,
            "scripts/verify_social_read_only_foundation_profile.py",
            "--require-promoted",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert required.returncode == 2
    assert json.loads(required.stdout)["status"] == (
        "IMPLEMENTATION_EVIDENCE_VERIFIED_PROMOTION_PENDING"
    )
