import { describe, expect, it } from "vitest";
import { mockControlCenterData } from "../mocks/controlCenterData";
import { normalizeMacOSSetupAssistant } from "./macosSetupAssistant";

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
    const normalized = normalizeMacOSSetupAssistant(
      {
        lifecycle: {
          schema_version: "macos_setup_lifecycle.v1",
          contract_ref: "macos-setup-lifecycle-contract:backend-test",
          status: "blocked_by_authority",
          current_state: "prerequisites",
          state_sequence: ["prerequisites", "ready_to_install", "failed"],
          operations: [
            {
              operation: "install",
              command_ref: "repo-local-command:macos-setup-lifecycle:install",
              status: "blocked_by_authority",
              current_state: "prerequisites",
              target_state: "installed",
              safe_summary: "Backend install contract remains blocked.",
              exact_scope_ref: "scope-ref:macos-setup-lifecycle:install",
              approval_ref: "approval-ref:macos-setup-lifecycle:install",
              idempotency_key_ref:
                "idempotency-ref:macos-setup-lifecycle:install",
              receipt_ref: "receipt-plan:macos-setup-lifecycle:install",
              rollback_ref: "rollback-plan:macos-setup-lifecycle:install",
              safe_disable_ref:
                "safe-disable-ref:macos-setup-lifecycle:install",
              evidence_refs: ["docs-ref:uaa-setup-assistant-plan"],
              verifier_refs: ["pytest:test-macos-setup-lifecycle"],
              reason_codes: [
                "MACOS_SETUP_LIFECYCLE_AUTHORITY_NOT_GRANTED",
              ],
              mutation_required: true,
              live_probe_required: false,
              approval_required: true,
              authority_granted: false,
              state_change_performed: false,
              subprocess_executed: false,
              file_mutation_performed: false,
              process_mutation_performed: false,
              credential_write_performed: false,
              network_request_performed: false,
              receipt_persisted: false,
            },
          ],
          health_contract: {
            contract_ref: "macos-setup-health-contract:backend-test",
            status: "blocked_by_authority",
            required_check_refs: [
              "health-check-ref:setup-process-identity",
            ],
            safe_summary: "No live setup probe has run.",
            process_identity_verified: false,
            api_manifest_version_verified: false,
            loopback_bind_verified: false,
            control_center_compatibility_verified: false,
            forbidden_authority_absence_verified: false,
            live_probe_performed: false,
          },
        },
      },
      mockControlCenterData.macosSetupAssistant,
    );

    expect(normalized.usedFallback).toBe(true);
    expect(normalized.value.lifecycle.contractRef).toBe(
      "macos-setup-lifecycle-contract:backend-test",
    );
    expect(normalized.value.lifecycle.stateSequence).toEqual([
      "prerequisites",
      "ready_to_install",
      "failed",
    ]);
    expect(normalized.value.lifecycle.operations[0]).toMatchObject({
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
    const normalized = normalizeMacOSSetupAssistant(
      {
        lifecycle: {
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
          operations: [
            {
              operation: "install",
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
            },
          ],
          health_contract: {
            status: "healthy",
            process_identity_verified: true,
            api_manifest_version_verified: true,
            loopback_bind_verified: true,
            control_center_compatibility_verified: true,
            forbidden_authority_absence_verified: true,
            live_probe_performed: true,
          },
        },
      },
      mockControlCenterData.macosSetupAssistant,
    );

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
    expect(normalized.value.lifecycle.operations[0]).toMatchObject({
      operation: "install",
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
});
