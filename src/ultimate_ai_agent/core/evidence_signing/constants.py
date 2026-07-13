from ultimate_ai_agent.core.authority.authority_constants import (
    PORTABLE_EVIDENCE_KEY_CREATE_TOOL_REF,
    PORTABLE_EVIDENCE_KEY_CLEANUP_TOOL_REF,
    PORTABLE_EVIDENCE_KEY_MARK_LOST_TOOL_REF,
    PORTABLE_EVIDENCE_KEY_REVOKE_TOOL_REF,
    PORTABLE_EVIDENCE_KEY_ROTATE_TOOL_REF,
    PORTABLE_EVIDENCE_SIGN_TOOL_REF,
)

__all__ = [
    "PORTABLE_EVIDENCE_KEY_CLEANUP_TOOL_REF",
    "PORTABLE_EVIDENCE_KEY_CREATE_TOOL_REF",
    "PORTABLE_EVIDENCE_KEY_MARK_LOST_TOOL_REF",
    "PORTABLE_EVIDENCE_KEY_REVOKE_TOOL_REF",
    "PORTABLE_EVIDENCE_KEY_ROTATE_TOOL_REF",
    "PORTABLE_EVIDENCE_SIGN_TOOL_REF",
]

PORTABLE_EVIDENCE_SIGN_ADAPTER_REF = "adapter-ref:portable-evidence-sign:v1"
PORTABLE_EVIDENCE_KEY_CREATE_ADAPTER_REF = "adapter-ref:portable-evidence-key-create:v1"
PORTABLE_EVIDENCE_KEY_ROTATE_ADAPTER_REF = "adapter-ref:portable-evidence-key-rotate:v1"
PORTABLE_EVIDENCE_KEY_REVOKE_ADAPTER_REF = "adapter-ref:portable-evidence-key-revoke:v1"
PORTABLE_EVIDENCE_KEY_MARK_LOST_ADAPTER_REF = (
    "adapter-ref:portable-evidence-key-mark-lost:v1"
)
PORTABLE_EVIDENCE_KEY_CLEANUP_ADAPTER_REF = (
    "adapter-ref:portable-evidence-key-material-cleanup:v1"
)

PORTABLE_EVIDENCE_SIGN_CAPABILITY_REF = (
    "authority-capability-ref:portable-evidence-bundle-sign:v1"
)
PORTABLE_EVIDENCE_KEY_CREATE_CAPABILITY_REF = (
    "authority-capability-ref:portable-evidence-key-create:v1"
)
PORTABLE_EVIDENCE_KEY_ROTATE_CAPABILITY_REF = (
    "authority-capability-ref:portable-evidence-key-rotate:v1"
)
PORTABLE_EVIDENCE_KEY_REVOKE_CAPABILITY_REF = (
    "authority-capability-ref:portable-evidence-key-revoke:v1"
)
PORTABLE_EVIDENCE_KEY_MARK_LOST_CAPABILITY_REF = (
    "authority-capability-ref:portable-evidence-key-mark-lost:v1"
)
PORTABLE_EVIDENCE_KEY_CLEANUP_CAPABILITY_REF = (
    "authority-capability-ref:portable-evidence-key-material-cleanup:v1"
)
