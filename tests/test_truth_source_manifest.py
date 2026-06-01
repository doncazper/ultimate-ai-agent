import pytest
from pydantic import ValidationError

from ultimate_ai_agent.core.truth import (
    TruthAuthorityLevel,
    TruthSourceManifest,
    TruthSourceType,
    is_source_selectable,
    validate_truth_source_manifest,
)


def test_model_output_cannot_be_authoritative():
    with pytest.raises(ValidationError, match="model_output"):
        TruthSourceManifest(
            source_id="src_model",
            source_type=TruthSourceType.model_output,
            authority_level=TruthAuthorityLevel.authoritative,
            display_name="Model output",
            owner="tests",
            allowed_scopes=["project"],
            allowed_purposes=["answer"],
            data_classification="public",
        )


def test_memory_has_lower_authority_than_canonical():
    canonical = TruthSourceManifest(
        source_id="src_canonical",
        source_type=TruthSourceType.canonical_file,
        authority_level=TruthAuthorityLevel.authoritative,
        display_name="Roadmap",
        owner="tests",
        allowed_scopes=["project"],
        allowed_purposes=["project_truth"],
        data_classification="project_private",
    )
    memory = TruthSourceManifest(
        source_id="src_memory",
        source_type=TruthSourceType.memory,
        authority_level=TruthAuthorityLevel.medium,
        display_name="Memory",
        owner="tests",
        allowed_scopes=["project"],
        allowed_purposes=["project_truth"],
        data_classification="project_private",
        memory_ref="mem_123",
    )

    assert memory.authority_rank < canonical.authority_rank


def test_consent_required_source_without_consent_is_not_selectable():
    source = TruthSourceManifest(
        source_id="src_private",
        source_type=TruthSourceType.approved_document,
        authority_level=TruthAuthorityLevel.high,
        display_name="Private doc",
        owner="tests",
        allowed_scopes=["user"],
        allowed_purposes=["answer"],
        data_classification="user_private",
        access_requires_consent=True,
    )

    assert is_source_selectable(source, consent_refs=[]) is False
    assert is_source_selectable(source, consent_refs=["consent_123"]) is False


def test_secret_like_source_metadata_rejected():
    source = TruthSourceManifest(
        source_id="src_secret",
        source_type=TruthSourceType.approved_document,
        authority_level=TruthAuthorityLevel.high,
        display_name="Doc",
        owner="tests",
        allowed_scopes=["project"],
        allowed_purposes=["answer"],
        data_classification="project_private",
        metadata={"note": "api_key='abcdefghijklmnop'"},
    )

    with pytest.raises(ValueError, match="secret"):
        validate_truth_source_manifest(source)
