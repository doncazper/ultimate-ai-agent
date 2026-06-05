import { useState } from "react";
import type { ContextProposalSummary, M39ContextProposalData } from "../api/types";
import { EmptyState } from "./DataState";

export function ContextProposalSurfacePanel({ proposals }: { proposals: M39ContextProposalData }) {
  const [selectedRef, setSelectedRef] = useState(proposals.proposals[0]?.proposalRef ?? "");
  const selected =
    proposals.proposals.find((proposal) => proposal.proposalRef === selectedRef) ?? proposals.proposals[0];

  return (
    <section className="page-section" aria-labelledby="context-proposal-surface-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">M39 CCC context proposal surface</p>
          <h2 id="context-proposal-surface-heading">Context Proposal Surface</h2>
        </div>
        <span className="status-pill compact">review-only</span>
      </div>
      <p className="section-copy">
        Safe context proposals are shown for local review only. The surface displays redacted proposal sections, exact
        source binding refs, source-chain refs, decision status, redaction verification, receipt-plan metadata, and
        denied authority flags.
      </p>
      <p className="safe-copy">{proposals.boundarySummary}</p>
      <p className="safe-copy">
        Control Center output is not authority. Proposal review here does not hand off to OpenWebUI, inject context,
        write memory, export data, execute actions, call models, or reveal raw file material.
      </p>
      <div className="note-list" aria-label="M39 context proposal warnings">
        {proposals.warningCodes.map((code) => (
          <span key={code}>{code}</span>
        ))}
      </div>

      {proposals.proposals.length > 0 && selected ? (
        <div className="review-layout">
          <div className="review-list" aria-label="Context proposals">
            {proposals.proposals.map((proposal) => (
              <ContextProposalRow
                key={proposal.proposalRef}
                proposal={proposal}
                selected={proposal.proposalRef === selected.proposalRef}
                onSelect={setSelectedRef}
              />
            ))}
          </div>
          <ContextProposalDetail proposal={selected} />
        </div>
      ) : (
        <EmptyState title="No context proposals" message="No safe context proposals are available." />
      )}
    </section>
  );
}

function ContextProposalRow({
  proposal,
  selected,
  onSelect
}: {
  proposal: ContextProposalSummary;
  selected: boolean;
  onSelect: (proposalRef: string) => void;
}) {
  return (
    <article
      className={`review-card${selected ? " selected" : ""}`}
      aria-current={selected ? "true" : undefined}
      aria-label={`${proposal.proposalRef} context proposal`}
    >
      <div className="review-card-heading">
        <h3>{proposal.proposalRef}</h3>
        <span>{proposal.status}</span>
      </div>
      <p>{proposal.sourceSummary}</p>
      <p className="review-meta">
        {proposal.redactionStatus} | {proposal.dataClassification}
      </p>
      <button type="button" className="secondary-button" onClick={() => onSelect(proposal.proposalRef)}>
        View context proposal
      </button>
    </article>
  );
}

function ContextProposalDetail({ proposal }: { proposal: ContextProposalSummary }) {
  return (
    <article className="panel review-detail" aria-label="Context proposal detail">
      <div className="section-heading compact-heading">
        <div>
          <p className="eyebrow">Selected proposal</p>
          <h3>{proposal.proposalRef}</h3>
        </div>
        <span className="status-pill compact">proposal-only</span>
      </div>
      <p className="safe-copy">{proposal.safeSummary}</p>
      <p className="safe-copy">
        Control Center output is not authority. M39 proposal review is display-only and cannot approve handoff,
        context injection, memory write, export, model call, raw file access, or execution.
      </p>

      <section aria-labelledby="proposal-sections-heading">
        <h4 id="proposal-sections-heading">Safe proposal sections</h4>
        {proposal.sections.map((section) => (
          <article className="status-card" key={section.sectionRef} aria-label={`${section.sectionRef} section`}>
            <div className="status-card-header">
              <h5>{section.title}</h5>
              <span>{section.sectionRef}</span>
            </div>
            <p>{section.redactedContent}</p>
            <dl className="detail-grid">
              <DetailTerm label="section_ref" value={section.sectionRef} />
              <DetailTerm label="source_ref" value={section.sourceRef} />
              <DetailTerm label="redacted" value={yesNo(section.redacted)} />
              <DetailTerm label="bounded" value={yesNo(section.bounded)} />
              <DetailTerm label="non-authoritative" value={yesNo(section.nonAuthoritative)} />
            </dl>
          </article>
        ))}
      </section>

      <section aria-labelledby="proposal-binding-refs-heading">
        <h4 id="proposal-binding-refs-heading">Exact binding refs</h4>
        <dl className="detail-grid">
          <DetailTerm label="proposal_ref" value={proposal.bindingRefs.proposalRef} />
          <DetailTerm label="approval_ref" value={proposal.bindingRefs.approvalRef} />
          <DetailTerm label="review_packet_ref" value={proposal.bindingRefs.reviewPacketRef} />
          <DetailTerm label="preview_result_ref" value={proposal.bindingRefs.previewResultRef} />
          <DetailTerm label="redaction_summary_ref" value={proposal.bindingRefs.redactionSummaryRef} />
          <DetailTerm label="file_ref" value={proposal.bindingRefs.fileRef} />
          <DetailTerm label="safe_path_ref" value={proposal.bindingRefs.safePathRef} />
          <DetailTerm label="actor_ref" value={proposal.bindingRefs.actorRef} />
        </dl>
      </section>

      <TagList label="Source chain refs" values={proposal.sourceChainRefs} />

      <dl className="detail-grid">
        <DetailTerm label="Decision status" value={proposal.decisionStatus} />
        <DetailTerm label="Redaction verification status" value={proposal.redactionVerificationStatus} />
        <DetailTerm label="Receipt plan ref" value={proposal.receiptPlan.receiptPlanRef} />
        <DetailTerm label="Receipt plan metadata" value={proposal.receiptPlan.safeSummary} />
        <DetailTerm label="raw content stored" value={yesNo(proposal.receiptPlan.rawContentStored)} includeInlineText />
        <DetailTerm label="full file content stored" value={yesNo(proposal.receiptPlan.fullFileContentStored)} />
        <DetailTerm label="unredacted preview stored" value={yesNo(proposal.receiptPlan.unredactedPreviewStored)} />
        <DetailTerm label="context injected" value={yesNo(proposal.receiptPlan.contextInjected)} includeInlineText />
        <DetailTerm label="OpenWebUI handoff performed" value={yesNo(proposal.receiptPlan.openwebuiHandoffPerformed)} />
        <DetailTerm label="memory write performed" value={yesNo(proposal.receiptPlan.memoryWritePerformed)} />
        <DetailTerm label="export performed" value={yesNo(proposal.receiptPlan.exportPerformed)} />
        <DetailTerm label="execution performed" value={yesNo(proposal.receiptPlan.executionPerformed)} />
        <DetailTerm
          label="OpenWebUI handoff authorized"
          value={yesNo(proposal.authority.openwebuiHandoffAuthorized)}
          includeInlineText
        />
        <DetailTerm
          label="context injection authorized"
          value={yesNo(proposal.authority.contextInjectionAuthorized)}
        />
        <DetailTerm label="model call authorized" value={yesNo(proposal.authority.modelCallAuthorized)} />
        <DetailTerm
          label="memory write authorized"
          value={yesNo(proposal.authority.memoryWriteAuthorized)}
          includeInlineText
        />
        <DetailTerm label="export authorized" value={yesNo(proposal.authority.exportAuthorized)} includeInlineText />
        <DetailTerm
          label="execution authorized"
          value={yesNo(proposal.authority.executionAuthorized)}
          includeInlineText
        />
        <DetailTerm label="raw file access authorized" value={yesNo(proposal.authority.rawFileAccessAuthorized)} />
        <DetailTerm label="truth authority claimed" value={yesNo(proposal.authority.truthAuthorityClaimed)} />
      </dl>

      <TagList label="Reason codes" values={proposal.reasonCodes} />
      <TagList label="Authority boundary warnings" values={proposal.authorityWarnings} />
    </article>
  );
}

function DetailTerm({ label, value, includeInlineText = false }: { label: string; value: string; includeInlineText?: boolean }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>
        {value}
        {includeInlineText ? <span className="visually-hidden">{`${label}: ${value}`}</span> : null}
      </dd>
    </div>
  );
}

function TagList({ label, values }: { label: string; values: string[] }) {
  return (
    <div className="tag-section">
      <h4>{label}</h4>
      <div className="note-list" aria-label={label}>
        {values.map((value) => (
          <span key={value}>{value}</span>
        ))}
      </div>
    </div>
  );
}

function yesNo(value: boolean): string {
  return value ? "yes" : "no";
}
