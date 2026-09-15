import { afterEach, describe, expect, it, vi } from "vitest";
import { FinanceCommitNotAttemptedError, postFinanceWorkspace, setLocalApiBearerForSession } from "./client";
import { loadFinance, validateFinanceCommit, validateFinancePreparation, validateFinanceView } from "./financeWorkspace";
import { financeBinding, financeCommit, financePreparation, financeView } from "../test/financeWorkspaceFixture";

const intent = { operation: "review_decision" as const, expected_revision: 2, request_ref: "request-ref:finance:test", idempotency_ref: "idempotency-ref:finance:test", review_item_ref: financeView.review_items[0].review_item_ref, decision: "confirm" as const };
function response(value: unknown) {
  return new Response(JSON.stringify(value), { headers: {
    "X-UAA-Backend-Revision-Ref": financeBinding.backendRevisionRef,
    "X-UAA-Backend-Instance-Ref": financeBinding.backendInstanceRef,
  } });
}
afterEach(() => { vi.unstubAllGlobals(); setLocalApiBearerForSession(null); });

describe("Finance response and transport boundaries", () => {
  it("accepts exact safe view, preparation and committed receipt", () => {
    expect(validateFinanceView(financeView)).toBe(financeView);
    const prepared = financePreparation(intent);
    expect(validateFinancePreparation(prepared, intent, financeView.configuration_ref)).toBe(prepared);
    const receipt = financeCommit(prepared);
    expect(validateFinanceCommit(receipt, prepared)).toBe(receipt);
  });
  it.each([
    { real_financial_data_allowed: true }, { mutation_performed: true },
    { item_count: 2 }, { item_offset: 50 }, { status: "unavailable" },
    { review_items: [{ ...financeView.review_items[0], decision_authority_granted: true }] },
    { review_items: [{ ...financeView.review_items[0], state: "confirmed" }] },
  ])("rejects altered view posture or pagination %j", patch => {
    expect(() => validateFinanceView({ ...financeView, ...patch })).toThrow("FINANCE_RESPONSE_INVALID");
  });
  it("rejects a substituted decision, stale preparation and foreign configuration", () => {
    const prepared = financePreparation(intent);
    expect(() => validateFinancePreparation(prepared, { ...intent, decision: "reject" }, financeView.configuration_ref)).toThrow();
    expect(() => validateFinancePreparation(prepared, intent, "configuration-ref:finance:other")).toThrow();
    prepared.bundle.preview.expires_at = new Date(Date.now() - 1).toISOString();
    expect(() => validateFinancePreparation(prepared, intent, financeView.configuration_ref)).toThrow();
  });
  it("binds a reopened interrupted review to its exact intent and repository", () => {
    const retainedIntent = { ...intent, compensates_event_ref: null };
    const preparation = financePreparation(intent);
    const view = { ...financeView, status: "outcome_uncertain", revision: null, snapshot_ref: null,
      review_items: [], item_count: 0, pending_review: { intent: retainedIntent, preparation } };
    expect(validateFinanceView(view)).toBe(view);
    expect(() => validateFinanceView({ ...view, status: "ready" })).toThrow();
    expect(() => validateFinanceView({ ...view, repository_ref: "repository-ref:finance:other" })).toThrow();
    expect(() => validateFinanceView({ ...view, pending_review: { intent: { ...retainedIntent, decision: "reject" }, preparation } })).toThrow();
    expect(() => validateFinanceView({ ...view, pending_review: { intent: { ...retainedIntent, operation: "create" }, preparation } })).toThrow();
  });
  it.each([{ phase: "prepared" }, { operation: "create" }, { after_revision: 99 }, { idempotency_ref: "idempotency-ref:finance:other" }, { payment_or_transfer_performed: true }])("rejects a mismatched receipt %j", patch => {
    const prepared = financePreparation(intent); const saved = financeCommit(prepared);
    expect(() => validateFinanceCommit({ ...saved, receipt: { ...saved.receipt, ...patch } }, prepared)).toThrow();
  });
  it("uses authenticated, exact backend and idempotency bindings", async () => {
    const prepared = financePreparation(intent);
    const fetcher = vi.fn().mockResolvedValue(response(prepared)); vi.stubGlobal("fetch", fetcher);
    setLocalApiBearerForSession("test-session-only");
    await postFinanceWorkspace("preview", intent, intent.idempotency_ref, financeBinding);
    expect(fetcher).toHaveBeenCalledWith(expect.stringContaining("/control-center/finance/workspace/preview"), expect.objectContaining({
      method: "POST", cache: "no-store", headers: expect.objectContaining({ "Authorization": "Bearer test-session-only", "X-UAA-Idempotency-Key": intent.idempotency_ref, "X-UAA-Control-Center-Mutation-Binding": "backend-truth.v1", "X-UAA-Expected-Backend-Instance-Ref": financeBinding.backendInstanceRef }),
    }));
  });
  it("never sends an unconfirmed commit or oversized body", async () => {
    const fetcher = vi.fn(); vi.stubGlobal("fetch", fetcher);
    await expect(postFinanceWorkspace("commit", {}, intent.idempotency_ref, financeBinding)).rejects.toThrow("FINANCE_CONFIRMATION_REQUIRED");
    await expect(postFinanceWorkspace("preview", { data: "x".repeat(131072) }, intent.idempotency_ref, financeBinding)).rejects.toThrow("FINANCE_REQUEST_TOO_LARGE");
    expect(fetcher).not.toHaveBeenCalled();
  });
  it("rejects a response from another backend and never substitutes mock state", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify(financeView))));
    await expect(loadFinance(financeBinding)).rejects.toThrow("BACKEND_RESPONSE_PROVENANCE_MISMATCH");
  });
  it("bounds response bytes and suppresses raw server errors", async () => {
    const large = response("x".repeat(1_048_576));
    const fetcher = vi.fn().mockResolvedValueOnce(large).mockResolvedValueOnce(new Response("private diagnostic", { status: 503, headers: response({}).headers }));
    vi.stubGlobal("fetch", fetcher);
    await expect(loadFinance(financeBinding)).rejects.toThrow("FINANCE_RESPONSE_TOO_LARGE");
    await expect(loadFinance(financeBinding)).rejects.toThrow("FINANCE_REQUEST_REJECTED_503");
  });
  it.each([403, 409, 503])("recognizes a bound not-attempted commit rejection at %s", async status => {
    const rejected = new Response(JSON.stringify({ detail: {
      code: "FINANCE_WORKSPACE_PREPARATION_NOT_CURRENT", commit_outcome: "not_attempted",
      message: "private server diagnostic is never displayed",
    } }), { status, headers: response({}).headers });
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(rejected));
    await expect(postFinanceWorkspace("commit", {}, intent.idempotency_ref, financeBinding, true))
      .rejects.toBeInstanceOf(FinanceCommitNotAttemptedError);
  });
  it.each([
    { code: "FINANCE_WORKSPACE_PREPARATION_NOT_CURRENT", commit_outcome: "unconfirmed" },
    { code: "FINANCE_WORKSPACE_PREPARATION_NOT_CURRENT" },
    { code: "untrusted raw detail", commit_outcome: "not_attempted" },
  ])("does not turn an ambiguous rejection into proof of no attempt %j", async detail => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail }), {
      status: 409, headers: response({}).headers,
    })));
    await expect(postFinanceWorkspace("commit", {}, intent.idempotency_ref, financeBinding, true))
      .rejects.toThrow("FINANCE_REQUEST_REJECTED_409");
  });
  it("rejects unbound, oversized and malformed preflight evidence", async () => {
    const detail = { code: "FINANCE_WORKSPACE_PREPARATION_NOT_CURRENT", commit_outcome: "not_attempted" };
    const fetcher = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail }), { status: 409 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail, data: "x".repeat(1_048_576) }), { status: 409, headers: response({}).headers }))
      .mockResolvedValueOnce(new Response("private invalid json", { status: 409, headers: response({}).headers }));
    vi.stubGlobal("fetch", fetcher);
    await expect(postFinanceWorkspace("commit", {}, intent.idempotency_ref, financeBinding, true)).rejects.toThrow("BACKEND_RESPONSE_PROVENANCE_MISMATCH");
    await expect(postFinanceWorkspace("commit", {}, intent.idempotency_ref, financeBinding, true)).rejects.toThrow("FINANCE_RESPONSE_TOO_LARGE");
    await expect(postFinanceWorkspace("commit", {}, intent.idempotency_ref, financeBinding, true)).rejects.toThrow("FINANCE_REQUEST_REJECTED_409");
  });
});
