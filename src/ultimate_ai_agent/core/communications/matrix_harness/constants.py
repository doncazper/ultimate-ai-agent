from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ultimate_ai_agent.core.authority.authority_constants import (
    MATRIX_HARNESS_FIXTURE_SEED_TOOL_REF,
    MATRIX_HARNESS_INSPECT_TOOL_REF,
    MATRIX_HARNESS_RESET_TOOL_REF,
    MATRIX_HARNESS_SMOKE_TOOL_REF,
    MATRIX_HARNESS_START_TOOL_REF,
    MATRIX_HARNESS_STOP_TOOL_REF,
)
from ultimate_ai_agent.core.authority.contracts import AuthorityCapability


MATRIX_HARNESS_SCHEMA_VERSION = "uaa-matrix-harness.v1"
MATRIX_HARNESS_PROVIDER_REF = "provider-ref:communications:matrix-local-synapse"
MATRIX_HARNESS_TARGET_REF = "target-ref:communications:matrix-harness-loopback"
MATRIX_HARNESS_PROJECT_REF = "project-ref:communications:matrix-harness-v1"
MATRIX_HARNESS_PORT_REF = "port-ref:communications:matrix-harness-18008"
MATRIX_HARNESS_CONFIG_REF = (
    "config-ref:communications:matrix-harness-loopback-sqlite-no-federation-v1"
)
MATRIX_HARNESS_LIMITS_REF = (
    "limits-ref:communications:matrix-harness-30m-1cpu-1g-128pids"
)
MATRIX_HARNESS_FIXTURE_PLAN_REF = (
    "fixture-plan-ref:communications:matrix-harness-synthetic-v1"
)
MATRIX_HARNESS_STATE_SCOPE_REF = (
    "state-scope-ref:communications:matrix-harness-disposable-v1"
)
MATRIX_HARNESS_SAFE_DISABLE_REF = (
    "safe-disable-ref:communications:matrix-harness-local"
)
MATRIX_HARNESS_KILL_SWITCH_REF = "kill-switch-ref:authority-lease-local"
MATRIX_HARNESS_IMAGE = "matrixdotorg/synapse"
MATRIX_HARNESS_IMAGE_TAG = "v1.156.0"
MATRIX_HARNESS_IMAGE_DIGEST = (
    "sha256:d2215c4a0e0bbd304489af228345b31d6857c1a228175471358d3fda187c0d91"
)
MATRIX_HARNESS_IMAGE_REF = f"{MATRIX_HARNESS_IMAGE}@{MATRIX_HARNESS_IMAGE_DIGEST}"
MATRIX_HARNESS_LOOPBACK_HOST = "127.0.0.1"
MATRIX_HARNESS_PORT = 18008
MATRIX_HARNESS_MAX_LIFETIME_SECONDS = 1800


class MatrixHarnessOperation(str, Enum):
    inspect = "inspect"
    smoke = "smoke"
    start = "start"
    fixture_seed = "fixture_seed"
    stop = "stop"
    reset = "reset"


@dataclass(frozen=True)
class MatrixHarnessLane:
    operation: MatrixHarnessOperation
    lane_ref: str
    capability_ref: str
    adapter_ref: str
    tool_ref: str
    tool_name: str
    authority_capability: AuthorityCapability
    approval_required: bool
    side_effect_class: str
    risk: str


def _lane(
    operation: MatrixHarnessOperation,
    *,
    tool_ref: str,
    capability: AuthorityCapability,
    approval_required: bool,
    side_effect_class: str,
    risk: str,
) -> MatrixHarnessLane:
    suffix = operation.value.replace("_", "-")
    return MatrixHarnessLane(
        operation=operation,
        lane_ref=f"authority-lane-ref:matrix-harness-{suffix}",
        capability_ref=f"authority-capability-ref:matrix-harness-{suffix}-v1",
        adapter_ref=f"authority-adapter-ref:matrix-harness-{suffix}-v1",
        tool_ref=tool_ref,
        tool_name=f"matrix_harness_{operation.value}",
        authority_capability=capability,
        approval_required=approval_required,
        side_effect_class=side_effect_class,
        risk=risk,
    )


MATRIX_HARNESS_LANES = {
    MatrixHarnessOperation.inspect: _lane(
        MatrixHarnessOperation.inspect,
        tool_ref=MATRIX_HARNESS_INSPECT_TOOL_REF,
        capability=AuthorityCapability.read,
        approval_required=False,
        side_effect_class="read_only_local",
        risk="low",
    ),
    MatrixHarnessOperation.smoke: _lane(
        MatrixHarnessOperation.smoke,
        tool_ref=MATRIX_HARNESS_SMOKE_TOOL_REF,
        capability=AuthorityCapability.read,
        approval_required=False,
        side_effect_class="governed_network_read_only",
        risk="low",
    ),
    MatrixHarnessOperation.start: _lane(
        MatrixHarnessOperation.start,
        tool_ref=MATRIX_HARNESS_START_TOOL_REF,
        capability=AuthorityCapability.execute,
        approval_required=True,
        side_effect_class="local_dev_workspace_only",
        risk="high",
    ),
    MatrixHarnessOperation.fixture_seed: _lane(
        MatrixHarnessOperation.fixture_seed,
        tool_ref=MATRIX_HARNESS_FIXTURE_SEED_TOOL_REF,
        capability=AuthorityCapability.mutate,
        approval_required=True,
        side_effect_class="local_dev_workspace_only",
        risk="high",
    ),
    MatrixHarnessOperation.stop: _lane(
        MatrixHarnessOperation.stop,
        tool_ref=MATRIX_HARNESS_STOP_TOOL_REF,
        capability=AuthorityCapability.execute,
        approval_required=True,
        side_effect_class="local_dev_workspace_only",
        risk="high",
    ),
    MatrixHarnessOperation.reset: _lane(
        MatrixHarnessOperation.reset,
        tool_ref=MATRIX_HARNESS_RESET_TOOL_REF,
        capability=AuthorityCapability.mutate,
        approval_required=True,
        side_effect_class="local_dev_workspace_only",
        risk="high",
    ),
}


def matrix_harness_lane(operation: MatrixHarnessOperation | str) -> MatrixHarnessLane:
    return MATRIX_HARNESS_LANES[MatrixHarnessOperation(operation)]
