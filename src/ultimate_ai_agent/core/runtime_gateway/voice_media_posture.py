from __future__ import annotations

import hashlib
import json
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.execution.validation import (
    validate_execution_ref,
    validate_safe_execution_text,
)
from ultimate_ai_agent.core.runtime_gateway.contracts import GOVERNED_RUNTIME_REDACTIONS
from ultimate_ai_agent.core.runtime_gateway.delegation import (
    RUNTIME_DELEGATION_CONTROL_CENTER_REF,
)


RUNTIME_VOICE_MEDIA_POSTURE_CONTRACT_REF = (
    "contract-ref:hermes-runtime-adoption-voice-media-posture:v1"
)
RUNTIME_VOICE_MEDIA_POSTURE_CLI_REF = "uaa runtime inspect-voice-media-posture"
RUNTIME_VOICE_MEDIA_POSTURE_DOC_REF = (
    "docs/runtime/UAA_HERMES_RUNTIME_VOICE_MEDIA_POSTURE.md"
)
RUNTIME_VOICE_MEDIA_POSTURE_SNAPSHOT_REF = (
    "voice-media-posture-snapshot-ref:runtime:phase-41"
)
RUNTIME_VOICE_MEDIA_POSTURE_PROOF_REF = (
    "proof-ref:hermes-runtime-adoption:phase-41:voice-media-posture"
)
RUNTIME_VOICE_MEDIA_POSTURE_VERIFIER_REF = (
    "verifier-ref:hermes-runtime-adoption:phase-41:voice-media-posture"
)

RUNTIME_VOICE_MEDIA_POSTURE_BLOCKED_AUTHORITY_REFS: tuple[str, ...] = (
    "blocked-authority:voice-media-no-microphone-access",
    "blocked-authority:voice-media-no-camera-access",
    "blocked-authority:voice-media-no-file-upload",
    "blocked-authority:voice-media-no-transcription",
    "blocked-authority:voice-media-no-media-generation",
    "blocked-authority:voice-media-no-provider-call",
    "blocked-authority:voice-media-no-external-delivery",
    "blocked-authority:voice-media-no-raw-media-persistence",
    "blocked-authority:voice-media-no-control-center-authority-mint",
)


class RuntimeVoiceMediaLaneKind(str, Enum):
    voice_input = "voice_input"
    speech_to_text = "speech_to_text"
    text_to_speech = "text_to_speech"
    image_input = "image_input"
    image_generation = "image_generation"
    media_upload = "media_upload"
    media_delivery = "media_delivery"


class RuntimeVoiceMediaLaneStatus(str, Enum):
    posture_only = "posture_only"
    blocked_until_authority = "blocked_until_authority"


class RuntimeVoiceMediaLane(BaseModel):
    lane_ref: str
    lane_kind: RuntimeVoiceMediaLaneKind
    display_label: str
    status: RuntimeVoiceMediaLaneStatus
    safe_summary: str
    device_permission_ref: str
    consent_ref: str
    redaction_policy_ref: str
    receipt_plan_ref: str
    safe_disable_ref: str
    proof_ref: str
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    local_only_option_required: bool = True
    provider_boundary_required: bool = True
    consent_required: bool = True
    receipt_required: bool = True
    safe_disable_required: bool = True
    microphone_access_enabled: bool = False
    camera_access_enabled: bool = False
    file_upload_enabled: bool = False
    transcription_enabled: bool = False
    media_generation_enabled: bool = False
    provider_calls_enabled: bool = False
    external_delivery_enabled: bool = False
    raw_media_persisted: bool = False
    control_center_mints_authority: bool = False

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_lane(self) -> "RuntimeVoiceMediaLane":
        for value, field_name in [
            (self.lane_ref, "lane_ref"),
            (self.device_permission_ref, "device_permission_ref"),
            (self.consent_ref, "consent_ref"),
            (self.redaction_policy_ref, "redaction_policy_ref"),
            (self.receipt_plan_ref, "receipt_plan_ref"),
            (self.safe_disable_ref, "safe_disable_ref"),
            (self.proof_ref, "proof_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for field_name in (
            "blocked_authority_refs",
            "promotion_path_refs",
            "next_safe_action_refs",
        ):
            for value in getattr(self, field_name):
                validate_execution_ref(value, field_name)
        for value, field_name in [
            (str(self.lane_kind), "lane_kind"),
            (self.display_label, "display_label"),
            (str(self.status), "status"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        denied_flags = {
            "microphone_access_enabled": self.microphone_access_enabled,
            "camera_access_enabled": self.camera_access_enabled,
            "file_upload_enabled": self.file_upload_enabled,
            "transcription_enabled": self.transcription_enabled,
            "media_generation_enabled": self.media_generation_enabled,
            "provider_calls_enabled": self.provider_calls_enabled,
            "external_delivery_enabled": self.external_delivery_enabled,
            "raw_media_persisted": self.raw_media_persisted,
            "control_center_mints_authority": self.control_center_mints_authority,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_VOICE_MEDIA_LANE_AUTHORITY_DENIED: " + ", ".join(enabled)
            )
        required_flags = {
            "local_only_option_required": self.local_only_option_required,
            "provider_boundary_required": self.provider_boundary_required,
            "consent_required": self.consent_required,
            "receipt_required": self.receipt_required,
            "safe_disable_required": self.safe_disable_required,
        }
        missing = [name for name, value in required_flags.items() if not value]
        if missing:
            raise ValueError(
                "RUNTIME_VOICE_MEDIA_LANE_PROMOTION_REQUIREMENTS_MISSING: "
                + ", ".join(missing)
            )
        if not self.blocked_authority_refs:
            raise ValueError("RUNTIME_VOICE_MEDIA_LANE_BLOCKERS_REQUIRED")
        return self


class RuntimeVoiceMediaPostureReadModel(BaseModel):
    schema_version: str = "runtime_voice_media_posture.v1"
    contract_ref: str = RUNTIME_VOICE_MEDIA_POSTURE_CONTRACT_REF
    status: str = "read_model_posture_only"
    snapshot_ref: str = RUNTIME_VOICE_MEDIA_POSTURE_SNAPSHOT_REF
    snapshot_hash_ref: str = "snapshot-hash-ref:voice-media-posture:pending"
    cli_ref: str = RUNTIME_VOICE_MEDIA_POSTURE_CLI_REF
    doc_ref: str = RUNTIME_VOICE_MEDIA_POSTURE_DOC_REF
    control_center_ref: str = RUNTIME_DELEGATION_CONTROL_CENTER_REF
    safe_summary: str = (
        "Voice, image, TTS, and media lanes are visible as blocked posture only; "
        "no microphone, camera, upload, transcription, generation, provider, or "
        "external delivery authority is granted."
    )
    lanes: list[RuntimeVoiceMediaLane] = Field(default_factory=list)
    lane_count: int = 0
    blocked_lane_count: int = 0
    local_only_option_required: bool = True
    provider_boundary_required: bool = True
    consent_required: bool = True
    receipt_required: bool = True
    safe_disable_required: bool = True
    microphone_access_enabled: bool = False
    camera_access_enabled: bool = False
    file_upload_enabled: bool = False
    transcription_enabled: bool = False
    media_generation_enabled: bool = False
    provider_calls_enabled: bool = False
    external_delivery_enabled: bool = False
    raw_media_persisted: bool = False
    control_center_mints_authority: bool = False
    blocked_authority_refs: list[str] = Field(default_factory=list)
    promotion_path_refs: list[str] = Field(default_factory=list)
    proof_refs: list[str] = Field(default_factory=list)
    verifier_refs: list[str] = Field(default_factory=list)
    next_safe_action_refs: list[str] = Field(default_factory=list)
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(GOVERNED_RUNTIME_REDACTIONS)
        + [
            "raw_media_omitted",
            "device_identifiers_omitted",
            "provider_payloads_omitted",
        ]
    )

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def validate_read_model(self) -> "RuntimeVoiceMediaPostureReadModel":
        for value, field_name in [
            (self.contract_ref, "contract_ref"),
            (self.snapshot_ref, "snapshot_ref"),
            (self.snapshot_hash_ref, "snapshot_hash_ref"),
            (self.control_center_ref, "control_center_ref"),
        ]:
            validate_execution_ref(value, field_name)
        for value, field_name in [
            (self.schema_version, "schema_version"),
            (self.status, "status"),
            (self.cli_ref, "cli_ref"),
            (self.doc_ref, "doc_ref"),
            (self.safe_summary, "safe_summary"),
        ]:
            validate_safe_execution_text(value, field_name)
        for field_name in (
            "blocked_authority_refs",
            "promotion_path_refs",
            "proof_refs",
            "verifier_refs",
            "next_safe_action_refs",
        ):
            for value in getattr(self, field_name):
                validate_execution_ref(value, field_name)
        for value in self.redactions_applied:
            validate_safe_execution_text(value, "redactions_applied")
        denied_flags = {
            "microphone_access_enabled": self.microphone_access_enabled,
            "camera_access_enabled": self.camera_access_enabled,
            "file_upload_enabled": self.file_upload_enabled,
            "transcription_enabled": self.transcription_enabled,
            "media_generation_enabled": self.media_generation_enabled,
            "provider_calls_enabled": self.provider_calls_enabled,
            "external_delivery_enabled": self.external_delivery_enabled,
            "raw_media_persisted": self.raw_media_persisted,
            "control_center_mints_authority": self.control_center_mints_authority,
        }
        enabled = [name for name, value in denied_flags.items() if value]
        if enabled:
            raise ValueError(
                "RUNTIME_VOICE_MEDIA_READ_MODEL_AUTHORITY_DENIED: "
                + ", ".join(enabled)
            )
        required_flags = {
            "local_only_option_required": self.local_only_option_required,
            "provider_boundary_required": self.provider_boundary_required,
            "consent_required": self.consent_required,
            "receipt_required": self.receipt_required,
            "safe_disable_required": self.safe_disable_required,
        }
        missing = [name for name, value in required_flags.items() if not value]
        if missing:
            raise ValueError(
                "RUNTIME_VOICE_MEDIA_PROMOTION_REQUIREMENTS_MISSING: "
                + ", ".join(missing)
            )
        if set(RUNTIME_VOICE_MEDIA_POSTURE_BLOCKED_AUTHORITY_REFS) - set(
            self.blocked_authority_refs
        ):
            raise ValueError("RUNTIME_VOICE_MEDIA_BLOCKERS_REQUIRED")
        if self.lane_count != len(self.lanes):
            raise ValueError("RUNTIME_VOICE_MEDIA_COUNT_MISMATCH")
        if self.blocked_lane_count != len(
            [
                lane
                for lane in self.lanes
                if lane.status == RuntimeVoiceMediaLaneStatus.blocked_until_authority
            ]
        ):
            raise ValueError("RUNTIME_VOICE_MEDIA_BLOCKED_COUNT_MISMATCH")
        return self


def _lane(
    lane_kind: RuntimeVoiceMediaLaneKind,
    display_label: str,
    summary: str,
) -> RuntimeVoiceMediaLane:
    token = lane_kind.value.replace("_", "-")
    return RuntimeVoiceMediaLane(
        lane_ref=f"voice-media-lane-ref:runtime:{token}",
        lane_kind=lane_kind,
        display_label=display_label,
        status=RuntimeVoiceMediaLaneStatus.blocked_until_authority,
        safe_summary=summary,
        device_permission_ref=f"device-permission-ref:voice-media:{token}",
        consent_ref=f"consent-ref:voice-media:{token}",
        redaction_policy_ref=f"redaction-policy-ref:voice-media:{token}",
        receipt_plan_ref=f"receipt-plan-ref:voice-media:{token}",
        safe_disable_ref=f"safe-disable-ref:voice-media:{token}",
        proof_ref=f"proof-ref:voice-media:{token}",
        blocked_authority_refs=list(RUNTIME_VOICE_MEDIA_POSTURE_BLOCKED_AUTHORITY_REFS),
        promotion_path_refs=[
            f"promotion-path-ref:voice-media:{token}:device-permission",
            f"promotion-path-ref:voice-media:{token}:redaction-receipt",
            f"promotion-path-ref:voice-media:{token}:safe-disable",
        ],
        next_safe_action_refs=[
            f"next-safe-action-ref:voice-media:{token}:promotion-contract"
        ],
    )


def build_runtime_voice_media_posture_read_model() -> (
    RuntimeVoiceMediaPostureReadModel
):
    lanes = [
        _lane(
            RuntimeVoiceMediaLaneKind.voice_input,
            "Voice input",
            "Microphone capture remains blocked until device permission, consent, "
            "redaction, receipt, and safe-disable are proven.",
        ),
        _lane(
            RuntimeVoiceMediaLaneKind.speech_to_text,
            "Speech to text",
            "Transcription remains blocked until local/provider boundary, consent, "
            "redaction, and receipt requirements are proven.",
        ),
        _lane(
            RuntimeVoiceMediaLaneKind.text_to_speech,
            "Text to speech",
            "TTS generation remains blocked until provider boundary, consent, "
            "delivery, and receipt requirements are proven.",
        ),
        _lane(
            RuntimeVoiceMediaLaneKind.image_input,
            "Image input",
            "Camera and image intake remain blocked until consent, redaction, "
            "safe refs, and retention posture are proven.",
        ),
        _lane(
            RuntimeVoiceMediaLaneKind.image_generation,
            "Image generation",
            "Image generation remains blocked until provider boundary, content "
            "policy, receipt, and safe-disable posture are proven.",
        ),
        _lane(
            RuntimeVoiceMediaLaneKind.media_upload,
            "Media upload",
            "Media upload remains blocked until file boundary, redaction, "
            "retention, and external delivery posture are proven.",
        ),
        _lane(
            RuntimeVoiceMediaLaneKind.media_delivery,
            "External media delivery",
            "Sending or publishing generated media remains blocked until exact "
            "connector authority, receipt, revoke, and proof are proven.",
        ),
    ]
    payload = {
        "lanes": lanes,
        "lane_count": len(lanes),
        "blocked_lane_count": len(lanes),
        "blocked_authority_refs": list(RUNTIME_VOICE_MEDIA_POSTURE_BLOCKED_AUTHORITY_REFS),
        "promotion_path_refs": [
            "promotion-path-ref:voice-media:device-permission",
            "promotion-path-ref:voice-media:local-only-option",
            "promotion-path-ref:voice-media:provider-boundary",
            "promotion-path-ref:voice-media:consent-receipt",
            "promotion-path-ref:voice-media:redaction-verifier",
            "promotion-path-ref:voice-media:safe-disable",
        ],
        "proof_refs": [RUNTIME_VOICE_MEDIA_POSTURE_PROOF_REF],
        "verifier_refs": [RUNTIME_VOICE_MEDIA_POSTURE_VERIFIER_REF],
        "next_safe_action_refs": [
            "next-safe-action-ref:voice-media:read-model-ui-labels",
            "next-safe-action-ref:voice-media:device-permission-contract",
        ],
    }
    snapshot_material = {
        "contract_ref": RUNTIME_VOICE_MEDIA_POSTURE_CONTRACT_REF,
        "cli_ref": RUNTIME_VOICE_MEDIA_POSTURE_CLI_REF,
        "lane_refs": [lane.lane_ref for lane in lanes],
        "blocked_authority_refs": payload["blocked_authority_refs"],
    }
    payload["snapshot_hash_ref"] = (
        "snapshot-hash-ref:voice-media-posture:"
        + hashlib.sha256(
            json.dumps(snapshot_material, sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
    )
    return RuntimeVoiceMediaPostureReadModel(**payload)
