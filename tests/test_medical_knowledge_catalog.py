import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.medical_knowledge import (
    MedicalKnowledgeSource,
    MedicalSourceAccessClass,
    MedicalSourceIntegrationState,
    build_medical_knowledge_catalog,
    get_medical_knowledge_source,
)


EXPECTED_SOURCE_IDS = {
    "who_icd_11",
    "apa_dsm_5_tr",
    "apa_dsm_5_tr_ampd",
    "harrisons_internal_medicine",
    "merck_manual",
    "current_medical_diagnosis_treatment",
    "goodman_gilman_pharmacology",
    "prescribers_digital_reference",
    "stahl_essential_psychopharmacology",
    "nelson_pediatrics",
    "schwartz_surgery",
    "bates_physical_examination",
    "medline_pubmed",
    "pmc_open_access_subset",
    "nlm_dailymed",
}


def test_catalog_registers_every_requested_source_as_metadata_only() -> None:
    catalog = build_medical_knowledge_catalog()

    assert {source.source_id for source in catalog.sources} == EXPECTED_SOURCE_IDS
    assert all(source.registered_as_base_reference for source in catalog.sources)
    assert all(not source.catalog_contains_source_content for source in catalog.sources)


def test_catalog_denies_runtime_training_and_clinical_authority() -> None:
    catalog = build_medical_knowledge_catalog()

    assert catalog.runtime_fetch_enabled is False
    assert catalog.automated_ingestion_enabled is False
    assert catalog.context_injection_enabled is False
    assert catalog.model_weight_training_enabled is False
    assert catalog.clinical_decision_authority_enabled is False
    for source in catalog.sources:
        assert source.runtime_fetch_enabled is False
        assert source.automated_ingestion_enabled is False
        assert source.context_injection_enabled is False
        assert source.model_weight_training_enabled is False
        assert source.diagnosis_authority_enabled is False
        assert source.prescribing_authority_enabled is False
        assert source.source_is_truth_authority is False


def test_proprietary_sources_remain_reference_only_and_rights_gated() -> None:
    proprietary = [
        source
        for source in build_medical_knowledge_catalog().sources
        if source.access_class == MedicalSourceAccessClass.licensed_proprietary.value
    ]

    assert len(proprietary) == 11
    assert all(
        source.integration_state
        == MedicalSourceIntegrationState.registered_reference_only.value
        for source in proprietary
    )
    assert all(
        source.rights_evidence_required_before_content_use for source in proprietary
    )


def test_medline_and_pmc_are_distinct_and_pmc_is_license_filtered() -> None:
    medline = get_medical_knowledge_source("medline_pubmed")
    pmc = get_medical_knowledge_source("pmc_open_access_subset")

    assert medline.domain == "biomedical_bibliography"
    assert "not a blanket grant to article full text" in medline.source_scope
    assert pmc.domain == "biomedical_full_text"
    assert "not all PMC articles" in pmc.source_scope
    assert "article license" in pmc.citation_locator_requirements


def test_catalog_models_fail_closed_if_authority_flag_is_enabled() -> None:
    source = get_medical_knowledge_source("nlm_dailymed")

    with pytest.raises(
        ValidationError, match="MEDICAL_SOURCE_RUNTIME_OR_CLINICAL_AUTHORITY_DENIED"
    ):
        MedicalKnowledgeSource.model_validate(
            {**source.model_dump(mode="python"), "automated_ingestion_enabled": True}
        )

    with pytest.raises(
        ValidationError, match="MEDICAL_SOURCE_RIGHTS_EVIDENCE_GATE_REQUIRED"
    ):
        MedicalKnowledgeSource.model_validate(
            {
                **source.model_dump(mode="python"),
                "rights_evidence_required_before_content_use": False,
            }
        )


def test_unknown_medical_source_is_rejected() -> None:
    with pytest.raises(KeyError, match="UNREGISTERED_MEDICAL_KNOWLEDGE_SOURCE"):
        get_medical_knowledge_source("unregistered_source")
