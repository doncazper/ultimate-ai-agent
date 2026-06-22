import {
  privateOperatorTrialAcceptanceLedger,
  privateOperatorTrialManualReviewScaffold,
  privateOperatorTrialPacket,
} from "../mocks/privateOperatorTrialPacket";

export function PrivateOperatorTrialPanel() {
  const packet = privateOperatorTrialPacket;
  const ledger = privateOperatorTrialAcceptanceLedger;
  const scaffold = privateOperatorTrialManualReviewScaffold;
  const counts = packet.checklistItems.reduce(
    (acc, item) => {
      acc[item.trialState] += 1;
      return acc;
    },
    { blocked: 0, needs_operator_review: 0, partial: 0, pass: 0 },
  );
  const ledgerCounts = ledger.surfaceReviews.reduce(
    (acc, review) => {
      acc[review.reviewState] += 1;
      return acc;
    },
    {
      accepted: 0,
      blocked: 0,
      needs_follow_up: 0,
      pending_operator_review: 0,
      revised: 0,
    },
  );
  const unansweredReviewCount = scaffold.reviewItems.filter(
    (item) => item.answerState === "unanswered_pending_manual_review",
  ).length;

  return (
    <section
      className="page-section"
      aria-labelledby="private-operator-trial-heading"
    >
      <div className="section-heading">
        <div>
          <p className="eyebrow">087.2a-2c packet</p>
          <h2 id="private-operator-trial-heading">Private Operator Trial</h2>
        </div>
        <span className="status-pill compact">local/private only</span>
      </div>
      <p className="section-copy">
        UAA-P1-087.2a prepares the local Control Center trial packet as safe
        refs. UAA-P1-087.2b adds the acceptance ledger for manual smoke review
        and pending operator findings. UAA-P1-087.2c adds unanswered manual
        review slots for later; full UAA-P1-087.2 still needs accepted or
        revised local/private findings later.
      </p>

      <div className="metric-grid">
        <Metric label="Pass" value={counts.pass} />
        <Metric label="Partial" value={counts.partial} />
        <Metric label="Blocked" value={counts.blocked} />
        <Metric label="Review" value={counts.needs_operator_review} />
        <Metric label="Pending" value={ledgerCounts.pending_operator_review} />
        <Metric label="Unanswered" value={unansweredReviewCount} />
      </div>

      <div className="panel-grid">
        <article className="status-card">
          <div className="status-card-header">
            <h3>Trial contract</h3>
            <span>{packet.status}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm label="Contract ref" value={packet.contractRef} />
            <DetailTerm label="Milestone" value={packet.milestoneRef} />
            <DetailTerm label="Boot command" value={packet.bootCommandRef} />
            <DetailTerm label="Scope" value={packet.trialScopeRef} />
          </dl>
          <p>{packet.nextSafeAction}</p>
        </article>

        <article className="status-card">
          <div className="status-card-header">
            <h3>Authority boundary</h3>
            <span>blocked</span>
          </div>
          <p>
            The packet adds no backend route, public beta, production authority,
            connector write, memory write, provider/model authority, Code apply,
            shell execution, or OpenWebUI product-state ownership.
          </p>
          <RefList refs={packet.blockedStateRefs} />
        </article>

        <article className="status-card">
          <div className="status-card-header">
            <h3>Evidence refs</h3>
            <span>{packet.evidenceRefs.length}</span>
          </div>
          <RefList refs={packet.evidenceRefs} />
        </article>

        <article className="status-card">
          <div className="status-card-header">
            <h3>UI/copy tasks</h3>
            <span>{packet.uiCopyTaskRefs.length}</span>
          </div>
          <RefList refs={packet.uiCopyTaskRefs} />
        </article>

        <article className="status-card">
          <div className="status-card-header">
            <h3>Acceptance ledger</h3>
            <span>{ledger.trialRunState}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm label="Ledger ref" value={ledger.ledgerRef} />
            <DetailTerm label="Milestone" value={ledger.milestoneRef} />
            <DetailTerm label="Source packet" value={ledger.sourcePacketRef} />
            <DetailTerm label="Reviewer" value="operator-ref:local-private-reviewer" />
          </dl>
          <p>{ledger.nextSafeAction}</p>
        </article>

        <article className="status-card">
          <div className="status-card-header">
            <h3>Manual smoke refs</h3>
            <span>{ledger.manualSmokeStepRefs.length}</span>
          </div>
          <RefList refs={ledger.manualSmokeStepRefs} />
        </article>

        <article className="status-card">
          <div className="status-card-header">
            <h3>Acceptance questions</h3>
            <span>{ledger.acceptanceQuestionRefs.length}</span>
          </div>
          <RefList refs={ledger.acceptanceQuestionRefs} />
        </article>

        <article className="status-card">
          <div className="status-card-header">
            <h3>Tuning decisions</h3>
            <span>{ledger.tuningDecisionRefs.length}</span>
          </div>
          <RefList refs={ledger.tuningDecisionRefs} />
        </article>

        <article className="status-card">
          <div className="status-card-header">
            <h3>Manual review scaffold</h3>
            <span>{scaffold.reviewState}</span>
          </div>
          <dl className="detail-list">
            <DetailTerm label="Scaffold ref" value={scaffold.scaffoldRef} />
            <DetailTerm label="Milestone" value={scaffold.milestoneRef} />
            <DetailTerm label="Source ledger" value={scaffold.sourceLedgerRef} />
            <DetailTerm label="Status" value={scaffold.status} />
          </dl>
          <p>{scaffold.nextSafeAction}</p>
        </article>

        <article className="status-card">
          <div className="status-card-header">
            <h3>Missing implementation</h3>
            <span>{scaffold.missingImplementationRefs.length}</span>
          </div>
          <RefList refs={scaffold.missingImplementationRefs} />
        </article>

        <article className="status-card">
          <div className="status-card-header">
            <h3>Deferred decisions</h3>
            <span>{scaffold.deferredDecisionRefs.length}</span>
          </div>
          <RefList refs={scaffold.deferredDecisionRefs} />
        </article>
      </div>

      <div className="review-grid">
        {packet.checklistItems.map((item) => (
          <article className="review-card" key={item.itemRef}>
            <div className="review-card-heading">
              <h3>{item.surface}</h3>
              <span>{item.trialState}</span>
            </div>
            <p>{item.safeSummary}</p>
            <dl className="detail-list">
              <DetailTerm label="Checklist ref" value={item.itemRef} />
              <DetailTerm label="Next safe action" value={item.nextSafeAction} />
            </dl>
            <RefList refs={item.evidenceRefs} />
            <RefList refs={item.frictionRefs} />
            <RefList refs={item.uiCopyTaskRefs} />
          </article>
        ))}
      </div>

      <div className="review-grid">
        {ledger.surfaceReviews.map((review) => (
          <article className="review-card" key={review.reviewRef}>
            <div className="review-card-heading">
              <h3>{review.surface} acceptance</h3>
              <span>{review.reviewState}</span>
            </div>
            <dl className="detail-list">
              <DetailTerm label="Review ref" value={review.reviewRef} />
              <DetailTerm label="Reviewer" value={review.reviewerRef} />
              <DetailTerm label="Next safe action" value={review.nextSafeAction} />
            </dl>
            <RefList refs={review.findingRefs} />
            <RefList refs={review.blockerRefs} />
          </article>
        ))}
      </div>

      <div className="review-grid">
        {scaffold.reviewItems.map((item) => (
          <article className="review-card" key={item.itemRef}>
            <div className="review-card-heading">
              <h3>{item.surface} manual review</h3>
              <span>{item.answerState}</span>
            </div>
            <p>{item.safeQuestion}</p>
            <dl className="detail-list">
              <DetailTerm label="Question ref" value={item.reviewQuestionRef} />
              <DetailTerm label="Pending answer" value={item.pendingAnswerRef} />
              <DetailTerm label="Next safe action" value={item.nextSafeAction} />
            </dl>
            <RefList refs={item.expectedEvidenceRefs} />
            <RefList refs={item.implementationPrerequisiteRefs} />
          </article>
        ))}
      </div>

      <div className="panel-grid">
        <article className="status-card">
          <div className="status-card-header">
            <h3>Friction findings</h3>
            <span>{packet.frictionFindingRefs.length}</span>
          </div>
          <RefList refs={packet.frictionFindingRefs} />
        </article>
        <article className="status-card">
          <div className="status-card-header">
            <h3>Core loop gaps</h3>
            <span>{packet.coreLoopGapRefs.length}</span>
          </div>
          <RefList refs={packet.coreLoopGapRefs} />
        </article>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <article className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function DetailTerm({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </>
  );
}

function RefList({ refs }: { refs: string[] }) {
  if (refs.length === 0) {
    return <p>No refs recorded.</p>;
  }
  return (
    <ul className="ref-list">
      {refs.map((ref) => (
        <li key={ref}>{ref}</li>
      ))}
    </ul>
  );
}
