import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type {
  AutocorrectControlStatus,
  AutocorrectProposal,
  AutocorrectReviewReceipt,
} from "../api/types";
import { AutocorrectControlPanel } from "./AutocorrectControlPanel";

const apiMocks = vi.hoisted(() => ({
  fetchAutocorrectStatus: vi.fn(),
  submitAutocorrectProposalPreview: vi.fn(),
  submitAutocorrectReviewPreview: vi.fn(),
}));

vi.mock("../api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api/client")>()),
  ...apiMocks,
}));

const status: AutocorrectControlStatus = {
  schema_version: "uaa-autocorrect-controls.v1",
  contract_ref: "contract-ref:queue-v2:Q28:autocorrect-controls:v1",
  status: "implemented_proposal_only",
  supported_target_kinds: [
    "task",
    "task_occurrence",
    "board",
    "board_template",
    "calendar_set",
  ],
  minimum_review_confidence: 60,
  process_local_review_capacity: 256,
  exact_revision_required: true,
  idempotency_conflicts_fail_closed: true,
  rejection_learning_content_free: true,
  canonical_mutation_enabled: false,
  changeset_creation_enabled: false,
  rollback_execution_enabled: false,
  model_calls_enabled: false,
  external_writes_enabled: false,
  safe_summary: "Content-free proposal review only.",
  blocked_authority_refs: ["blocked-authority-ref:autocorrect:canonical-mutation"],
  next_safe_action: "Review the exact diff.",
};

const fieldDiff = {
  operation_ref: "operation-ref:autocorrect:review-field",
  target_ref: "task-ref:review-target",
  field_ref: "field-ref:title",
  change_kind: "updated" as const,
  before_fingerprint_ref: "fingerprint-ref:before",
  after_fingerprint_ref: "fingerprint-ref:after",
  raw_value_included: false as const,
};

const proposal: AutocorrectProposal = {
  schema_version: "uaa-autocorrect-controls.v1",
  contract_ref: "contract-ref:queue-v2:Q28:autocorrect-controls:v1",
  proposal_ref: `correction-proposal-ref:sha256:${"a".repeat(64)}`,
  proposal_fingerprint_ref: `correction-proposal-fingerprint-ref:sha256:${"b".repeat(64)}`,
  source_proposal_ref: "proposal-ref:reviewed-candidate",
  workspace_ref: "workspace-ref:local",
  target_kind: "task",
  target_owner: "tasks",
  target_ref: "task-ref:review-target",
  state: "ready_for_review",
  confidence_percent: 88,
  confidence: "high",
  comparison: {
    target_ref: "task-ref:review-target",
    expected_revision_ref: "revision-ref:target:1",
    current_revision_ref: "revision-ref:target:1",
    field_diffs: [fieldDiff],
    changed_field_count: 1,
    exact_revision_match: true,
    raw_values_included: false,
  },
  evidence_refs: ["evidence-ref:review-source"],
  reason_refs: ["reason-ref:operator-correction"],
  rejection_history_refs: [],
  expected_approval_scope_ref: "approval-scope-ref:sha256:sample",
  expected_changeset_plan_ref: "changeset-plan-ref:sha256:sample",
  review_packet_ref: "correction-review-packet-ref:sha256:sample",
  rollback: {
    rollback_plan_ref: "rollback-plan-ref:sha256:sample",
    rollback_ready: true,
    rollback_requires_applied_changeset_receipt: true,
    rollback_execution_available: false,
    safe_disable_available: true,
  },
  next_safe_action: "Review without applying.",
  blocked_authority_refs: ["blocked-authority-ref:autocorrect:canonical-mutation"],
  canonical_state_mutated: false,
  changeset_created: false,
  approval_granted: false,
  rollback_executed: false,
  model_call_performed: false,
  external_write_performed: false,
};

const receipt: AutocorrectReviewReceipt = {
  schema_version: "uaa-autocorrect-controls.v1",
  contract_ref: "contract-ref:queue-v2:Q28:autocorrect-controls:v1",
  receipt_ref: "correction-review-receipt-ref:sha256:sample",
  review_fingerprint_ref: "correction-review-fingerprint-ref:sha256:sample",
  proposal_ref: proposal.proposal_ref,
  proposal_fingerprint_ref: proposal.proposal_fingerprint_ref,
  reviewer_ref: "reviewer-ref:local-operator",
  idempotency_ref: "idempotency-ref:autocorrect:sample:accept",
  decision: "accept",
  outcome: "accepted_for_changeset_review",
  superseding_proposal_ref: null,
  rejection_learning_ref: null,
  expected_changeset_plan_ref: proposal.expected_changeset_plan_ref,
  expected_approval_scope_ref: proposal.expected_approval_scope_ref,
  rollback_plan_ref: proposal.rollback.rollback_plan_ref,
  evidence_refs: proposal.evidence_refs,
  next_safe_action: "Prepare a separately approved ECO-008 child lane.",
  replayed: false,
  canonical_state_mutated: false,
  changeset_created: false,
  approval_granted: false,
  rollback_executed: false,
  model_call_performed: false,
  external_write_performed: false,
};

describe("AutocorrectControlPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    apiMocks.fetchAutocorrectStatus.mockResolvedValue(status);
    apiMocks.submitAutocorrectProposalPreview.mockResolvedValue(proposal);
    apiMocks.submitAutocorrectReviewPreview.mockResolvedValue(receipt);
  });

  it("renders backend authority truth and a content-free exact comparison", async () => {
    render(<AutocorrectControlPanel />);

    expect(await screen.findByText(/Minimum review confidence: 60%/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Preview correction" }));

    expect(apiMocks.submitAutocorrectProposalPreview).toHaveBeenCalledWith(
      expect.objectContaining({
        target_kind: "task",
        target_owner: "tasks",
        raw_content_included: false,
        model_generated: false,
        field_diffs: [expect.objectContaining({ raw_value_included: false })],
      }),
    );
    expect(await screen.findByText("matched")).toBeInTheDocument();
    expect(screen.getByText("omitted")).toBeInTheDocument();
    expect(screen.getByText(/Before:/)).toHaveTextContent("fingerprint-ref:before");
    expect(screen.getByText(/Proposed:/)).toHaveTextContent("fingerprint-ref:after");
  });

  it("records review-only acceptance without presenting mutation as performed", async () => {
    render(<AutocorrectControlPanel />);
    fireEvent.click(screen.getByRole("button", { name: "Preview correction" }));
    fireEvent.click(
      await screen.findByRole("button", { name: "Accept for ChangeSet review" }),
    );

    expect(apiMocks.submitAutocorrectReviewPreview).toHaveBeenCalledWith(
      expect.objectContaining({
        decision: "accept",
        superseding_proposal_ref: null,
      }),
    );
    expect(
      await screen.findByText("accepted_for_changeset_review"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Canonical mutation: no · ChangeSet created: no · Rollback executed: no"),
    ).toBeInTheDocument();
  });
});
