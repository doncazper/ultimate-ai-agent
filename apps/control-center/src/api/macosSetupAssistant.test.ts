import { describe, expect, it } from "vitest";
import { mockControlCenterData } from "../mocks/controlCenterData";
import { buildCompleteMacOSSetupPayload } from "../test/macosSetupAssistantFixture";
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

function completeSetupPayload(): Record<string, unknown> {
  return buildCompleteMacOSSetupPayload(
    mockControlCenterData.macosSetupAssistant,
  );
}

describe("macOS Setup Assistant normalization provenance", () => {
  it("accepts the complete bounded backend safety contract", () => {
    const normalized = normalizeMacOSSetupAssistant(
      completeSetupPayload(),
      mockControlCenterData.macosSetupAssistant,
    );

    expect(normalized.usedFallback).toBe(false);
    expect(normalized.value.planRef).toBe(
      mockControlCenterData.macosSetupAssistant.planRef,
    );
    expect(normalized.value.steps).toHaveLength(14);
    expect(normalized.value.approvalEnvelopes).toHaveLength(7);
  });

  it("rejects a top-level Setup status promoted beyond dry run", () => {
    const payload = completeSetupPayload();
    payload.status = "ready";

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

  it("rejects a lifecycle operation rebound to another valid target state", () => {
    const payload = completeSetupPayload();
    const lifecycle = payload.lifecycle as Record<string, unknown>;
    const operations = lifecycle.operations as Array<Record<string, unknown>>;
    const install = operations.find(
      (operation) => operation.operation === "install",
    );
    expect(install).toBeDefined();
    install!.target_state = "healthy";

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

  it("rejects a lifecycle operation rebound to another valid command ref", () => {
    const payload = completeSetupPayload();
    const lifecycle = payload.lifecycle as Record<string, unknown>;
    const operations = lifecycle.operations as Array<Record<string, unknown>>;
    const install = operations.find(
      (operation) => operation.operation === "install",
    );
    expect(install).toBeDefined();
    install!.command_ref = "repo-local-command:macos-setup-lifecycle:status";

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

  it.each([
    ["exact_scope_ref", "scope-ref:macos-setup-lifecycle:stop"],
    ["approval_ref", "approval-ref:macos-setup-lifecycle:stop"],
    [
      "idempotency_key_ref",
      "idempotency-ref:macos-setup-lifecycle:stop",
    ],
    ["receipt_ref", "receipt-plan:macos-setup-lifecycle:stop"],
    ["rollback_ref", "rollback-plan:macos-setup-lifecycle:stop"],
    ["safe_disable_ref", "safe-disable-ref:macos-setup-lifecycle:stop"],
  ])("rejects a rebound lifecycle %s", (field, substitutedRef) => {
    const payload = completeSetupPayload();
    const lifecycle = payload.lifecycle as Record<string, unknown>;
    const operations = lifecycle.operations as Array<Record<string, unknown>>;
    const install = operations.find(
      (operation) => operation.operation === "install",
    );
    expect(install).toBeDefined();
    install![field] = substitutedRef;

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

  it.each([
    ["cli_surface_ref", "repo-local-command:unrelated-surface"],
    ["api_surface_ref", "api-surface:unrelated-summary"],
    ["python_core_service_ref", "python-core-service:unrelated"],
    ["safe_disable_ref", "safe-disable-ref:unrelated:enabled"],
    ["rollback_contract_ref", "rollback-contract-ref:unrelated"],
    ["receipt_contract_ref", "receipt-contract-ref:unrelated"],
  ])("rejects a rebound lifecycle contract %s", (field, substitutedRef) => {
    const payload = completeSetupPayload();
    const lifecycle = payload.lifecycle as Record<string, unknown>;
    lifecycle[field] = substitutedRef;

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

  it("rejects an incomplete lifecycle health-check contract", () => {
    const payload = completeSetupPayload();
    const lifecycle = payload.lifecycle as Record<string, unknown>;
    const healthContract = lifecycle.health_contract as Record<string, unknown>;
    healthContract.required_check_refs = [
      "health-check-ref:setup-process-identity",
    ];

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

  it("rejects a bridge preview enabled by default", () => {
    const payload = completeSetupPayload();
    const bridges = payload.bridge_previews as Array<Record<string, unknown>>;
    bridges[0].enablement_default = "enabled";

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

  it("rejects a bridge preview promoted to ready", () => {
    const payload = completeSetupPayload();
    const bridges = payload.bridge_previews as Array<Record<string, unknown>>;
    bridges[0].status = "ready";

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

  it("rejects a broadened approval scope for a bounded setup step", () => {
    const payload = completeSetupPayload();
    const envelopes = payload.approval_envelopes as Array<
      Record<string, unknown>
    >;
    envelopes[0].requested_scope_refs = [
      "scope-ref:macos-setup-production-authority",
    ];

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

  it("rejects an approval envelope rebound to another valid status", () => {
    const payload = completeSetupPayload();
    const envelopes = payload.approval_envelopes as Array<
      Record<string, unknown>
    >;
    const backgroundService = envelopes.find(
      (envelope) =>
        envelope.setup_step_kind === "background_service_setup_planning",
    );
    expect(backgroundService).toBeDefined();
    backgroundService!.status = "approval_required";

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

  it("rejects an approval envelope action rebound to an executable ref", () => {
    const payload = completeSetupPayload();
    const envelopes = payload.approval_envelopes as Array<
      Record<string, unknown>
    >;
    envelopes[0].operator_next_action = "execute-installer";

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

  it.each(["not_scoped_actions", "blocked_runtime_authority"])(
    "rejects a substituted approval-envelope %s set",
    (field) => {
      const payload = completeSetupPayload();
      const envelopes = payload.approval_envelopes as Array<
        Record<string, unknown>
      >;
      envelopes[0][field] = ["review-only"];

      expect(
        normalizeMacOSSetupAssistant(
          payload,
          mockControlCenterData.macosSetupAssistant,
        ).usedFallback,
      ).toBe(true);
    },
  );

  it("rejects a blocked setup step rebound to ready", () => {
    const payload = completeSetupPayload();
    const steps = payload.steps as Array<Record<string, unknown>>;
    const backgroundService = steps.find(
      (step) => step.kind === "background_service_setup_planning",
    );
    expect(backgroundService).toBeDefined();
    backgroundService!.status = "ready";

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

  it("rejects a non-envelope setup step rebound to ready", () => {
    const payload = completeSetupPayload();
    const steps = payload.steps as Array<Record<string, unknown>>;
    const localModel = steps.find(
      (step) => step.kind === "local_model_readiness",
    );
    expect(localModel).toBeDefined();
    localModel!.status = "ready";

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

  it("rejects an incomplete static setup-step sequence", () => {
    const payload = completeSetupPayload();
    const steps = payload.steps as Array<Record<string, unknown>>;
    payload.steps = steps.filter(
      (step) => step.kind !== "local_model_readiness",
    );

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

  it("rejects a mutating diagnostic next-action substitution", () => {
    const payload = completeSetupPayload();
    const diagnostics = payload.diagnostics as Array<Record<string, unknown>>;
    const nativeApp = diagnostics.find(
      (diagnostic) =>
        diagnostic.diagnostic_ref === "macos-setup-diagnostic:native-app",
    );
    expect(nativeApp).toBeDefined();
    nativeApp!.next_safe_action = "execute-installer";

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

  it("rejects an incomplete static diagnostic sequence", () => {
    const payload = completeSetupPayload();
    const diagnostics = payload.diagnostics as Array<Record<string, unknown>>;
    payload.diagnostics = diagnostics.slice(1);

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

  it.each([
    ["empty", []],
    [
      "incomplete",
      mockControlCenterData.macosSetupAssistant.blockedCapabilities.slice(1),
    ],
    [
      "substituted",
      [
        ...mockControlCenterData.macosSetupAssistant.blockedCapabilities.slice(
          0,
          -1,
        ),
        "macos-setup-broader-authority",
      ],
    ],
  ])("rejects a %s blocked-capability contract", (_name, capabilities) => {
    const payload = completeSetupPayload();
    payload.blocked_capabilities = capabilities;

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

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
    expect(normalized.value).toEqual(
      mockControlCenterData.macosSetupAssistant,
    );
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

  it.each([
    "launch_agent_removed",
    "model_files_removed",
    "config_removed",
  ])("fails closed when rollback claims %s", (unsafeField) => {
    const payload = completeSetupPayload();
    const rollbackPlan = payload.rollback_plan as Record<string, unknown>;
    payload.rollback_plan = {
      ...rollbackPlan,
      launch_agent_removed: false,
      model_files_removed: false,
      config_removed: false,
    };
    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(false);

    payload.rollback_plan = {
      ...(payload.rollback_plan as Record<string, unknown>),
      [unsafeField]: true,
    };

    const normalized = normalizeMacOSSetupAssistant(
      payload,
      mockControlCenterData.macosSetupAssistant,
    );

    expect(normalized.usedFallback).toBe(true);
    expect(normalized.value).toEqual(
      mockControlCenterData.macosSetupAssistant,
    );
  });

  it.each([
    "macos_first",
    "local_first",
    "disabled_by_default",
    "control_center_preview_ready",
  ])("rejects a disabled required posture flag %s", (field) => {
    const payload = completeSetupPayload();
    payload[field] = false;

    const normalized = normalizeMacOSSetupAssistant(
      payload,
      mockControlCenterData.macosSetupAssistant,
    );

    expect(normalized.usedFallback).toBe(true);
    expect(normalized.value).toEqual(
      mockControlCenterData.macosSetupAssistant,
    );
  });

  it.each([
    "native_macos_app_ready",
    "setup_question_assistant_enabled",
    "model_output_authoritative",
    "installer_side_effects_enabled",
  ])("rejects a forbidden top-level authority claim %s", (field) => {
    const payload = completeSetupPayload();
    payload[field] = true;

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ),
    ).toMatchObject({
      usedFallback: true,
      value: mockControlCenterData.macosSetupAssistant,
    });
  });

  it.each([
    ["steps", "state_change_allowed"],
    ["steps", "terminal_command_executed"],
    ["steps", "raw_log_stored"],
    ["model_recommendations", "model_download_performed"],
    ["model_recommendations", "model_call_performed"],
    ["model_recommendations", "raw_local_path_included"],
    ["bridge_previews", "credential_material_stored"],
    ["bridge_previews", "raw_transcript_stored"],
    ["bridge_previews", "connector_write_performed"],
    ["approval_envelopes", "real_execution_requested"],
    ["approval_envelopes", "provider_or_model_call_requested"],
    ["approval_envelopes", "raw_prompt_included"],
  ])(
    "rejects nested forbidden claim %s.%s",
    (collectionName, field) => {
      const payload = completeSetupPayload();
      const collection = payload[collectionName] as Array<
        Record<string, unknown>
      >;
      collection[0][field] = true;

      expect(
        normalizeMacOSSetupAssistant(
          payload,
          mockControlCenterData.macosSetupAssistant,
        ).usedFallback,
      ).toBe(true);
    },
  );

  it("rejects missing approval requirements and forged receipt bindings", () => {
    const payload = completeSetupPayload();
    const envelopes = payload.approval_envelopes as Array<
      Record<string, unknown>
    >;
    envelopes[0].exact_scope_required = false;

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);

    const reboundPayload = completeSetupPayload();
    const reboundEnvelopes = reboundPayload.approval_envelopes as Array<
      Record<string, unknown>
    >;
    reboundEnvelopes[0].expected_receipt_ref =
      "receipt-plan:macos-setup:substituted";

    expect(
      normalizeMacOSSetupAssistant(
        reboundPayload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);

    const unapprovedStepPayload = completeSetupPayload();
    const approvalBoundSteps = unapprovedStepPayload.steps as Array<
      Record<string, unknown>
    >;
    const approvalBoundStep = approvalBoundSteps.find(
      (step) => step.kind === "model_selection",
    );
    expect(approvalBoundStep).toBeDefined();
    approvalBoundStep!.status = "ready";
    approvalBoundStep!.approval_required = false;

    expect(
      normalizeMacOSSetupAssistant(
        unapprovedStepPayload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

  it("rejects model download recommendations without approval", () => {
    const payload = completeSetupPayload();
    const recommendations = payload.model_recommendations as Array<
      Record<string, unknown>
    >;
    recommendations[0].approval_required_before_download = false;

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

  it("rejects bridge previews without approval", () => {
    const payload = completeSetupPayload();
    const bridges = payload.bridge_previews as Array<Record<string, unknown>>;
    bridges[0].approval_required = false;

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

  it("rejects an approval-scoped step without a unique envelope", () => {
    const payload = completeSetupPayload();
    const steps = payload.steps as Array<Record<string, unknown>>;
    const modelSelectionStep = steps.find(
      (step) => step.kind === "model_selection",
    );
    expect(modelSelectionStep).toBeDefined();
    steps.push({
      ...modelSelectionStep,
      step_id: "macos-setup-step:unbound-model-selection",
      status: "ready",
      approval_required: false,
    });

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

  it("rejects process-manager command text in approval envelopes", () => {
    const payload = completeSetupPayload();
    const envelopes = payload.approval_envelopes as Array<
      Record<string, unknown>
    >;
    envelopes[0].safe_summary = ["Run launch", "ctl now"].join("");

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

  it.each([
    "receipt_created",
    "audit_event_created",
    "raw_log_stored",
    "raw_prompt_stored",
    "raw_provider_payload_stored",
    "credential_material_stored",
  ])("rejects receipt-plan write claim %s", (field) => {
    const payload = completeSetupPayload();
    const receiptPlan = payload.receipt_plan as Record<string, unknown>;
    receiptPlan[field] = true;

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
  });

  it.each([
    ["secret-like text", ["token", "abcdefghijklmnop"].join("=")],
    ["terminal control text", "Unsafe\u001bsummary"],
    ["raw local path", "Review /Users/operator/private.log"],
    ["unlisted workspace path", "Review /workspace/operator/private.log"],
    ["unlisted mount path", "Inspect /mnt/data/config.json"],
    ["hyphen-adjacent path", "Review-/Users/operator/private.log"],
    ["underscore-adjacent path", "Review_/Library/LaunchAgents/example.plist"],
    ["period-adjacent path", "Review./workspace/operator/private.log"],
    ["punctuated raw local path", "Path:/Users/operator/private.log"],
    ["repeated-slash raw local path", "Review //Users/operator/private.log"],
    ["file URL raw local path", "Review file:///Users/operator/private.log"],
    ["macOS application path", "Review /Applications/UAA.app"],
    [
      "macOS launch agent path",
      "Review /Library/LaunchAgents/com.example.plist",
    ],
    [
      "punctuated macOS launch agent path",
      "Review:/Library/LaunchAgents/example.plist",
    ],
    [
      "oversized whitespace-padded text",
      `${" ".repeat(10_000)}Safe summary${" ".repeat(10_000)}`,
    ],
    ["overlong text", "A".repeat(801)],
  ])("rejects %s before Setup text reaches the UI", (_name, unsafeText) => {
    const payload = completeSetupPayload();
    const steps = payload.steps as Array<Record<string, unknown>>;
    steps[0].safe_summary = unsafeText;

    const normalized = normalizeMacOSSetupAssistant(
      payload,
      mockControlCenterData.macosSetupAssistant,
    );

    expect(normalized.usedFallback).toBe(true);
    expect(normalized.value).toEqual(
      mockControlCenterData.macosSetupAssistant,
    );
  });

  it("rejects oversized Setup collections before rendering", () => {
    const payload = completeSetupPayload();
    payload.next_steps = Array.from(
      { length: 101 },
      (_, index) => `Review bounded setup step ${index}`,
    );

    expect(
      normalizeMacOSSetupAssistant(
        payload,
        mockControlCenterData.macosSetupAssistant,
      ).usedFallback,
    ).toBe(true);
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
