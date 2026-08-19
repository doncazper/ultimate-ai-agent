"""Static, fail-closed catalog of approved medical knowledge source targets."""

from __future__ import annotations

from datetime import date
from enum import Enum
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, model_validator


MEDICAL_KNOWLEDGE_CONTRACT_REF = "contract-ref:medical-knowledge-source-catalog:v1"
MEDICAL_KNOWLEDGE_LAST_REVIEWED_AT = date(2026, 8, 16)

_ALLOWED_OFFICIAL_HOSTS = {
    "accessmedicine.mhmedical.com",
    "dictionary.apa.org",
    "dailymed.nlm.nih.gov",
    "icd.who.int",
    "merckmanuals.com",
    "pmc.ncbi.nlm.nih.gov",
    "pubmed.ncbi.nlm.nih.gov",
    "medicine.lww.com",
    "shop.elsevier.com",
    "www.cambridge.org",
    "www.elsevier.com",
    "www.merckmanuals.com",
    "www.ncbi.nlm.nih.gov",
    "www.nlm.nih.gov",
    "www.pdr.net",
    "www.psychiatry.org",
}


class MedicalSourceAccessClass(str, Enum):
    licensed_proprietary = "licensed_proprietary"
    official_classification_api = "official_classification_api"
    bibliographic_dataset = "bibliographic_dataset"
    license_filtered_open_access_subset = "license_filtered_open_access_subset"
    official_structured_labeling = "official_structured_labeling"


class MedicalSourceIntegrationState(str, Enum):
    registered_reference_only = "registered_reference_only"
    eligible_for_future_governed_adapter = "eligible_for_future_governed_adapter"


class _MedicalKnowledgeModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, use_enum_values=True, hide_input_in_errors=True
    )

    def model_copy(
        self, *, update: dict[str, object] | None = None, deep: bool = False
    ):  # type: ignore[no-untyped-def]
        copied = super().model_copy(update=update, deep=deep)
        return self.__class__.model_validate(copied.model_dump(mode="python"))


class MedicalKnowledgeSource(_MedicalKnowledgeModel):
    source_id: str = Field(..., pattern=r"^[a-z][a-z0-9_]{2,80}$")
    title: str = Field(..., min_length=3, max_length=180)
    publisher: str = Field(..., min_length=2, max_length=120)
    domain: str = Field(..., min_length=3, max_length=80)
    official_url: str
    access_class: MedicalSourceAccessClass
    integration_state: MedicalSourceIntegrationState
    source_scope: str = Field(..., min_length=10, max_length=500)
    license_posture: str = Field(..., min_length=10, max_length=500)
    citation_locator_requirements: tuple[str, ...] = Field(..., min_length=1)
    future_adapter_scope: tuple[str, ...] = Field(default_factory=tuple)
    last_reviewed_at: date = MEDICAL_KNOWLEDGE_LAST_REVIEWED_AT
    registered_as_base_reference: bool = True
    catalog_contains_source_content: bool = False
    rights_evidence_required_before_content_use: bool = True
    runtime_fetch_enabled: bool = False
    automated_ingestion_enabled: bool = False
    context_injection_enabled: bool = False
    model_weight_training_enabled: bool = False
    diagnosis_authority_enabled: bool = False
    prescribing_authority_enabled: bool = False
    source_is_truth_authority: bool = False

    @model_validator(mode="after")
    def validate_fail_closed_source(self) -> "MedicalKnowledgeSource":
        parsed = urlparse(self.official_url)
        if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_OFFICIAL_HOSTS:
            raise ValueError("MEDICAL_SOURCE_OFFICIAL_HTTPS_ALLOWLIST_REQUIRED")
        if not self.registered_as_base_reference:
            raise ValueError("MEDICAL_SOURCE_BASE_REFERENCE_REGISTRATION_REQUIRED")
        denied_flags = (
            self.catalog_contains_source_content,
            self.runtime_fetch_enabled,
            self.automated_ingestion_enabled,
            self.context_injection_enabled,
            self.model_weight_training_enabled,
            self.diagnosis_authority_enabled,
            self.prescribing_authority_enabled,
            self.source_is_truth_authority,
        )
        if any(denied_flags):
            raise ValueError("MEDICAL_SOURCE_RUNTIME_OR_CLINICAL_AUTHORITY_DENIED")
        if not self.rights_evidence_required_before_content_use:
            raise ValueError("MEDICAL_SOURCE_RIGHTS_EVIDENCE_GATE_REQUIRED")
        if not all(locator.strip() for locator in self.citation_locator_requirements):
            raise ValueError("MEDICAL_SOURCE_CITATION_LOCATOR_REQUIRED")
        if (
            self.integration_state
            == MedicalSourceIntegrationState.eligible_for_future_governed_adapter.value
            and not self.future_adapter_scope
        ):
            raise ValueError("MEDICAL_SOURCE_FUTURE_ADAPTER_SCOPE_REQUIRED")
        return self


class MedicalKnowledgeCatalog(_MedicalKnowledgeModel):
    contract_ref: str = MEDICAL_KNOWLEDGE_CONTRACT_REF
    schema_version: str = "medical_knowledge_source_catalog.v1"
    sources: tuple[MedicalKnowledgeSource, ...] = Field(..., min_length=1)
    medical_use_requires_current_citations: bool = True
    medical_use_requires_human_clinical_judgment: bool = True
    contradictory_evidence_must_be_disclosed: bool = True
    emergency_use_claimed: bool = False
    runtime_fetch_enabled: bool = False
    automated_ingestion_enabled: bool = False
    context_injection_enabled: bool = False
    model_weight_training_enabled: bool = False
    clinical_decision_authority_enabled: bool = False

    @model_validator(mode="after")
    def validate_catalog_boundary(self) -> "MedicalKnowledgeCatalog":
        source_ids = [source.source_id for source in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("MEDICAL_SOURCE_ID_MUST_BE_UNIQUE")
        if not (
            self.medical_use_requires_current_citations
            and self.medical_use_requires_human_clinical_judgment
            and self.contradictory_evidence_must_be_disclosed
        ):
            raise ValueError("MEDICAL_KNOWLEDGE_SAFETY_GATES_REQUIRED")
        if any(
            (
                self.emergency_use_claimed,
                self.runtime_fetch_enabled,
                self.automated_ingestion_enabled,
                self.context_injection_enabled,
                self.model_weight_training_enabled,
                self.clinical_decision_authority_enabled,
            )
        ):
            raise ValueError("MEDICAL_KNOWLEDGE_RUNTIME_OR_CLINICAL_AUTHORITY_DENIED")
        return self


def _source(
    source_id: str,
    title: str,
    publisher: str,
    domain: str,
    official_url: str,
    access_class: MedicalSourceAccessClass,
    integration_state: MedicalSourceIntegrationState,
    source_scope: str,
    license_posture: str,
    citation_locator_requirements: list[str],
    future_adapter_scope: list[str] | None = None,
) -> MedicalKnowledgeSource:
    return MedicalKnowledgeSource(
        source_id=source_id,
        title=title,
        publisher=publisher,
        domain=domain,
        official_url=official_url,
        access_class=access_class,
        integration_state=integration_state,
        source_scope=source_scope,
        license_posture=license_posture,
        citation_locator_requirements=citation_locator_requirements,
        future_adapter_scope=future_adapter_scope or [],
    )


def build_medical_knowledge_catalog() -> MedicalKnowledgeCatalog:
    """Return reviewed source metadata without retrieving or embedding content."""

    proprietary = MedicalSourceAccessClass.licensed_proprietary
    reference_only = MedicalSourceIntegrationState.registered_reference_only
    future_adapter = MedicalSourceIntegrationState.eligible_for_future_governed_adapter
    sources = [
        _source(
            "who_icd_11",
            "International Classification of Diseases, Eleventh Revision",
            "World Health Organization",
            "global_diagnostics_and_classification",
            "https://icd.who.int/icdapi",
            MedicalSourceAccessClass.official_classification_api,
            future_adapter,
            "WHO classification metadata and ICD-11 MMS identifiers for morbidity and mortality use.",
            "CC BY-ND 3.0 IGO terms and WHO attribution, versioning, and no-derivatives requirements apply.",
            [
                "release",
                "linearization",
                "code",
                "title",
                "WHO entity URI",
                "retrieval date",
            ],
            ["version_pinned_classification_lookup"],
        ),
        _source(
            "apa_dsm_5_tr",
            "Diagnostic and Statistical Manual of Mental Disorders, Fifth Edition, Text Revision",
            "American Psychiatric Association Publishing",
            "psychiatric_diagnostics",
            "https://www.psychiatry.org/psychiatrists/practice/dsm",
            proprietary,
            reference_only,
            "APA diagnostic manual metadata and licensed diagnostic reference material.",
            "APA content is copyrighted; written permission is required for generative AI or machine-learning use.",
            [
                "edition",
                "update supplement date",
                "section",
                "page or criterion locator",
            ],
        ),
        _source(
            "apa_dsm_5_tr_ampd",
            "DSM-5-TR Alternative Model for Personality Disorders",
            "American Psychiatric Association Publishing",
            "dimensional_personality_assessment",
            "https://www.psychiatry.org/psychiatrists/practice/dsm",
            proprietary,
            reference_only,
            "Section III dimensional framework metadata and separately licensed reference material.",
            "AMPD is part of copyrighted DSM-5-TR material and inherits APA permission requirements.",
            ["edition", "Section III", "model element", "page or criterion locator"],
        ),
        _source(
            "harrisons_internal_medicine",
            "Harrison's Principles of Internal Medicine",
            "McGraw Hill",
            "internal_medicine",
            "https://accessmedicine.mhmedical.com/",
            proprietary,
            reference_only,
            "Licensed internal medicine reference metadata only.",
            "Publisher authorization is required before storing, embedding, ingesting, or training on content.",
            ["edition", "chapter", "section", "page or stable content locator"],
        ),
        _source(
            "merck_manual",
            "The Merck Manual of Diagnosis and Therapy",
            "Merck Manuals",
            "general_clinical_reference",
            "https://www.merckmanuals.com/professional",
            proprietary,
            reference_only,
            "Professional clinical reference metadata only.",
            "Public readability does not establish ingestion or model-training rights; applicable terms require review.",
            [
                "professional edition",
                "topic",
                "review or revision date",
                "stable URL",
                "retrieval date",
            ],
        ),
        _source(
            "current_medical_diagnosis_treatment",
            "Current Medical Diagnosis and Treatment",
            "McGraw Hill",
            "primary_care_and_internal_medicine",
            "https://accessmedicine.mhmedical.com/",
            proprietary,
            reference_only,
            "Annually revised clinical reference metadata only.",
            "Publisher authorization is required before storing, embedding, ingesting, or training on content.",
            ["edition year", "chapter", "section", "page or stable content locator"],
        ),
        _source(
            "goodman_gilman_pharmacology",
            "Goodman & Gilman's The Pharmacological Basis of Therapeutics",
            "McGraw Hill",
            "pharmacology",
            "https://accessmedicine.mhmedical.com/",
            proprietary,
            reference_only,
            "Licensed pharmacology reference metadata only.",
            "Publisher authorization is required before storing, embedding, ingesting, or training on content.",
            [
                "edition",
                "chapter",
                "drug or mechanism section",
                "page or stable content locator",
            ],
        ),
        _source(
            "prescribers_digital_reference",
            "Prescribers' Digital Reference",
            "PDR Network",
            "prescription_drug_labeling_reference",
            "https://www.pdr.net/",
            proprietary,
            reference_only,
            "Commercial drug reference metadata only; official labeling should be cross-checked with DailyMed or FDA records.",
            "PDR terms and publisher authorization must be established before any content use.",
            [
                "drug",
                "label or monograph version",
                "section",
                "revision date",
                "stable URL",
            ],
        ),
        _source(
            "stahl_essential_psychopharmacology",
            "Stahl's Essential Psychopharmacology",
            "Cambridge University Press",
            "psychopharmacology",
            "https://www.cambridge.org/highereducation/books/stahls-essential-psychopharmacology/",
            proprietary,
            reference_only,
            "Licensed psychopharmacology reference metadata only.",
            "Publisher authorization is required before storing, embedding, ingesting, or training on content.",
            ["edition", "chapter", "section", "page or stable content locator"],
        ),
        _source(
            "nelson_pediatrics",
            "Nelson Textbook of Pediatrics",
            "Elsevier",
            "pediatrics",
            "https://shop.elsevier.com/books/nelson-textbook-of-pediatrics-2-volume-set/kliegman/978-0-323-88305-4",
            proprietary,
            reference_only,
            "Licensed pediatric reference metadata only.",
            "Publisher authorization is required before storing, embedding, ingesting, or training on content.",
            ["edition", "chapter", "section", "page or stable content locator"],
        ),
        _source(
            "schwartz_surgery",
            "Schwartz's Principles of Surgery",
            "McGraw Hill",
            "surgery",
            "https://accessmedicine.mhmedical.com/",
            proprietary,
            reference_only,
            "Licensed surgery reference metadata only.",
            "Publisher authorization is required before storing, embedding, ingesting, or training on content.",
            ["edition", "chapter", "section", "page or stable content locator"],
        ),
        _source(
            "bates_physical_examination",
            "Bates' Guide to Physical Examination and History Taking",
            "Wolters Kluwer",
            "physical_examination_and_history",
            "https://medicine.lww.com/Book/Show/1093100",
            proprietary,
            reference_only,
            "Licensed clinical examination reference metadata only.",
            "Publisher authorization and an authoritative publisher endpoint must be verified before content use.",
            ["edition", "chapter", "section", "page or stable content locator"],
        ),
        _source(
            "medline_pubmed",
            "MEDLINE and PubMed Citation Data",
            "U.S. National Library of Medicine",
            "biomedical_bibliography",
            "https://pubmed.ncbi.nlm.nih.gov/",
            MedicalSourceAccessClass.bibliographic_dataset,
            future_adapter,
            "Citation, abstract, indexing, publication-type, and MeSH metadata; not a blanket grant to article full text.",
            "NLM data terms, attribution, currentness disclosure, and third-party abstract copyright must be enforced.",
            [
                "PMID",
                "title",
                "journal",
                "publication date",
                "authors",
                "retrieval date",
            ],
            ["citation_metadata_search", "versioned_medline_dataset_import"],
        ),
        _source(
            "pmc_open_access_subset",
            "PubMed Central Open Access Subset",
            "U.S. National Library of Medicine",
            "biomedical_full_text",
            "https://pmc.ncbi.nlm.nih.gov/tools/openftlist/",
            MedicalSourceAccessClass.license_filtered_open_access_subset,
            future_adapter,
            "Only the PMC Open Access Subset through NLM-approved automated retrieval services; not all PMC articles.",
            "Each article license controls reuse; automated retrieval must use approved PMC dataset services and revocations must be honored.",
            [
                "PMCID",
                "PMID or DOI when present",
                "article license",
                "version",
                "retrieval date",
            ],
            ["per_item_license_filtered_full_text_import"],
        ),
        _source(
            "nlm_dailymed",
            "DailyMed Structured Product Labeling",
            "U.S. National Library of Medicine",
            "drug_labeling",
            "https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm",
            MedicalSourceAccessClass.official_structured_labeling,
            future_adapter,
            "Current structured labeling submitted to FDA by companies and published by NLM, including version history.",
            "NLM terms and label-specific provenance apply; current labeling must be checked at use time.",
            [
                "SET ID",
                "SPL version",
                "published date",
                "label status",
                "retrieval date",
            ],
            ["versioned_structured_product_label_import"],
        ),
    ]
    return MedicalKnowledgeCatalog(sources=sources)


def get_medical_knowledge_source(source_id: str) -> MedicalKnowledgeSource:
    """Look up static source metadata; raise for unregistered sources."""

    for source in build_medical_knowledge_catalog().sources:
        if source.source_id == source_id:
            return source
    raise KeyError(f"UNREGISTERED_MEDICAL_KNOWLEDGE_SOURCE:{source_id}")
