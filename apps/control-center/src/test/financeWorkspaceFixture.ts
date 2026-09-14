import type { FinanceIntent, FinancePreparation } from "../api/financeWorkspace";

export const financeBinding = { snapshotRef: "proof-ref:finance:test", backendRevisionRef: "commit-ref:finance:test", backendInstanceRef: "backend-instance-ref:finance:test" };
export const financeView = {
  schema_version: "uaa-finance-workspace-view.v1" as const,
  contract_ref: "contract-ref:finance/FIN-003:synthetic-in-app:v1",
  status: "ready" as const, configuration_ref: "configuration-ref:finance:test", repository_ref: "repository-ref:finance:test",
  revision: 2, snapshot_ref: "snapshot-ref:finance:test", safe_disable_engaged: false, import_available: false,
  item_count: 1, history_count: 0, item_offset: 0, history_offset: 0, page_limit: 50,
  synthetic_only: true, real_financial_data_allowed: false, mutation_performed: false,
  review_items: [{
    review_item_ref: "review-item-ref:finance:test", lineage_ref: "lineage-ref:finance:test", rank: 1, state: "needs_review" as const,
    effective_decision_ref: null, synthetic_only: true, raw_financial_values_included: false, decision_authority_granted: false, mutation_performed: false,
  }], decision_history: [], pending_review: null,
};
export const financeSetup = { ...financeView, status: "book_setup_required" as const, revision: 0, snapshot_ref: null, item_count: 0, review_items: [] };

export function financePreparation(intent: FinanceIntent) {
  return {
    schema_version: "uaa-finance-workspace-preparation.v1" as const,
    configuration_ref: financeView.configuration_ref, synthetic_only: true, real_financial_data_allowed: false,
    bundle: {
      schema_version: "uaa-finance-prepared-mutation-bundle.v1" as const, mutation_performed: false, operator_confirmation_required: true,
      request: {
        ...intent, repository_ref: financeView.repository_ref, synthetic_fixture_only: true, raw_financial_values_included: false,
        real_financial_data_included: false, exact_scope_ref: "scope-ref:finance:test", approval_ref: "approval-ref:finance:test",
        review_preview: intent.review_item_ref ? { review_item_ref: intent.review_item_ref, decision: intent.decision ?? null, compensates_event_ref: intent.compensates_event_ref ?? null } : null,
      },
      preview: {
        preview_ref: "preview-ref:finance:test", payload_fingerprint_ref: "fingerprint-ref:finance:test", exact_scope_ref: "scope-ref:finance:test",
        expected_approval_ref: "approval-ref:finance:test", prepared_at: new Date().toISOString(), expires_at: new Date(Date.now() + 60_000).toISOString(),
        mutation_performed: false, product_runtime_authority_granted: false,
      },
    },
  };
}
export function financeCommit(prepared: FinancePreparation) {
  return {
    schema_version: "uaa-finance-workspace-commit.v1" as const, synthetic_only: true, real_financial_data_included: false,
    receipt: {
      receipt_ref: "receipt-ref:finance:test", phase: "committed" as const, operation: prepared.bundle.request.operation,
      repository_ref: financeView.repository_ref, request_ref: prepared.bundle.request.request_ref, idempotency_ref: prepared.bundle.request.idempotency_ref,
      payload_fingerprint_ref: prepared.bundle.preview.payload_fingerprint_ref,
      before_revision: prepared.bundle.request.expected_revision, after_revision: prepared.bundle.request.expected_revision + 1,
      replayed: false, content_free: true, raw_financial_values_included: false, raw_paths_included: false, key_material_included: false,
      real_financial_data_included: false, connector_call_performed: false, payment_or_transfer_performed: false, filing_or_advice_performed: false,
    },
  };
}
