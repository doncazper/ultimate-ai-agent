#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.runtime_gateway import (  # noqa: E402
    RUNTIME_VOICE_MEDIA_POSTURE_AUTHORITY_MAPPING_REF,
    RUNTIME_VOICE_MEDIA_POSTURE_BLOCKED_AUTHORITY_REFS,
    build_runtime_voice_media_posture_read_model,
)

DOC = ROOT / "docs/runtime/UAA_HERMES_RUNTIME_VOICE_MEDIA_POSTURE.md"
CORE = ROOT / "src/ultimate_ai_agent/core/runtime_gateway/voice_media_posture.py"
CLI = ROOT / "scripts/dev/uaa_runtime.py"
TEST = ROOT / "tests/test_hermes_runtime_voice_media_posture.py"
PRODUCT_TRUTH = ROOT / "docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md"
DOC_INDEX = ROOT / "docs/DOCUMENTATION_INDEX.md"


def main() -> int:
    failures: list[str] = []
    read_model = build_runtime_voice_media_posture_read_model()

    if read_model.status != "read_model_posture_only":
        failures.append("voice/media status is not posture-only")
    if read_model.route_ref != "GET /api/runtime/voice-media-posture":
        failures.append("voice/media route ref drifted")
    if read_model.cli_ref != "uaa runtime inspect-voice-media-posture":
        failures.append("voice/media CLI ref drifted")
    if (
        read_model.authority_state_mapping_ref
        != RUNTIME_VOICE_MEDIA_POSTURE_AUTHORITY_MAPPING_REF
    ):
        failures.append("voice/media AuthorityState mapping drifted")
    if read_model.authority_state_decision_outcome != "allow":
        failures.append("voice/media AuthorityState decision is not allow")
    if (
        "reason-ref:authority:active-lease-grants-domain-capability"
        not in read_model.authority_state_reason_refs
    ):
        failures.append("voice/media AuthorityState reason missing active lease")
    if "adapter-ref:voice-media-microphone:not-implemented" not in (
        read_model.unsupported_adapter_refs
    ):
        failures.append("voice/media unsupported adapter refs missing microphone")
    if read_model.lane_count != 7:
        failures.append("voice/media lane count drifted")
    if read_model.blocked_lane_count != read_model.lane_count:
        failures.append("not every voice/media lane is blocked")

    denied_flags = {
        "microphone": read_model.microphone_access_enabled,
        "camera": read_model.camera_access_enabled,
        "upload": read_model.file_upload_enabled,
        "transcription": read_model.transcription_enabled,
        "generation": read_model.media_generation_enabled,
        "provider": read_model.provider_calls_enabled,
        "delivery": read_model.external_delivery_enabled,
        "raw media": read_model.raw_media_persisted,
        "control center authority": read_model.control_center_mints_authority,
    }
    for label, enabled in denied_flags.items():
        if enabled:
            failures.append(f"{label} unexpectedly enabled")

    missing_blocked = set(RUNTIME_VOICE_MEDIA_POSTURE_BLOCKED_AUTHORITY_REFS) - set(
        read_model.blocked_authority_refs
    )
    if missing_blocked:
        failures.append(f"missing blocked authority refs: {sorted(missing_blocked)}")

    for lane in read_model.lanes:
        if lane.status != "blocked_until_authority":
            failures.append(f"lane not blocked: {lane.lane_ref}")
        lane_denied = [
            lane.microphone_access_enabled,
            lane.camera_access_enabled,
            lane.file_upload_enabled,
            lane.transcription_enabled,
            lane.media_generation_enabled,
            lane.provider_calls_enabled,
            lane.external_delivery_enabled,
            lane.raw_media_persisted,
            lane.control_center_mints_authority,
        ]
        if any(lane_denied):
            failures.append(f"lane grants authority: {lane.lane_ref}")
        if not (
            lane.local_only_option_required
            and lane.provider_boundary_required
            and lane.consent_required
            and lane.receipt_required
            and lane.safe_disable_required
        ):
            failures.append(f"lane missing promotion requirements: {lane.lane_ref}")

    for path in [DOC, CORE, CLI, TEST, PRODUCT_TRUTH, DOC_INDEX]:
        if not path.exists():
            failures.append(f"missing {path.relative_to(ROOT)}")

    doc_text = DOC.read_text(encoding="utf-8")
    for expected in [
        "Full-Strength",
        "Repo-Safe",
        "Blocked / Needs Authority",
        "AuthorityState",
        "Exact Authority Path",
        "microphone access",
        "camera access",
        "file or media upload",
        "provider calls",
        "Planning text and read-model visibility do not grant",
    ]:
        if expected not in doc_text:
            failures.append(f"doc missing {expected}")

    cli_text = CLI.read_text(encoding="utf-8")
    for expected in [
        "inspect-voice-media-posture",
        "runtime_voice_media_posture",
        "authority_state_mapping_ref",
        "authority_state_decision_outcome",
        "microphone_access_performed",
        "media_generation_performed",
        "provider_call_performed",
    ]:
        if expected not in cli_text:
            failures.append(f"CLI missing {expected}")

    product_truth = PRODUCT_TRUTH.read_text(encoding="utf-8")
    for expected in [
        "Hermes Runtime Adoption Phase 41",
        "UAA_HERMES_RUNTIME_VOICE_MEDIA_POSTURE.md",
        "voice_media_posture.py",
        "inspect-voice-media-posture",
    ]:
        if expected not in product_truth:
            failures.append(f"product truth missing {expected}")

    if "Hermes runtime voice media posture" not in DOC_INDEX.read_text(
        encoding="utf-8"
    ):
        failures.append("documentation index missing voice/media entry")

    cli_result = subprocess.run(
        [sys.executable, str(CLI), "inspect-voice-media-posture", "--json"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if cli_result.returncode != 0:
        failures.append("voice/media CLI failed")
    else:
        payload = json.loads(cli_result.stdout)
        if payload["microphone_access_performed"] is not False:
            failures.append("CLI claims microphone access")
        if payload["media_generation_performed"] is not False:
            failures.append("CLI claims media generation")
        if payload["provider_call_performed"] is not False:
            failures.append("CLI claims provider calls")
        if (
            payload["runtime_voice_media_posture"]["authority_state_mapping_ref"]
            != RUNTIME_VOICE_MEDIA_POSTURE_AUTHORITY_MAPPING_REF
        ):
            failures.append("CLI returned stale AuthorityState mapping")
        if (
            payload["runtime_voice_media_posture"]["authority_state_decision_outcome"]
            != "allow"
        ):
            failures.append("CLI returned stale AuthorityState decision")
        if payload["runtime_voice_media_posture"]["lane_count"] != 7:
            failures.append("CLI returned stale lane count")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Hermes Runtime Adoption Phase 41 voice/media posture verifier passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
