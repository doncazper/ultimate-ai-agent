import { describe, expect, it } from "vitest";
import { mockControlCenterData } from "../mocks/controlCenterData";
import { normalizeMacOSSetupAssistant } from "./macosSetupAssistant";

const LIFECYCLE_STATES = [
  "prerequisites",
  "ready_to_install",
  "approval_required",
  "installing",
  "installed",
  "starting",
  "healthy",
  "degraded",
  "repairable",
  "stopping",
  "rollback_required",
  "rolled_back",
  "failed",
];
const LIFECYCLE_OPERATIONS = [
  "plan",
  "status",
  "install",
  "verify",
  "repair",
  "stop",
  "rollback",
  "receipts",
] as const;

function lifecycleOperationPayload(
  operation: (typeof LIFECYCLE_OPERATIONS)[number],
  overrides: Record<string, unknown> = {},
): Record<string, unknown> {
  const readOnly =
    operation === "plan" ||
    operation === "status" ||
    operation === "receipts";
  return {
    operation,
    command_ref: `repo-local-command:macos-setup-lifecycle:${operation}`,
    status: readOnly ? "available_read_only" : "blocked_by_authority",
    current_state: "prerequisites",
    target_state: "prerequisites",
    safe_summary: "Bounded setup lifecycle operation.",
    exact_scope_ref: `scope-ref:macos-setup-lifecycle:${operation}`,
    approval_ref: `approval-ref:macos-setup-lifecycle:${operation}`,
    idempotency_key_ref: `idempotency-ref:macos-setup-lifecycle:${operation}`,
    receipt_ref: `receipt-plan:macos-setup-lifecycle:${operation}`,
    rollback_ref: `rollback-plan:macos-setup-lifecycle:${operation}`,
    safe_disable_ref: `safe-disable-ref:macos-setup-lifecycle:${operation}`,
    evidence_refs: ["docs-ref:uaa-setup-assistant-plan"],
    verifier_refs: ["pytest:test-macos-setup-lifecycle"],
    reason_codes: ["MACOS_SETUP_LIFECYCLE_AUTHORITY_NOT_GRANTED"],
    mutation_required: false,
    live_probe_required: false,
    approval_required: !readOnly,
    authority_granted: false,
    state_change_performed: false,
    subprocess_executed: false,
    file_mutation_performed: false,
    process_mutation_performed: false,
    credential_write_performed: false,
    network_request_performed: false,
    receipt_persisted: false,
    ...overrides,
  };
}

function lifecyclePayload(
  overrides: Record<string, unknown> = {},
): Record<string, unknown> {
  return {
    schema_version: "macos_setup_lifecycle.v1",
    contract_ref: "macos-setup-lifecycle-contract:backend-test",
    status: "blocked_by_authority",
    current_state: "prerequisites",
    state_sequence: LIFECYCLE_STATES,
    operations: LIFECYCLE_OPERATIONS.map((operation) =>
      lifecycleOperationPayload(operation),
    ),
    health_contract: {
      contract_ref: "macos-setup-health-contract:backend-test",
      status: "blocked_by_authority",
      required_check_refs: ["health-check-ref:setup-process-identity"],
      safe_summary: "No live setup probe has run.",
      process_identity_verified: false,
      api_manifest_version_verified: false,
      loopback_bind_verified: false,
      control_center_compatibility_verified: false,
      forbidden_authority_absence_verified: false,
      live_probe_performed: false,
    },
    activation_authorized: false,
    installation_performed: false,
    process_launched: false,
    health_probe_performed: false,
    repair_performed: false,
    stop_performed: false,
    rollback_performed: false,
    file_mutation_performed: false,
    credential_write_performed: false,
    subprocess_executed: false,
    live_network_request_performed: false,
    production_authority_enabled: false,
    ...overrides,
  };
}

describe("macOS Setup Assistant normalization provenance", () => {
  it("marks partial backend objects as fallback-derived", () => {
    const normalized = normalizeMacOSSetupAssistant(
      { plan_ref: "setup-plan-ref:partial" },
      mockControlCenterData.macosSetupAssistant,
    );

    expect(normalized.usedFallback).toBe(true);
    expect(normalized.value.steps).toEqual(
      mockControlCenterData.macosSetupAssistant.steps,
    );
  });

  it("marks missing backend payloads as fallback-derived", () => {
    const normalized = normalizeMacOSSetupAssistant(
      undefined,
      mockControlCenterData.macosSetupAssistant,
    );

    expect(normalized.usedFallback).toBe(true);
    expect(normalized.value).toEqual(
      mockControlCenterData.macosSetupAssistant,
    );
  });

  it("normalizes backend lifecycle state and operation proof fields", () => {
    const operations = LIFECYCLE_OPERATIONS.map((operation) =>
      lifecycleOperationPayload(
        operation,
        operation === "install"
          ? {
              target_state: "installed",
              mutation_required: true,
            }
          : {},
      ),
    );
    const normalized = normalizeMacOSSetupAssistant(
      {
        lifecycle: lifecyclePayload({ operations }),
      },
      mockControlCenterData.macosSetupAssistant,
    );

    expect(normalized.usedFallback).toBe(true);
    expect(normalized.value.lifecycle.contractRef).toBe(
      "macos-setup-lifecycle-contract:backend-test",
    );
    expect(normalized.value.lifecycle.stateSequence).toEqual(LIFECYCLE_STATES);
    expect(
      normalized.value.lifecycle.operations.find(
        (operation) => operation.operation === "install",
      ),
    ).toMatchObject({
      operation: "install",
      status: "blocked_by_authority",
      targetState: "installed",
      mutationRequired: true,
      authorityGranted: false,
      stateChangePerformed: false,
    });
    expect(
      normalized.value.lifecycle.healthContract.processIdentityVerified,
    ).toBe(false);
  });

  it("fails closed on tampered lifecycle execution and authority claims", () => {
    const operations = LIFECYCLE_OPERATIONS.map((operation) =>
      lifecycleOperationPayload(
        operation,
        operation === "install"
          ? {
              status: "available_read_only",
              current_state: "healthy",
              authority_granted: true,
              state_change_performed: true,
              subprocess_executed: true,
              file_mutation_performed: true,
              process_mutation_performed: true,
              credential_write_performed: true,
              network_request_performed: true,
              receipt_persisted: true,
            }
          : {},
      ),
    );
    const normalized = normalizeMacOSSetupAssistant(
      {
        lifecycle: lifecyclePayload({
          status: "healthy",
          current_state: "healthy",
          activation_authorized: true,
          installation_performed: true,
          process_launched: true,
          health_probe_performed: true,
          repair_performed: true,
          stop_performed: true,
          rollback_performed: true,
          file_mutation_performed: true,
          credential_write_performed: true,
          subprocess_executed: true,
          live_network_request_performed: true,
          production_authority_enabled: true,
          operations,
          health_contract: {
            status: "healthy",
            process_identity_verified: true,
            api_manifest_version_verified: true,
            loopback_bind_verified: true,
            control_center_compatibility_verified: true,
            forbidden_authority_absence_verified: true,
            live_probe_performed: true,
          },
        }),
      },
      mockControlCenterData.macosSetupAssistant,
    );

    expect(normalized.usedFallback).toBe(true);
    expect(normalized.value.lifecycle).toMatchObject({
      status: "blocked_by_authority",
      currentState: "prerequisites",
      activationAuthorized: false,
      installationPerformed: false,
      processLaunched: false,
      healthProbePerformed: false,
      repairPerformed: false,
      stopPerformed: false,
      rollbackPerformed: false,
      fileMutationPerformed: false,
      credentialWritePerformed: false,
      subprocessExecuted: false,
      liveNetworkRequestPerformed: false,
      productionAuthorityEnabled: false,
    });
    expect(
      normalized.value.lifecycle.operations.find(
        (operation) => operation.operation === "install",
      ),
    ).toMatchObject({
      status: "blocked_by_authority",
      currentState: "prerequisites",
      approvalRequired: true,
      authorityGranted: false,
      stateChangePerformed: false,
      subprocessExecuted: false,
      fileMutationPerformed: false,
      processMutationPerformed: false,
      credentialWritePerformed: false,
      networkRequestPerformed: false,
      receiptPersisted: false,
    });
    expect(normalized.value.lifecycle.healthContract).toMatchObject({
      status: "blocked_by_authority",
      processIdentityVerified: false,
      apiManifestVersionVerified: false,
      loopbackBindVerified: false,
      controlCenterCompatibilityVerified: false,
      forbiddenAuthorityAbsenceVerified: false,
      liveProbePerformed: false,
    });
  });

  it("fails closed on tampered setup diagnostic side-effect claims", () => {
    const normalized = normalizeMacOSSetupAssistant(
      {
        diagnostics: [
          {
            diagnostic_ref: "macos-setup-diagnostic:tampered",
            label: "Tampered diagnostic",
            status: "ready",
            safe_summary: "Untrusted diagnostic payload.",
            source_refs: ["api-surface:control-center-setup-summary"],
            reason_codes: ["MACOS_SETUP_TAMPERED_DIAGNOSTIC"],
            next_safe_action: "inspect-setup-plan",
            read_only: false,
            live_probe_performed: true,
            state_change_performed: true,
          },
        ],
      },
      mockControlCenterData.macosSetupAssistant,
    );

    expect(normalized.usedFallback).toBe(true);
    expect(normalized.value.diagnostics[0]).toMatchObject({
      readOnly: true,
      liveProbePerformed: false,
      stateChangePerformed: false,
    });
  });

  it("fails closed on tampered rollback readiness claims", () => {
    const normalized = normalizeMacOSSetupAssistant(
      {
        rollback_plan: {
          rollback_plan_ref: "macos-setup-rollback-plan:tampered",
          uninstall_ref: "macos-setup-uninstall:tampered",
          safe_summary: "Untrusted rollback payload.",
          rollback_available_after_approval: true,
          rollback_contract_defined: true,
          rollback_execution_available: true,
          rollback_rehearsal_completed: true,
          restore_proof_available: true,
          blocked_reason_refs: ["blocked-ref:macos-setup-rollback-test"],
          next_safe_action: "inspect-setup-plan",
          rollback_executed: true,
        },
      },
      mockControlCenterData.macosSetupAssistant,
    );

    expect(normalized.usedFallback).toBe(true);
    expect(normalized.value.rollbackPlan).toMatchObject({
      rollbackAvailableAfterApproval: false,
      rollbackContractDefined: true,
      rollbackExecutionAvailable: false,
      rollbackRehearsalCompleted: false,
      restoreProofAvailable: false,
      rollbackExecuted: false,
    });
  });

  it.each(["plan", "status", "receipts"] as const)(
    "pins %s lifecycle inspection to passive proof flags",
    (operationName) => {
      const operations = LIFECYCLE_OPERATIONS.map((operation) =>
        lifecycleOperationPayload(
          operation,
          operation === operationName
            ? {
                mutation_required: true,
                live_probe_required: true,
              }
            : {},
        ),
      );
      const normalized = normalizeMacOSSetupAssistant(
        { lifecycle: lifecyclePayload({ operations }) },
        mockControlCenterData.macosSetupAssistant,
      );

      expect(
        normalized.value.lifecycle.operations.find(
          (operation) => operation.operation === operationName,
        ),
      ).toMatchObject({
        status: "available_read_only",
        mutationRequired: false,
        liveProbeRequired: false,
        approvalRequired: false,
      });
      expect(normalized.usedFallback).toBe(true);
    },
  );

  it.each([
    [
      "missing",
      LIFECYCLE_OPERATIONS.slice(0, -1).map((operation) =>
        lifecycleOperationPayload(operation),
      ),
    ],
    [
      "duplicated",
      LIFECYCLE_OPERATIONS.map((operation, index) =>
        lifecycleOperationPayload(index === 1 ? "plan" : operation),
      ),
    ],
    [
      "reordered",
      [
        lifecycleOperationPayload("status"),
        lifecycleOperationPayload("plan"),
        ...LIFECYCLE_OPERATIONS.slice(2).map((operation) =>
          lifecycleOperationPayload(operation),
        ),
      ],
    ],
  ])(
    "falls back to the complete lifecycle operation sequence when %s",
    (_caseName, operations) => {
      const normalized = normalizeMacOSSetupAssistant(
        { lifecycle: lifecyclePayload({ operations }) },
        mockControlCenterData.macosSetupAssistant,
      );

      expect(
        normalized.value.lifecycle.operations.map(
          (operation) => operation.operation,
        ),
      ).toEqual(LIFECYCLE_OPERATIONS);
      expect(normalized.usedFallback).toBe(true);
    },
  );

  it.each([
    ["status", { status: "healthy" }],
    ["current state", { current_state: "healthy" }],
  ])("marks a tampered lifecycle %s as fallback-derived", (_name, override) => {
    const normalized = normalizeMacOSSetupAssistant(
      { lifecycle: lifecyclePayload(override) },
      mockControlCenterData.macosSetupAssistant,
    );

    expect(normalized.usedFallback).toBe(true);
    expect(normalized.value.lifecycle).toMatchObject({
      status: "blocked_by_authority",
      currentState: "prerequisites",
    });
  });
});
