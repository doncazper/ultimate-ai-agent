import type { ReactNode } from "react";
import type {
  CodingCockpitPreviewPanel,
  CodingCockpitRefItem,
  CodingCockpitSessionReadModel,
  CodingGitReviewReadModel,
  CodingLivePreviewReadModel,
  CodingMultiAgentReviewReadModel,
  CodingPatchApplyReadinessReadModel,
  CodingPatchProposalReadModel,
  CodingProjectModelReadModel,
  CodingTestCommandReadinessReadModel,
  CodingWorkspaceContextReadModel,
} from "../api/types";
import { SafeAlert } from "./SafeAlert";

interface CodingCockpitPanelProps {
  context: CodingWorkspaceContextReadModel;
  gitReview: CodingGitReviewReadModel;
  livePreview: CodingLivePreviewReadModel;
  multiAgentReview: CodingMultiAgentReviewReadModel;
  patchApplyReadiness: CodingPatchApplyReadinessReadModel;
  patchProposal: CodingPatchProposalReadModel;
  session: CodingCockpitSessionReadModel;
  testCommandReadiness: CodingTestCommandReadinessReadModel;
  authoritative: boolean;
}

export function CodingCockpitPanel({
  authoritative,
  context,
  gitReview,
  livePreview,
  multiAgentReview,
  patchApplyReadiness,
  patchProposal,
  session,
  testCommandReadiness,
}: CodingCockpitPanelProps) {
  const backendOwned =
    authoritative &&
    session.backend_owned &&
    !session.mock_fallback &&
    session.local_read_model_only &&
    session.safe_refs_only &&
    session.project_model.backend_owned &&
    session.project_model.read_only &&
    session.project_model.safe_refs_only &&
    session.project_model.repo_file_read_performed === false &&
    session.project_model.file_write_enabled === false &&
    session.project_model.shell_subprocess_execution_enabled === false &&
    session.project_model.git_mutation_enabled === false &&
    session.project_model.browser_automation_enabled === false &&
    session.project_model.provider_model_call_enabled === false &&
    context.backend_owned &&
    context.read_only &&
    context.preview_only &&
    context.safe_refs_only &&
    patchProposal.backend_owned &&
    patchProposal.read_only &&
    patchProposal.proposal_only &&
    patchProposal.safe_refs_only &&
    patchApplyReadiness.backend_owned &&
    patchApplyReadiness.read_only &&
    patchApplyReadiness.readiness_only &&
    patchApplyReadiness.safe_refs_only &&
    testCommandReadiness.backend_owned &&
    testCommandReadiness.read_only &&
    testCommandReadiness.readiness_only &&
    testCommandReadiness.safe_refs_only &&
    gitReview.backend_owned &&
    gitReview.read_only &&
    gitReview.proposal_only &&
    gitReview.safe_refs_only &&
    livePreview.backend_owned &&
    livePreview.read_only &&
    livePreview.status_only &&
    livePreview.safe_refs_only &&
    isSafeMultiAgentReview(multiAgentReview);
  const currentAuthorityMode =
    session.authority_modes.find((mode) => mode.state === "current") ??
    session.authority_modes[0];

  return (
    <section
      className="page-section coding-cockpit"
      aria-labelledby="coding-cockpit-heading"
      data-testid="coding-cockpit"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">Read-only coding command center</p>
          <h2 id="coding-cockpit-heading">Coding Cockpit</h2>
        </div>
        <span className="status-pill compact">
          {backendOwned ? session.status : "non-authoritative mock fallback"}
        </span>
      </div>

      <SafeAlert
        tone={backendOwned ? "info" : "warning"}
        title={
          backendOwned
            ? "Backend-owned coding session"
            : "Non-authoritative Coding fallback"
        }
        message={
          backendOwned
            ? "Python Core owns this read model. Control Center is rendering safe refs only and grants no mutation authority."
            : "The coding cockpit is rendering fallback data only. It is not workflow truth and no coding authority is enabled."
        }
      />

      <div className="coding-command-bar" aria-label="Coding cockpit status">
        <DetailTile label="Workspace" value={session.workspace_ref} />
        <DetailTile label="Branch" value={session.branch_label} />
        <DetailTile label="Active agent" value={session.active_agent_label} />
        <DetailTile label="Task status" value={session.task_status} />
        <label className="coding-authority-select">
          <span>Authority Mode</span>
          <select
            aria-label="Coding authority mode"
            disabled
            value={currentAuthorityMode?.label ?? session.authority_mode}
          >
            {session.authority_modes.map((mode) => (
              <option key={mode.mode_ref} value={mode.label}>
                {mode.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="coding-grid">
        <aside className="coding-pane workspace-pane" aria-label="Workspace context">
          <PanelHeader
            eyebrow="Workspace"
            title="Context"
            state={session.workspace_context.state}
          />
          <PanelBody panel={session.workspace_context} />
          <ProjectModelPreview
            authoritative={backendOwned}
            projectModel={session.project_model}
          />
          <ContextPackPreview context={context} authoritative={backendOwned} />
          <RefStack title="Context refs" refs={session.same_ref_spine.slice(0, 5)} />
        </aside>

        <div className="coding-main-pane" aria-label="Task diff and proof preview">
          <PreviewPanel panel={session.task_timeline} eyebrow="Workflow" />
          <PreviewPanel panel={session.diff_preview} eyebrow="Patch preview">
            <PatchProposalPreview
              authoritative={backendOwned}
              proposal={patchProposal}
            />
            <PatchApplyReadinessPreview
              authoritative={backendOwned}
              readiness={patchApplyReadiness}
            />
            <div className="coding-action-row" aria-label="Patch actions">
              <DisabledAction label="Accept all" />
              <DisabledAction label="Accept file" />
              <DisabledAction label="Accept hunk" />
              <DisabledAction label="Apply patch" />
            </div>
          </PreviewPanel>
          <PreviewPanel panel={session.proof_preview} eyebrow="Proof" />
        </div>

        <aside className="coding-pane chat-pane" aria-label="Agent chat and task thread">
          <PanelHeader
            eyebrow="Agent thread"
            title="Chat"
            state={session.chat_thread.state}
          />
          <PanelBody panel={session.chat_thread} />
          <MultiAgentReviewPreview
            authoritative={backendOwned}
            review={multiAgentReview}
          />
          <div className="coding-authority-stack" aria-label="Authority profiles">
            {session.authority_modes.map((mode) => (
              <article className="coding-authority-card" key={mode.mode_ref}>
                <div>
                  <strong>{mode.label}</strong>
                  <p>{mode.safe_summary}</p>
                </div>
                <span className="status-pill compact">
                  {mode.allowed_now ? "current" : mode.state.replaceAll("_", " ")}
                </span>
              </article>
            ))}
          </div>
        </aside>
      </div>

      <div className="coding-bottom-drawer" aria-label="Coding preview drawer">
        <DrawerPanel panel={session.terminal_preview} actionLabel="Run command">
          <TestCommandReadinessPreview
            authoritative={backendOwned}
            readiness={testCommandReadiness}
          />
        </DrawerPanel>
        <DrawerPanel panel={session.git_preview} actionLabel="Commit">
          <GitReviewPreview authoritative={backendOwned} review={gitReview} />
        </DrawerPanel>
        <DrawerPanel panel={session.test_output_preview} actionLabel="Run tests" />
        <DrawerPanel panel={session.live_preview} actionLabel="Preview status">
          <LivePreviewReadinessPreview
            authoritative={backendOwned}
            preview={livePreview}
          />
        </DrawerPanel>
      </div>

      <div className="coding-boundary-strip" aria-label="Blocked coding authority">
        <div>
          <strong>Blocked authority</strong>
          <span>
            File writes, shell/subprocess execution, Git mutation, provider/model
            calls, browser automation, connector writes, background autonomy, and
            production authority remain blocked.
          </span>
        </div>
        <RefStack title="Blocked refs" refs={session.blocked_authority_refs} />
      </div>
    </section>
  );
}

function ProjectModelPreview({
  authoritative,
  projectModel,
}: {
  authoritative: boolean;
  projectModel: CodingProjectModelReadModel;
}) {
  return (
    <div className="coding-context-pack" aria-label="Coding project model posture">
      <div className="coding-context-budget">
        <DetailTile label="Project" value={projectModel.project_model_ref} />
        <DetailTile label="Lane" value={projectModel.lane_ref} />
        <DetailTile
          label="Status"
          value={projectModel.status.replaceAll("_", " ")}
        />
      </div>
      <p className="safe-copy">
        {authoritative
          ? "Project posture is backend-owned, read-only, and safe-ref only."
          : "Project posture is non-authoritative fallback data only."}
      </p>
      <div className="coding-item-stack">
        {projectModel.capabilities.slice(0, 6).map((item) => (
          <article className="coding-item-row" key={item.capability_ref}>
            <div>
              <strong>{item.label}</strong>
              <p>{item.safe_summary}</p>
            </div>
            <span className="status-pill compact">
              {item.state.replaceAll("_", " ")}
            </span>
          </article>
        ))}
      </div>
      <RefStack refs={projectModel.blocked_authority_refs} title="Blocked refs" />
      <p className="safe-copy">{projectModel.next_safe_action}</p>
    </div>
  );
}

function ContextPackPreview({
  authoritative,
  context,
}: {
  authoritative: boolean;
  context: CodingWorkspaceContextReadModel;
}) {
  return (
    <div className="coding-context-pack" aria-label="Coding context pack preview">
      <div className="coding-context-budget">
        <DetailTile label="Context pack" value={context.context_pack_ref} />
        <DetailTile label="Budget" value={context.budget_state.replaceAll("_", " ")} />
        <DetailTile
          label="Tokens"
          value={`${context.token_estimate_total}/${context.token_budget_limit}`}
        />
      </div>
      <p className="safe-copy">
        {authoritative
          ? "Context preview is backend-owned, read-only, and safe-ref only."
          : "Context preview is non-authoritative fallback data only."}
      </p>
      <div className="coding-item-stack">
        {context.context_refs.slice(0, 4).map((item) => (
          <article className="coding-item-row" key={item.context_ref}>
            <div>
              <strong>{item.label}</strong>
              <p>{item.include_reason}</p>
            </div>
            <span className="status-pill compact">
              {item.status.replaceAll("_", " ")}
            </span>
          </article>
        ))}
      </div>
      <div className="coding-context-comparison">
        {context.comparison.map((item) => (
          <p className="safe-copy" key={item.comparison_ref}>
            {item.label}: {item.safe_summary}
          </p>
        ))}
      </div>
    </div>
  );
}

function PatchProposalPreview({
  authoritative,
  proposal,
}: {
  authoritative: boolean;
  proposal: CodingPatchProposalReadModel;
}) {
  return (
    <div className="coding-patch-proposal" aria-label="Coding patch proposal preview">
      <div className="coding-context-budget">
        <DetailTile label="Proposal" value={proposal.patch_proposal_ref} />
        <DetailTile label="Status" value={proposal.status.replaceAll("_", " ")} />
        <DetailTile
          label="Files"
          value={`${proposal.file_changes.length} refs`}
        />
      </div>
      <p className="safe-copy">
        {authoritative
          ? "Patch proposal is backend-owned, proposal-only, and safe-ref only."
          : "Patch proposal is non-authoritative fallback data only."}
      </p>
      <div className="coding-item-stack">
        {proposal.file_changes.map((item) => (
          <article className="coding-item-row" key={item.change_ref}>
            <div>
              <strong>{item.label}</strong>
              <p>{item.safe_summary}</p>
            </div>
            <span className="status-pill compact">
              {item.status.replaceAll("_", " ")}
            </span>
          </article>
        ))}
      </div>
      <div className="coding-context-comparison">
        {proposal.diff_summary_lines.map((line) => (
          <p className="safe-copy" key={line}>
            {line}
          </p>
        ))}
      </div>
    </div>
  );
}

function PatchApplyReadinessPreview({
  authoritative,
  readiness,
}: {
  authoritative: boolean;
  readiness: CodingPatchApplyReadinessReadModel;
}) {
  return (
    <div className="coding-patch-proposal" aria-label="Coding patch apply readiness">
      <div className="coding-context-budget">
        <DetailTile label="Apply readiness" value={readiness.readiness_ref} />
        <DetailTile label="Status" value={readiness.status.replaceAll("_", " ")} />
        <DetailTile
          label="Prereqs"
          value={`${readiness.prerequisites.length} refs`}
        />
      </div>
      <p className="safe-copy">
        {authoritative
          ? "Patch apply readiness is backend-owned, read-only, and blocked until exact authority exists."
          : "Patch apply readiness is non-authoritative fallback data only."}
      </p>
      <div className="coding-item-stack">
        {readiness.prerequisites.slice(0, 4).map((item) => (
          <article className="coding-item-row" key={item.prerequisite_ref}>
            <div>
              <strong>{item.label}</strong>
              <p>{item.safe_summary}</p>
            </div>
            <span className="status-pill compact">
              {item.status.replaceAll("_", " ")}
            </span>
          </article>
        ))}
      </div>
      <p className="safe-copy">{readiness.next_safe_action}</p>
    </div>
  );
}

function TestCommandReadinessPreview({
  authoritative,
  readiness,
}: {
  authoritative: boolean;
  readiness: CodingTestCommandReadinessReadModel;
}) {
  return (
    <div className="coding-patch-proposal" aria-label="Coding test command readiness">
      <div className="coding-context-budget">
        <DetailTile label="Command readiness" value={readiness.readiness_ref} />
        <DetailTile label="Status" value={readiness.status.replaceAll("_", " ")} />
        <DetailTile
          label="Suggested"
          value={`${readiness.suggested_commands.length} refs`}
        />
      </div>
      <p className="safe-copy">
        {authoritative
          ? "Test command readiness is backend-owned, read-only, and blocked until exact shell authority exists."
          : "Test command readiness is non-authoritative fallback data only."}
      </p>
      <div className="coding-item-stack">
        {readiness.suggested_commands.slice(0, 3).map((item) => (
          <article className="coding-item-row" key={item.command_ref}>
            <div>
              <strong>{item.label}</strong>
              <p>{item.safe_command_summary}</p>
            </div>
            <span className="status-pill compact">
              {item.status.replaceAll("_", " ")}
            </span>
          </article>
        ))}
      </div>
      <p className="safe-copy">{readiness.next_safe_action}</p>
    </div>
  );
}

function GitReviewPreview({
  authoritative,
  review,
}: {
  authoritative: boolean;
  review: CodingGitReviewReadModel;
}) {
  return (
    <div className="coding-patch-proposal" aria-label="Coding Git review">
      <div className="coding-context-budget">
        <DetailTile label="Git review" value={review.git_review_ref} />
        <DetailTile label="Status" value={review.status.replaceAll("_", " ")} />
        <DetailTile label="Review refs" value={`${review.review_items.length} refs`} />
      </div>
      <p className="safe-copy">
        {authoritative
          ? "Git review is backend-owned, read-only, and blocked until exact Git authority exists."
          : "Git review is non-authoritative fallback data only."}
      </p>
      <div className="coding-item-stack">
        {review.review_items.slice(0, 3).map((item) => (
          <article className="coding-item-row" key={item.item_ref}>
            <div>
              <strong>{item.label}</strong>
              <p>{item.safe_summary}</p>
            </div>
            <span className="status-pill compact">
              {item.status.replaceAll("_", " ")}
            </span>
          </article>
        ))}
      </div>
      <p className="safe-copy">{review.next_safe_action}</p>
    </div>
  );
}

function LivePreviewReadinessPreview({
  authoritative,
  preview,
}: {
  authoritative: boolean;
  preview: CodingLivePreviewReadModel;
}) {
  return (
    <div className="coding-patch-proposal" aria-label="Coding live preview">
      <div className="coding-context-budget">
        <DetailTile label="Live preview" value={preview.live_preview_ref} />
        <DetailTile label="Status" value={preview.status.replaceAll("_", " ")} />
        <DetailTile
          label="Preview refs"
          value={`${preview.preview_items.length} refs`}
        />
      </div>
      <p className="safe-copy">
        {authoritative
          ? "Live preview is backend-owned, status-only, and blocked until exact browser and dev-server authority exists."
          : "Live preview is non-authoritative fallback data only."}
      </p>
      <div className="coding-item-stack">
        {preview.preview_items.slice(0, 3).map((item) => (
          <article className="coding-item-row" key={item.item_ref}>
            <div>
              <strong>{item.label}</strong>
              <p>{item.safe_summary}</p>
            </div>
            <span className="status-pill compact">
              {item.status.replaceAll("_", " ")}
            </span>
          </article>
        ))}
      </div>
      <p className="safe-copy">{preview.next_safe_action}</p>
    </div>
  );
}

function MultiAgentReviewPreview({
  authoritative,
  review,
}: {
  authoritative: boolean;
  review: CodingMultiAgentReviewReadModel;
}) {
  return (
    <div className="coding-patch-proposal" aria-label="Coding multi-agent review">
      <div className="coding-context-budget">
        <DetailTile label="Review" value={review.review_ref} />
        <DetailTile label="Status" value={review.status.replaceAll("_", " ")} />
        <DetailTile label="Agent slots" value={`${review.agent_slots.length} refs`} />
      </div>
      <p className="safe-copy">
        {authoritative
          ? "Multi-agent review is backend-owned, proposal-only, and blocked until exact agent authority exists."
          : "Multi-agent review is non-authoritative fallback data only."}
      </p>
      <PairAgentRelayPreview
        authoritative={authoritative}
        relay={review.pair_agent_relay}
      />
      <div className="coding-item-stack">
        {review.agent_slots.map((slot) => (
          <article className="coding-item-row" key={slot.agent_slot_ref}>
            <div>
              <strong>{slot.label}</strong>
              <p>{slot.safe_summary}</p>
              <RefStack
                refs={slot.blocked_authority_refs}
                title="Blocked authority"
              />
            </div>
            <span className="status-pill compact">
              {slot.status.replaceAll("_", " ")}
            </span>
          </article>
        ))}
      </div>
      <RefStack refs={review.plan_artifact_refs} title="Plan refs" />
      <RefStack refs={review.review_artifact_refs} title="Review refs" />
      <RefStack refs={review.diff_comparison_refs} title="Diff refs" />
      <RefStack
        refs={review.disagreement_summary_refs}
        title="Disagreement refs"
      />
      <RefStack refs={review.handoff_refs} title="Handoff refs" />
      <RefStack refs={review.proof_refs} title="Proof refs" />
      <RefStack refs={review.evidence_refs} title="Evidence refs" />
      <RefStack refs={review.blocked_authority_refs} title="Blocked refs" />
      <RefStack refs={review.promotion_path_refs} title="Promotion refs" />
      <RefStack refs={review.unblock_prompt_refs} title="Unblock refs" />
      <RefStack refs={review.redactions_applied} title="Redaction refs" />
      <p className="safe-copy">{review.next_safe_action}</p>
    </div>
  );
}

function PairAgentRelayPreview({
  authoritative,
  relay,
}: {
  authoritative: boolean;
  relay: CodingMultiAgentReviewReadModel["pair_agent_relay"];
}) {
  return (
    <section className="coding-pair-relay" aria-label="Coding pair agents">
      <div className="coding-context-budget">
        <DetailTile label="Pair run" value={relay.run_contract.run_ref} />
        <DetailTile label="State" value={relay.run_contract.state} />
        <DetailTile label="Turns" value={`${relay.run_contract.max_turns} max`} />
        <DetailTile
          label="Output"
          value={`${relay.run_contract.per_turn_output_limit_bytes} bytes`}
        />
      </div>
      <p className="safe-copy">
        {authoritative
          ? "Pair Agents is backend-owned preview/readiness. Foreground adapter execution is blocked until the exact lane is approved and proven."
          : "Pair Agents is non-authoritative fallback data only."}
      </p>
      <div className="coding-item-stack">
        {relay.run_contract.agent_slots.map((slot) => (
          <article className="coding-item-row" key={slot.slot_ref}>
            <div>
              <strong>{slot.display_label}</strong>
              <p>{slot.disabled_reason_ref}</p>
              <RefStack refs={slot.argv_template_refs} title="Adapter argv refs" />
              <RefStack refs={slot.allowed_workspace_refs} title="Workspace refs" />
            </div>
            <span className="status-pill compact">
              {slot.status.replaceAll("_", " ")}
            </span>
          </article>
        ))}
      </div>
      <RefStack refs={relay.run_contract.stop_condition_refs} title="Stop refs" />
      <RefStack refs={relay.run_contract.approval_binding_refs} title="Approval refs" />
      <RefStack refs={relay.artifact_refs} title="Artifact refs" />
      <RefStack refs={relay.receipt_refs} title="Receipt refs" />
      <RefStack refs={relay.proof_refs} title="Pair proof refs" />
      <RefStack refs={relay.evidence_refs} title="Pair evidence refs" />
      <RefStack refs={relay.blocked_authority_refs} title="Pair blocked refs" />
      <RefStack refs={relay.promotion_path_refs} title="Pair promotion refs" />
      <RefStack refs={relay.unblock_prompt_refs} title="Pair unblock refs" />
      <p className="safe-copy">{relay.next_safe_action}</p>
    </section>
  );
}

function isSafeMultiAgentReview(
  review: CodingMultiAgentReviewReadModel,
): boolean {
  if (!Array.isArray(review.agent_slots)) {
    return false;
  }
  const deniedTopLevelFlags: Array<keyof CodingMultiAgentReviewReadModel> = [
    "provider_model_call_enabled",
    "provider_sdk_call_enabled",
    "local_agent_execution_enabled",
    "multi_agent_execution_enabled",
    "background_dispatch_enabled",
    "background_autonomy_enabled",
    "autonomous_execution_enabled",
    "context_injection_enabled",
    "raw_prompt_included",
    "raw_response_included",
    "provider_payload_included",
    "file_write_enabled",
    "shell_subprocess_execution_enabled",
    "git_mutation_enabled",
    "browser_automation_enabled",
    "connector_write_enabled",
    "production_authority_enabled",
  ];
  const requiredSlotKinds = [
    "implementer",
    "reviewer",
    "local_verifier",
    "security_reviewer",
    "ux_reviewer",
    "test_fixer",
    "merge_captain",
  ] as const;
  const slotKinds = new Set(review.agent_slots.map((slot) => slot.slot_kind));
  const hasRequiredSlots =
    review.agent_slots.length === requiredSlotKinds.length &&
    requiredSlotKinds.every((slotKind) => slotKinds.has(slotKind));
  const hasRequiredRefGroups = [
    review.backend_route_refs,
    review.frontend_route_refs,
    review.cli_inspection_refs,
    review.docs_refs,
    review.unblock_prompt_refs,
    review.plan_artifact_refs,
    review.review_artifact_refs,
    review.diff_comparison_refs,
    review.disagreement_summary_refs,
    review.handoff_refs,
    review.proof_refs,
    review.evidence_refs,
    review.blocked_authority_refs,
    review.promotion_path_refs,
    review.redactions_applied,
  ].every(isNonEmptyRefArray);
  return (
    review.status === "blocked_missing_multi_agent_authority" &&
    review.backend_owned &&
    review.read_only &&
    review.proposal_only &&
    review.safe_refs_only &&
    isSafePairAgentRelay(review.pair_agent_relay) &&
    hasRequiredSlots &&
    hasRequiredRefGroups &&
    deniedTopLevelFlags.every((flag) => review[flag] === false) &&
    review.agent_slots.every(
      (slot) =>
        isNonEmptyRefArray(slot.output_artifact_refs) &&
        isNonEmptyRefArray(slot.proof_refs) &&
        isNonEmptyRefArray(slot.evidence_refs) &&
        isNonEmptyRefArray(slot.blocked_authority_refs) &&
        slot.provider_model_call_enabled === false &&
        slot.local_agent_execution_enabled === false &&
        slot.background_dispatch_enabled === false &&
        slot.autonomous_execution_enabled === false &&
        slot.raw_prompt_included === false &&
        slot.raw_response_included === false,
    )
  );
}

function isSafePairAgentRelay(
  relay: CodingMultiAgentReviewReadModel["pair_agent_relay"] | undefined,
): boolean {
  if (relay === undefined) {
    return false;
  }
  const deniedFlags: Array<
    keyof CodingMultiAgentReviewReadModel["pair_agent_relay"]
  > = [
    "execution_promoted",
    "foreground_adapter_execution_enabled",
    "local_agent_process_execution_enabled",
    "provider_sdk_call_enabled",
    "provider_model_call_enabled",
    "background_dispatch_enabled",
    "generic_agent_bus_enabled",
    "arbitrary_command_text_allowed",
    "shell_subprocess_execution_enabled",
    "plugin_runtime_import_enabled",
    "browser_automation_enabled",
    "connector_write_enabled",
    "git_mutation_enabled",
    "automatic_patch_apply_enabled",
    "raw_transcript_durable",
    "raw_prompt_persisted",
    "raw_response_persisted",
    "provider_payload_persisted",
    "raw_log_persisted",
    "raw_local_path_persisted",
    "production_authority_enabled",
    "broad_autonomy_enabled",
  ];
  return (
    relay.schema_version === "uaa-coding-pair-agent-relay-runner.v1" &&
    relay.canonical_lane_name === "coding_pair_agent_foreground_relay_runner" &&
    relay.status === "preview_readiness_execution_blocked" &&
    relay.backend_owned &&
    relay.preview_only &&
    relay.readiness_only &&
    relay.safe_refs_only &&
    relay.run_contract.state === "blocked" &&
    relay.run_contract.max_turns <= 12 &&
    relay.run_contract.wall_clock_timeout_seconds <= 3600 &&
    relay.run_contract.per_turn_output_limit_bytes <= 20000 &&
    relay.run_contract.agent_slots.length === 2 &&
    relay.run_contract.agent_slots.every(
      (slot) =>
        slot.arbitrary_command_text_allowed === false &&
        slot.local_agent_process_execution_enabled === false &&
        slot.provider_sdk_call_enabled === false &&
        slot.provider_model_call_enabled === false &&
        slot.background_dispatch_enabled === false &&
        slot.raw_env_persisted === false &&
        slot.raw_prompt_persisted === false &&
        slot.raw_response_persisted === false,
    ) &&
    relay.artifacts.every(
      (artifact) =>
        artifact.raw_content_omitted &&
        artifact.raw_prompt_omitted &&
        artifact.raw_response_omitted &&
        artifact.provider_payload_omitted &&
        artifact.raw_log_omitted &&
        artifact.raw_local_path_omitted &&
        artifact.durable_evidence === false,
    ) &&
    relay.receipts.every(
      (receipt) =>
        receipt.raw_content_included === false &&
        receipt.portable_receipt_ready === true,
    ) &&
    deniedFlags.every((flag) => relay[flag] === false)
  );
}

function isNonEmptyRefArray(value: unknown): value is string[] {
  return (
    Array.isArray(value) &&
    value.length > 0 &&
    value.every((item) => typeof item === "string" && item.length > 0)
  );
}

function PreviewPanel({
  children,
  eyebrow,
  panel,
}: {
  children?: ReactNode;
  eyebrow: string;
  panel: CodingCockpitPreviewPanel;
}) {
  return (
    <article className="coding-pane coding-preview-panel">
      <PanelHeader eyebrow={eyebrow} title={panel.title} state={panel.state} />
      <PanelBody panel={panel} />
      {children}
    </article>
  );
}

function DrawerPanel({
  actionLabel,
  children,
  panel,
}: {
  actionLabel: string;
  children?: ReactNode;
  panel: CodingCockpitPreviewPanel;
}) {
  return (
    <article className="coding-drawer-panel">
      <PanelHeader eyebrow="Preview only" title={panel.title} state={panel.state} />
      <PanelBody panel={panel} compact />
      {children}
      <DisabledAction label={actionLabel} />
    </article>
  );
}

function PanelHeader({
  eyebrow,
  state,
  title,
}: {
  eyebrow: string;
  state: string;
  title: string;
}) {
  return (
    <div className="coding-panel-header">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h3>{title}</h3>
      </div>
      <span className="status-pill compact">{state.replaceAll("_", " ")}</span>
    </div>
  );
}

function PanelBody({
  compact = false,
  panel,
}: {
  compact?: boolean;
  panel: CodingCockpitPreviewPanel;
}) {
  return (
    <div className={compact ? "coding-panel-body compact" : "coding-panel-body"}>
      <p className="muted">{panel.safe_summary}</p>
      <div className="coding-item-stack">
        {panel.items.map((item) => (
          <CodingItem item={item} key={item.item_ref} />
        ))}
      </div>
      <p className="safe-copy">Next safe action: {panel.next_safe_action}</p>
      <RefStack title="Proof refs" refs={panel.proof_refs} />
    </div>
  );
}

function CodingItem({ item }: { item: CodingCockpitRefItem }) {
  return (
    <article className="coding-item-row">
      <div>
        <strong>{item.label}</strong>
        <p>{item.safe_summary}</p>
      </div>
      <span className="status-pill compact">{item.status}</span>
    </article>
  );
}

function DisabledAction({ label }: { label: string }) {
  return (
    <button className="coding-disabled-action" disabled type="button">
      {label}
    </button>
  );
}

function DetailTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="coding-detail-tile">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function RefStack({ refs, title }: { refs: string[]; title: string }) {
  if (refs.length === 0) {
    return null;
  }

  return (
    <div className="coding-ref-stack">
      <span>{title}</span>
      <div>
        {refs.map((ref) => (
          <code key={ref}>{ref}</code>
        ))}
      </div>
    </div>
  );
}
