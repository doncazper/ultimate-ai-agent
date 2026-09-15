import { postFinanceWorkspace, readFinanceWorkspace, type BackendTruthReadBinding } from "./client";

export type FinanceDecision = "confirm" | "reject" | "defer";
export type FinanceOperation = "create" | "import_commit" | "review_decision" | "review_undo";
export interface FinanceIntent {
  operation: FinanceOperation;
  expected_revision: number;
  request_ref: string;
  idempotency_ref: string;
  review_item_ref?: string;
  decision?: FinanceDecision;
  compensates_event_ref?: string;
}
export interface FinanceItem {
  review_item_ref: string;
  lineage_ref: string;
  rank: number;
  state: "needs_review" | "confirmed" | "rejected" | "deferred";
  effective_decision_ref: string | null;
}
export interface FinanceHistory {
  event_ref: string;
  lineage_ref: string;
  operation: "review_decision" | "review_undo";
  decision: FinanceDecision | null;
  before_revision: number;
}
export interface FinanceView {
  schema_version: "uaa-finance-workspace-view.v1";
  status: "configuration_missing" | "configuration_invalid" | "helper_unavailable" | "book_setup_required" | "ready" | "outcome_uncertain" | "unavailable";
  configuration_ref: string | null;
  repository_ref: string | null;
  revision: number | null;
  snapshot_ref: string | null;
  safe_disable_engaged: boolean;
  import_available: boolean;
  item_count: number;
  history_count: number;
  item_offset: number;
  history_offset: number;
  page_limit: number;
  review_items: FinanceItem[];
  decision_history: FinanceHistory[];
  pending_review: { intent: FinanceIntent; preparation: FinancePreparation } | null;
}
export interface FinancePreparation {
  schema_version: "uaa-finance-workspace-preparation.v1";
  configuration_ref: string;
  bundle: {
    schema_version: "uaa-finance-prepared-mutation-bundle.v1";
    request: Record<string, unknown> & {
      operation: FinanceOperation;
      expected_revision: number;
      repository_ref: string;
      request_ref: string;
      idempotency_ref: string;
    };
    preview: Record<string, unknown> & {
      preview_ref: string;
      payload_fingerprint_ref: string;
      exact_scope_ref: string;
      expires_at: string;
    };
  };
}
export interface FinanceCommit {
  schema_version: "uaa-finance-workspace-commit.v1";
  receipt: {
    receipt_ref: string;
    operation: FinanceOperation;
    request_ref: string;
    idempotency_ref: string;
    before_revision: number;
    after_revision: number;
    replayed: boolean;
    phase: "committed" | "recovered";
  };
}

function record(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
function safeRef(value: unknown): value is string {
  return typeof value === "string" && value.length <= 200 && /^[A-Za-z0-9][A-Za-z0-9._:/-]*$/.test(value);
}
function count(value: unknown, max = Number.MAX_SAFE_INTEGER): value is number {
  return Number.isSafeInteger(value) && Number(value) >= 0 && Number(value) <= max;
}
function fail(): never { throw new Error("FINANCE_RESPONSE_INVALID"); }
const decisions = ["confirm", "reject", "defer"];

export function validateFinanceView(value: unknown, itemOffset = 0, historyOffset = 0): FinanceView {
  if (!record(value) || value.schema_version !== "uaa-finance-workspace-view.v1"
    || value.contract_ref !== "contract-ref:finance/FIN-003:synthetic-in-app:v1"
    || value.synthetic_only !== true || value.real_financial_data_allowed !== false || value.mutation_performed !== false
    || !["configuration_missing", "configuration_invalid", "helper_unavailable", "book_setup_required", "ready", "outcome_uncertain", "unavailable"].includes(String(value.status))
    || typeof value.safe_disable_engaged !== "boolean" || typeof value.import_available !== "boolean"
    || !count(value.item_count, 10_000) || !count(value.history_count, 4096)
    || value.item_offset !== itemOffset || value.history_offset !== historyOffset || value.page_limit !== 50
    || !Array.isArray(value.review_items) || !Array.isArray(value.decision_history)
    || value.review_items.length > 50 || value.decision_history.length > 50
    || ![value.configuration_ref, value.repository_ref, value.snapshot_ref].every(ref => ref === null || safeRef(ref))) fail();
  if (value.status === "ready") {
    if (!count(value.revision) || value.revision < 1 || !safeRef(value.configuration_ref) || !safeRef(value.repository_ref) || !safeRef(value.snapshot_ref)
      || value.review_items.length !== Math.min(50, Math.max(0, value.item_count - itemOffset))
      || value.decision_history.length !== Math.min(50, Math.max(0, value.history_count - historyOffset))) fail();
  } else {
    if (value.review_items.length !== 0 || value.decision_history.length !== 0 || value.item_count !== 0 || value.history_count !== 0) fail();
    if (value.status === "book_setup_required" && (value.revision !== 0 || !safeRef(value.configuration_ref))) fail();
  }
  for (const item of value.review_items) {
    if (!record(item) || !safeRef(item.review_item_ref) || !safeRef(item.lineage_ref) || !count(item.rank, 10_000) || item.rank < 1
      || !["needs_review", "confirmed", "rejected", "deferred"].includes(String(item.state))
      || (item.effective_decision_ref !== null && !safeRef(item.effective_decision_ref))
      || (item.state === "needs_review") !== (item.effective_decision_ref === null)
      || item.synthetic_only !== true || item.raw_financial_values_included !== false || item.decision_authority_granted !== false || item.mutation_performed !== false) fail();
  }
  for (const event of value.decision_history) {
    if (!record(event) || !safeRef(event.event_ref) || !safeRef(event.lineage_ref) || !count(event.before_revision) || event.before_revision < 2
      || !["review_decision", "review_undo"].includes(String(event.operation))
      || (event.operation === "review_decision" ? !decisions.includes(String(event.decision)) : event.decision !== null)
      || event.synthetic_only !== true || event.ledger_postings_changed !== false || event.categorization_performed !== false) fail();
  }
  if (new Set(value.review_items.map(item => item.review_item_ref)).size !== value.review_items.length
    || new Set(value.decision_history.map(event => event.event_ref)).size !== value.decision_history.length) fail();
  if (value.pending_review !== null) {
    if (value.status !== "outcome_uncertain" || !safeRef(value.configuration_ref) || !safeRef(value.repository_ref)
      || !record(value.pending_review) || !record(value.pending_review.intent)) fail();
    const retained = value.pending_review.intent;
    if (!["review_decision", "review_undo"].includes(String(retained.operation))
      || !count(retained.expected_revision) || retained.expected_revision < 2
      || !safeRef(retained.request_ref) || !safeRef(retained.idempotency_ref) || !safeRef(retained.review_item_ref)
      || (retained.operation === "review_decision"
        ? !decisions.includes(String(retained.decision)) || retained.compensates_event_ref !== null
        : retained.decision !== null || !safeRef(retained.compensates_event_ref))) fail();
    const intent = retained as unknown as FinanceIntent;
    const preparation = validateFinancePreparation(value.pending_review.preparation, intent, value.configuration_ref);
    if (preparation.bundle.request.repository_ref !== value.repository_ref) fail();
  }
  return value as unknown as FinanceView;
}

export function validateFinancePreparation(value: unknown, intent: FinanceIntent, configurationRef: string): FinancePreparation {
  if (!record(value) || value.schema_version !== "uaa-finance-workspace-preparation.v1"
    || value.configuration_ref !== configurationRef || value.synthetic_only !== true || value.real_financial_data_allowed !== false
    || !record(value.bundle)) fail();
  const bundle = value.bundle;
  if (bundle.schema_version !== "uaa-finance-prepared-mutation-bundle.v1"
    || bundle.mutation_performed !== false || bundle.operator_confirmation_required !== true
    || !record(bundle.request) || !record(bundle.preview)) fail();
  const request = bundle.request;
  const preview = bundle.preview;
  if (request.operation !== intent.operation || request.expected_revision !== intent.expected_revision
    || request.request_ref !== intent.request_ref || request.idempotency_ref !== intent.idempotency_ref
    || !safeRef(request.repository_ref) || request.synthetic_fixture_only !== true
    || request.raw_financial_values_included !== false || request.real_financial_data_included !== false
    || preview.mutation_performed !== false || preview.product_runtime_authority_granted !== false
    || !safeRef(preview.preview_ref) || !safeRef(preview.payload_fingerprint_ref) || !safeRef(preview.exact_scope_ref)
    || request.exact_scope_ref !== preview.exact_scope_ref || request.approval_ref !== preview.expected_approval_ref
    || typeof preview.expires_at !== "string" || typeof preview.prepared_at !== "string"
    || !Number.isFinite(Date.parse(preview.expires_at)) || !Number.isFinite(Date.parse(preview.prepared_at))
    || Date.parse(preview.expires_at) <= Date.now() || Date.parse(preview.prepared_at) > Date.now() + 5000) fail();
  if (intent.operation === "review_decision" || intent.operation === "review_undo") {
    const review = request.review_preview;
    if (!record(review) || review.review_item_ref !== intent.review_item_ref || review.decision !== (intent.decision ?? null)
      || review.compensates_event_ref !== (intent.compensates_event_ref ?? null)) fail();
  }
  return value as unknown as FinancePreparation;
}

export function validateFinanceCommit(value: unknown, prepared: FinancePreparation): FinanceCommit {
  if (!record(value) || value.schema_version !== "uaa-finance-workspace-commit.v1"
    || value.synthetic_only !== true || value.real_financial_data_included !== false || !record(value.receipt)) fail();
  const receipt = value.receipt;
  const request = prepared.bundle.request;
  if (!safeRef(receipt.receipt_ref) || !["committed", "recovered"].includes(String(receipt.phase))
    || receipt.operation !== request.operation || receipt.repository_ref !== request.repository_ref
    || receipt.request_ref !== request.request_ref || receipt.idempotency_ref !== request.idempotency_ref
    || receipt.payload_fingerprint_ref !== prepared.bundle.preview.payload_fingerprint_ref
    || receipt.before_revision !== request.expected_revision || receipt.after_revision !== request.expected_revision + 1
    || typeof receipt.replayed !== "boolean" || receipt.content_free !== true
    || receipt.raw_financial_values_included !== false || receipt.raw_paths_included !== false || receipt.key_material_included !== false
    || receipt.real_financial_data_included !== false || receipt.connector_call_performed !== false
    || receipt.payment_or_transfer_performed !== false || receipt.filing_or_advice_performed !== false) fail();
  return value as unknown as FinanceCommit;
}

export async function loadFinance(binding: BackendTruthReadBinding, itemOffset = 0, historyOffset = 0): Promise<FinanceView> {
  return validateFinanceView(await readFinanceWorkspace(binding, itemOffset, historyOffset), itemOffset, historyOffset);
}
export async function prepareFinance(intent: FinanceIntent, configurationRef: string, binding: BackendTruthReadBinding): Promise<FinancePreparation> {
  return validateFinancePreparation(await postFinanceWorkspace("preview", intent, intent.idempotency_ref, binding), intent, configurationRef);
}
export async function refreshFinance(prepared: FinancePreparation, intent: FinanceIntent, binding: BackendTruthReadBinding): Promise<FinancePreparation> {
  return validateFinancePreparation(await postFinanceWorkspace("refresh", prepared, intent.idempotency_ref, binding), intent, prepared.configuration_ref);
}
export async function commitFinance(prepared: FinancePreparation, binding: BackendTruthReadBinding): Promise<FinanceCommit> {
  return validateFinanceCommit(await postFinanceWorkspace("commit", prepared, prepared.bundle.request.idempotency_ref, binding, true), prepared);
}
