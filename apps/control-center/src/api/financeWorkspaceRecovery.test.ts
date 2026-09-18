import { beforeEach, describe, expect, it, vi } from "vitest";
import { refreshFinance, validateFinanceView, type FinanceIntent, type FinanceOperation } from "./financeWorkspace";
import { financeBinding, financeCommit, financePreparation, financeSetup, financeView } from "../test/financeWorkspaceFixture";

const transport = vi.hoisted(() => ({ postFinanceWorkspace: vi.fn(), readFinanceWorkspace: vi.fn() }));
vi.mock("./client", () => transport);

const operations: FinanceOperation[] = ["create", "import_commit", "review_decision", "review_undo"];
function retainedAction(operation: FinanceOperation = "review_decision") {
  const intent: FinanceIntent = {
    operation, expected_revision: operation === "create" ? 0 : operation === "import_commit" ? 1 : 2,
    request_ref: "request-ref:finance:retained", idempotency_ref: "idempotency-ref:finance:retained",
    review_item_ref: operation.startsWith("review_") ? financeView.review_items[0].review_item_ref : null,
    decision: operation === "review_decision" ? "defer" : null,
    compensates_event_ref: operation === "review_undo" ? "event-ref:finance:prior" : null,
  };
  return { intent, preparation: financePreparation(intent), result: null };
}

describe("Finance Core recovery presentation", () => {
  beforeEach(() => vi.resetAllMocks());

  it.each(operations)("accepts an exact pending %s and its historical receipt", operation => {
    const recovery = retainedAction(operation);
    const pending = { ...financeView, recovery };
    expect(validateFinanceView(pending)).toBe(pending);
    const saved = { ...pending, recovery: { ...recovery, result: financeCommit(recovery.preparation) } };
    expect(validateFinanceView(saved)).toBe(saved);
  });

  it.each(["book_setup_required", "outcome_uncertain", "unavailable", "helper_unavailable"])("preserves recovery when the book view is %s", status => {
    const recovery = retainedAction("create");
    const value = { ...financeSetup, status, revision: status === "book_setup_required" ? 0 : null,
      recovery: { ...recovery, result: financeCommit(recovery.preparation) } };
    expect(validateFinanceView(value)).toBe(value);
  });

  it("requires explicit null for absent recovery and absent result", () => {
    expect(() => validateFinanceView({ ...financeView, recovery: undefined })).toThrow("FINANCE_RESPONSE_INVALID");
    expect(() => validateFinanceView({ ...financeView, recovery: { ...retainedAction(), result: undefined } })).toThrow("FINANCE_RESPONSE_INVALID");
  });

  it.each([
    { operation: "delete" }, { expected_revision: -1 }, { expected_revision: 0 },
    { request_ref: "request-ref:finance:substituted" }, { idempotency_ref: "idempotency-ref:finance:substituted" },
    { review_item_ref: "review-item-ref:finance:substituted" }, { decision: "confirm" },
    { compensates_event_ref: "event-ref:finance:unexpected" }, { grants_authority: true },
  ])("rejects an altered retained review intent %j", patch => {
    const recovery = retainedAction();
    expect(() => validateFinanceView({ ...financeView, recovery: { ...recovery, intent: { ...recovery.intent, ...patch } } }))
      .toThrow("FINANCE_RESPONSE_INVALID");
  });

  it.each(["create", "import_commit"] as const)("rejects review scope and invalid revisions in retained %s", operation => {
    const recovery = retainedAction(operation);
    for (const patch of [
      { expected_revision: operation === "create" ? 1 : 0 },
      { review_item_ref: "review-item-ref:finance:unexpected" }, { decision: "defer" },
      { compensates_event_ref: "event-ref:finance:unexpected" }, { review_item_ref: undefined },
    ]) {
      expect(() => validateFinanceView({ ...financeView, recovery: { ...recovery, intent: { ...recovery.intent, ...patch } } })).toThrow();
    }
    expect(() => validateFinanceView({ ...financeView, recovery: { ...recovery, preparation: {
      ...recovery.preparation, bundle: { ...recovery.preparation.bundle, request: {
        ...recovery.preparation.bundle.request, review_preview: { decision: "defer" },
      } },
    } } })).toThrow();
  });

  it("rejects substituted undo, foreign configuration or repository and expired preparation", () => {
    const recovery = retainedAction("review_undo");
    expect(() => validateFinanceView({ ...financeView, recovery: { ...recovery,
      intent: { ...recovery.intent, compensates_event_ref: "event-ref:finance:substituted" } } })).toThrow();
    for (const patch of [
      { configuration_ref: "configuration-ref:finance:other" },
      { repository_ref: "repository-ref:finance:other" }, { status: "configuration_invalid" },
    ]) expect(() => validateFinanceView({ ...financeView, recovery, ...patch })).toThrow();
    recovery.preparation.bundle.preview.expires_at = new Date(Date.now() - 1).toISOString();
    expect(() => validateFinanceView({ ...financeView, recovery })).toThrow();
  });

  it.each([
    { phase: "prepared" }, { operation: "create" }, { before_revision: 1 }, { after_revision: 99 },
    { request_ref: "request-ref:finance:other" }, { idempotency_ref: "idempotency-ref:finance:other" },
    { repository_ref: "repository-ref:finance:other" }, { payload_fingerprint_ref: "fingerprint-ref:finance:other" },
    { payment_or_transfer_performed: true },
  ])("rejects a historical result not bound to the exact retained payload %j", patch => {
    const recovery = retainedAction(); const result = financeCommit(recovery.preparation);
    expect(() => validateFinanceView({ ...financeView, recovery: { ...recovery,
      result: { ...result, receipt: { ...result.receipt, ...patch } } } })).toThrow("FINANCE_RESPONSE_INVALID");
  });

  it.each(operations)("refreshes retained %s without submitting a commit", async operation => {
    const { intent, preparation } = retainedAction(operation);
    const fresh = financePreparation(intent);
    transport.postFinanceWorkspace.mockResolvedValue(fresh);
    expect(await refreshFinance(preparation, intent, financeBinding)).toBe(fresh);
    expect(transport.postFinanceWorkspace).toHaveBeenCalledExactlyOnceWith("refresh", preparation, intent.idempotency_ref, financeBinding);
  });

  it("rejects a refresh that replaces the repository or payload", async () => {
    const { intent, preparation } = retainedAction("create");
    const foreignRepository = financePreparation(intent);
    foreignRepository.bundle.request.repository_ref = "repository-ref:finance:other";
    transport.postFinanceWorkspace.mockResolvedValueOnce(foreignRepository);
    await expect(refreshFinance(preparation, intent, financeBinding)).rejects.toThrow("FINANCE_RESPONSE_INVALID");
    const foreignPayload = financePreparation(intent);
    foreignPayload.bundle.preview.payload_fingerprint_ref = "fingerprint-ref:finance:other";
    transport.postFinanceWorkspace.mockResolvedValueOnce(foreignPayload);
    await expect(refreshFinance(preparation, intent, financeBinding)).rejects.toThrow("FINANCE_RESPONSE_INVALID");
  });
});
