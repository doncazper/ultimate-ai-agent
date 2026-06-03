from ultimate_ai_agent.core.ledger.validation import scan_payload_for_secrets
from ultimate_ai_agent.core.truth.enums import TruthSourceKind
from ultimate_ai_agent.core.truth.enums import ClaimVerificationStatus
from ultimate_ai_agent.core.truth.evidence import EvidenceManifest
from ultimate_ai_agent.core.truth.sources import TruthSourceManifest


RAW_TRUTH_CONTENT_MARKERS = (
    "raw_prompt",
    "raw prompt",
    "raw_model_output",
    "raw model output",
    "raw_file_content",
    "raw file content",
    "raw_transcript",
    "raw transcript",
    "private key",
    "begin private key",
)

SECRET_LIKE_TRUTH_MARKERS = (
    "api_key",
    "apikey",
    "secret",
    "token=",
    "password",
    "authorization",
    "cookie",
)


def validate_no_truth_secret_payload(payload: object) -> bool:
    if scan_payload_for_secrets(payload):
        raise ValueError("Truth/evidence payload contains secret-like content.")
    return True


def assert_no_raw_truth_content(payload: object) -> bool:
    text = str(payload).lower()
    if any(marker in text for marker in RAW_TRUTH_CONTENT_MARKERS):
        raise ValueError("Truth/evidence payload contains raw content.")
    if any(marker in text for marker in SECRET_LIKE_TRUTH_MARKERS):
        raise ValueError("Truth/evidence payload contains secret-like content.")
    if scan_payload_for_secrets(payload):
        raise ValueError("Truth/evidence payload contains secret-like content.")
    return True


def validate_structured_truth_ref(ref: str, field_name: str = "ref") -> bool:
    if ":" not in ref or not ref.split(":", 1)[0] or not ref.split(":", 1)[1]:
        raise ValueError(f"{field_name} must be a structured source_ref.")
    assert_no_raw_truth_content(ref)
    return True


def assert_claim_not_self_verified(evidence_chain) -> bool:
    if evidence_chain.claim_ref in set(evidence_chain.source_refs + evidence_chain.evidence_refs):
        raise ValueError("Claim cannot self-verify.")
    return True


def assert_memory_not_truth(evidence_chain) -> bool:
    refs = set(evidence_chain.source_refs + evidence_chain.evidence_refs + evidence_chain.memory_refs)
    if any(ref.startswith("memory:") or ":memory:" in ref for ref in refs):
        return True
    return True


def assert_model_output_not_truth(evidence_chain) -> bool:
    refs = set(evidence_chain.source_refs + evidence_chain.evidence_refs)
    blocked_prefixes = ("model:", "runtime:", "openwebui:", "model_output:", "runtime_output:", "openwebui_output:")
    if any(ref.startswith(blocked_prefixes) for ref in refs):
        return True
    return True


def assert_no_external_verification(
    *,
    external_verification_enabled: bool,
    web_search_enabled: bool,
    model_verification_enabled: bool,
) -> bool:
    if external_verification_enabled:
        raise ValueError("External verification is blocked in M25.")
    if web_search_enabled:
        raise ValueError("Web search is blocked in M25.")
    if model_verification_enabled:
        raise ValueError("Model verification is blocked in M25.")
    return True


def validate_truth_source_ref(source_ref) -> bool:
    validate_structured_truth_ref(source_ref.source_ref, "source_ref")
    assert_no_raw_truth_content(source_ref.model_dump(mode="json"))
    return True


def validate_evidence_ref(evidence_ref) -> bool:
    validate_structured_truth_ref(evidence_ref.evidence_ref, "evidence_ref")
    validate_structured_truth_ref(evidence_ref.source_ref, "source_ref")
    assert_no_raw_truth_content(evidence_ref.model_dump(mode="json"))
    return True


def validate_claim(claim) -> bool:
    assert_no_raw_truth_content(claim.model_dump(mode="json"))
    return True


def validate_evidence_chain(evidence_chain) -> bool:
    assert_claim_not_self_verified(evidence_chain)
    assert_no_raw_truth_content(evidence_chain.model_dump(mode="json"))
    return True


def validate_verification_request(request) -> bool:
    if request.allow_model_output:
        raise ValueError("allow_model_output must be False.")
    if request.allow_raw_content:
        raise ValueError("allow_raw_content must be False.")
    assert_no_raw_truth_content(request.model_dump(mode="json"))
    return True


def assert_no_truth_memory_write_call(module_source: str) -> bool:
    forbidden = (
        "write_" + "memory(",
        ".write_" + "memory(",
        "put_" + "record(",
        ".put_" + "record(",
    )
    if any(fragment in module_source for fragment in forbidden):
        raise ValueError("Truth module must not write memory.")
    return True


def assert_truth_source_kind_can_verify(kind: TruthSourceKind) -> bool:
    if kind in {
        TruthSourceKind.source_linked_memory,
        TruthSourceKind.reviewed_memory,
        TruthSourceKind.unreviewed_memory,
        TruthSourceKind.model_output,
        TruthSourceKind.runtime_output,
        TruthSourceKind.openwebui_output,
        TruthSourceKind.unknown,
    }:
        raise ValueError("Source kind cannot verify truth.")
    return True


def validate_truth_source_manifest(source: TruthSourceManifest) -> bool:
    validate_no_truth_secret_payload(source.model_dump(mode="json"))
    return True


def validate_evidence_manifest(manifest: EvidenceManifest) -> bool:
    validate_no_truth_secret_payload(manifest.model_dump(mode="json"))

    evidence_ids = {item.evidence_id for item in manifest.evidence_items}
    unsupported_claim_ids = set(manifest.unsupported_claims)
    for claim in manifest.claims:
        if claim.verification_status == ClaimVerificationStatus.supported:
            missing_refs = [ref for ref in claim.evidence_refs if ref not in evidence_ids]
            if missing_refs:
                raise ValueError("supported claim references missing evidence.")
        if claim.verification_status == ClaimVerificationStatus.unsupported and claim.claim_id not in unsupported_claim_ids:
            raise ValueError("unsupported claims must be listed in unsupported_claims.")
    return True
