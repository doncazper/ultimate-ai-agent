"""Governed medical knowledge source metadata.

This package registers sources and policy posture only. It contains no source
content and grants no retrieval, ingestion, diagnosis, prescribing, or model
training authority.
"""

from ultimate_ai_agent.core.medical_knowledge.catalog import (
    MEDICAL_KNOWLEDGE_CONTRACT_REF,
    MedicalKnowledgeCatalog,
    MedicalKnowledgeSource,
    MedicalSourceAccessClass,
    MedicalSourceIntegrationState,
    build_medical_knowledge_catalog,
    get_medical_knowledge_source,
)

__all__ = [
    "MEDICAL_KNOWLEDGE_CONTRACT_REF",
    "MedicalKnowledgeCatalog",
    "MedicalKnowledgeSource",
    "MedicalSourceAccessClass",
    "MedicalSourceIntegrationState",
    "build_medical_knowledge_catalog",
    "get_medical_knowledge_source",
]
