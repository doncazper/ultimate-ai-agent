from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.capability_availability import (
    WebHybridAvailabilityReadModel,
    build_web_hybrid_availability_read_model,
)


ROOT = Path(__file__).resolve().parents[4]
CAPABILITY_SURFACE_MANIFEST_PATH = (
    "docs/control_center/capability_surface_manifest.json"
)
CAPABILITY_SURFACE_GENERATED_OVERLAY_PATH = (
    "docs/control_center/capability_surface_generated_overlay.json"
)
CAPABILITY_SURFACE_DOC_PATH = "docs/control_center/CAPABILITY_SURFACE_COVERAGE.md"
ROUTE_STATUS_MANIFEST_PATH = "docs/control_center/route_status_manifest.json"
RELEASE_SURFACE_MANIFEST_PATH = "docs/control_center/release_surface_manifest.json"
CAPABILITY_SURFACE_ROUTE_REF = "GET /control-center/capabilities/surface"
CAPABILITY_SURFACE_CLI_REF = "scripts/dev/uaa_capability_surface.py inspect"
CAPABILITY_SURFACE_READ_MODEL_REF = (
    "read-model-ref:control-center-capability-surface:v1"
)
CAPABILITY_SURFACE_BLOCKED_AUTHORITY_REFS = [
    "blocked-state:capability-surface-no-runtime-authority",
    "blocked-state:capability-surface-no-provider-model-calls",
    "blocked-state:capability-surface-no-web-fetch",
    "blocked-state:capability-surface-no-browser-automation",
    "blocked-state:capability-surface-no-connector-writes",
    "blocked-state:capability-surface-no-shell-subprocess-execution",
    "blocked-state:capability-surface-no-memory-write",
    "blocked-state:capability-surface-no-context-injection",
    "blocked-state:capability-surface-no-production-authority",
]
CAPABILITY_SURFACE_REDACTIONS = [
    "safe_refs_only",
    "bounded_capability_rows_only",
    "raw_manifest_dump_omitted",
    "raw_route_payloads_omitted",
    "raw_logs_prompts_paths_and_provider_payloads_omitted",
]


class CapabilitySurfaceApiRouteProjection(BaseModel):
    method: str = Field(..., min_length=1)
    path: str = Field(..., min_length=1)
    operation_id: str = Field(..., min_length=1)
    route_ref: str = Field(..., min_length=1)
    side_effect_class: str = Field(..., min_length=1)
    route_classification: str = Field(..., min_length=1)
    approval_posture: str = Field(..., min_length=1)
    source_truth_status: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")


class CapabilitySurfaceUiRouteProjection(BaseModel):
    path: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    release_status: str = Field(..., min_length=1)
    ui_status: str = Field(..., min_length=1)
    source_truth_status: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")


class CapabilitySurfaceActionProjection(BaseModel):
    action_id: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    release_status: str = Field(..., min_length=1)
    side_effect_class: str = Field(..., min_length=1)
    risk_class: str = Field(..., min_length=1)
    source_truth_status: str = Field(..., min_length=1)

    model_config = ConfigDict(extra="forbid")


class CapabilitySurfaceRow(BaseModel):
    capability_id: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    authority_posture: str = Field(..., min_length=1)
    missing_reason: str = Field(..., min_length=1)
    python_core_owner: str = Field(..., min_length=1)
    source_truth_status: str = Field(..., min_length=1)
    api_routes: list[CapabilitySurfaceApiRouteProjection] = Field(default_factory=list)
    ui_routes: list[CapabilitySurfaceUiRouteProjection] = Field(default_factory=list)
    control_action_ids: list[CapabilitySurfaceActionProjection] = Field(
        default_factory=list
    )
    cli_paths: list[str] = Field(default_factory=list)
    tests_evidence_refs: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def keep_row_operator_bounded(self) -> "CapabilitySurfaceRow":
        if self.status == "ui_api_cli_wired" and self.missing_reason != "none":
            raise ValueError("CAPABILITY_SURFACE_WIRED_ROW_MUST_HAVE_NO_MISSING_REASON")
        if self.status != "ui_api_cli_wired" and self.missing_reason == "none":
            raise ValueError(
                "CAPABILITY_SURFACE_GAPPED_ROW_MUST_EXPLAIN_MISSING_REASON"
            )
        return self


class CapabilitySurfaceSummary(BaseModel):
    capability_count: int
    api_route_count: int
    ui_route_count: int
    visible_action_count: int
    covered_release_route_count: int
    covered_visible_action_count: int
    missing_release_routes: list[str] = Field(default_factory=list)
    missing_visible_actions: list[str] = Field(default_factory=list)
    status_counts: dict[str, int] = Field(default_factory=dict)
    authority_posture_counts: dict[str, int] = Field(default_factory=dict)
    source_truth_status_counts: dict[str, int] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class ControlCenterCapabilitySurfaceReadModel(BaseModel):
    schema_version: str = "control-center-capability-surface-read-model.v1"
    read_model_ref: str = CAPABILITY_SURFACE_READ_MODEL_REF
    source: str = "python_core_control_center_capability_surface_read_model"
    backend_owned: bool = True
    read_only: bool = True
    safe_refs_only: bool = True
    raw_manifest_dump_included: bool = False
    runtime_authority_added: bool = False
    public_beta_claim_enabled: bool = False
    production_readiness_claim_enabled: bool = False
    route_ref: str = CAPABILITY_SURFACE_ROUTE_REF
    cli_ref: str = CAPABILITY_SURFACE_CLI_REF
    manifest_ref: str = CAPABILITY_SURFACE_MANIFEST_PATH
    generated_overlay_ref: str = CAPABILITY_SURFACE_GENERATED_OVERLAY_PATH
    doc_ref: str = CAPABILITY_SURFACE_DOC_PATH
    route_status_manifest_ref: str = ROUTE_STATUS_MANIFEST_PATH
    release_surface_manifest_ref: str = RELEASE_SURFACE_MANIFEST_PATH
    api_manifest_ref: str = "/api/manifest"
    safe_summary: str
    summary: CapabilitySurfaceSummary
    rows: list[CapabilitySurfaceRow]
    web_hybrid: WebHybridAvailabilityReadModel
    blocked_authority_refs: list[str] = Field(
        default_factory=lambda: list(CAPABILITY_SURFACE_BLOCKED_AUTHORITY_REFS)
    )
    redactions_applied: list[str] = Field(
        default_factory=lambda: list(CAPABILITY_SURFACE_REDACTIONS)
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def deny_authority_claims(self) -> "ControlCenterCapabilitySurfaceReadModel":
        if self.runtime_authority_added:
            raise ValueError("CAPABILITY_SURFACE_RUNTIME_AUTHORITY_NOT_ALLOWED")
        if self.public_beta_claim_enabled:
            raise ValueError("CAPABILITY_SURFACE_PUBLIC_BETA_CLAIM_NOT_ALLOWED")
        if self.production_readiness_claim_enabled:
            raise ValueError("CAPABILITY_SURFACE_PRODUCTION_CLAIM_NOT_ALLOWED")
        if self.raw_manifest_dump_included:
            raise ValueError("CAPABILITY_SURFACE_RAW_MANIFEST_DUMP_NOT_ALLOWED")
        return self


def build_control_center_capability_surface_read_model(
    *,
    root: Path = ROOT,
    live_api_routes: Iterable[Any],
) -> ControlCenterCapabilitySurfaceReadModel:
    manifest = _load_json(root, CAPABILITY_SURFACE_MANIFEST_PATH)
    overlay = _load_json(root, CAPABILITY_SURFACE_GENERATED_OVERLAY_PATH)
    overlay_by_capability = {
        str(row.get("capability_id")): row
        for row in overlay.get("capabilities", [])
        if isinstance(row, dict)
    }
    live_routes = {
        (str(getattr(route, "method", "")), str(getattr(route, "path", ""))): route
        for route in live_api_routes
    }
    rows = [
        _build_row(capability, overlay_by_capability, live_routes)
        for capability in sorted(
            manifest.get("capabilities", []),
            key=lambda item: str(item.get("capability_id", "")),
        )
        if isinstance(capability, dict)
    ]
    summary = _build_summary(rows, overlay.get("source_truth_counts", {}))
    return ControlCenterCapabilitySurfaceReadModel(
        safe_summary=(
            "Read-only Control Center capability coverage from the human "
            "capability manifest, generated source-truth overlay, and live API "
            "manifest metadata. This view adds no runtime authority."
        ),
        summary=summary,
        rows=rows,
        web_hybrid=build_web_hybrid_availability_read_model(),
    )


def _build_row(
    capability: dict[str, Any],
    overlay_by_capability: dict[str, dict[str, Any]],
    live_routes: dict[tuple[str, str], Any],
) -> CapabilitySurfaceRow:
    capability_id = str(capability.get("capability_id", "unknown-capability"))
    overlay = overlay_by_capability.get(capability_id, {})
    return CapabilitySurfaceRow(
        capability_id=capability_id,
        label=str(capability.get("label", capability_id)),
        status=str(capability.get("status", "unknown")),
        authority_posture=str(capability.get("authority_posture", "unknown")),
        missing_reason=str(capability.get("missing_reason", "unknown")),
        python_core_owner=str(capability.get("python_core_owner", "unknown")),
        source_truth_status=str(overlay.get("source_truth_status", "source_truth_gap")),
        api_routes=[
            _api_route_projection(route, live_routes)
            for route in overlay.get("api_routes", [])
            if isinstance(route, dict)
        ],
        ui_routes=[
            CapabilitySurfaceUiRouteProjection(
                path=str(route.get("path", "")),
                label=str(route.get("label", "")),
                release_status=str(route.get("release_status", "")),
                ui_status=str(route.get("ui_status", "")),
                source_truth_status=str(route.get("source_truth_status", "")),
            )
            for route in overlay.get("ui_routes", [])
            if isinstance(route, dict)
        ],
        control_action_ids=[
            CapabilitySurfaceActionProjection(
                action_id=str(action.get("action_id", "")),
                source=str(action.get("source", "")),
                release_status=str(action.get("release_status", "")),
                side_effect_class=str(action.get("side_effect_class", "")),
                risk_class=str(action.get("risk_class", "")),
                source_truth_status=str(action.get("source_truth_status", "")),
            )
            for action in overlay.get("control_action_ids", [])
            if isinstance(action, dict)
        ],
        cli_paths=sorted(str(path) for path in capability.get("cli_paths", [])),
        tests_evidence_refs=sorted(
            str(ref) for ref in capability.get("tests_evidence_refs", [])
        ),
    )


def _api_route_projection(
    route: dict[str, Any],
    live_routes: dict[tuple[str, str], Any],
) -> CapabilitySurfaceApiRouteProjection:
    method = str(route.get("method", "")).upper()
    path = str(route.get("path", ""))
    live_route = live_routes.get((method, path))
    operation_id = str(route.get("operation_id", ""))
    side_effect_class = str(route.get("side_effect_class", ""))
    route_classification = str(route.get("route_classification", ""))
    approval_posture = str(route.get("approval_posture", ""))
    source_truth_status = str(route.get("source_truth_status", ""))
    if live_route is not None:
        operation_id = str(getattr(live_route, "operation_id", operation_id))
        side_effect_class = _enum_value(
            getattr(live_route, "side_effect_class", side_effect_class)
        )
        route_classification = _enum_value(
            getattr(live_route, "route_classification", route_classification)
        )
        approval_posture = _enum_value(
            getattr(live_route, "approval_posture", approval_posture)
        )
        source_truth_status = "current"
    return CapabilitySurfaceApiRouteProjection(
        method=method,
        path=path,
        operation_id=operation_id,
        route_ref=f"{method} {path}",
        side_effect_class=side_effect_class,
        route_classification=route_classification,
        approval_posture=approval_posture,
        source_truth_status=source_truth_status,
    )


def _build_summary(
    rows: list[CapabilitySurfaceRow],
    source_truth_counts: dict[str, Any],
) -> CapabilitySurfaceSummary:
    status_counts = Counter(row.status for row in rows)
    authority_counts = Counter(row.authority_posture for row in rows)
    source_truth_status_counts = Counter(row.source_truth_status for row in rows)
    return CapabilitySurfaceSummary(
        capability_count=len(rows),
        api_route_count=sum(len(row.api_routes) for row in rows),
        ui_route_count=int(source_truth_counts.get("release_surface_route_count", 0)),
        visible_action_count=int(source_truth_counts.get("visible_action_count", 0)),
        covered_release_route_count=int(
            source_truth_counts.get("covered_release_route_count", 0)
        ),
        covered_visible_action_count=int(
            source_truth_counts.get("covered_visible_action_count", 0)
        ),
        missing_release_routes=list(
            source_truth_counts.get("missing_release_routes", [])
        ),
        missing_visible_actions=list(
            source_truth_counts.get("missing_visible_actions", [])
        ),
        status_counts=dict(sorted(status_counts.items())),
        authority_posture_counts=dict(sorted(authority_counts.items())),
        source_truth_status_counts=dict(sorted(source_truth_status_counts.items())),
    )


def _load_json(root: Path, rel_path: str) -> Any:
    import json

    return json.loads((root / rel_path).read_text(encoding="utf-8"))


def _enum_value(value: Any) -> str:
    candidate = getattr(value, "value", value)
    return str(candidate)
