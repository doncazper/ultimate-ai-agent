import type {
  MacOSSetupAssistantData,
  MacOSSetupAssistantStep,
  MacOSSetupModelRecommendation,
} from "../api/types";

export function MacOSSetupAssistantPanel({
  setup,
}: {
  setup: MacOSSetupAssistantData;
}) {
  return (
    <section className="page-section" aria-labelledby="macos-setup-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">macOS-first onboarding</p>
          <h2 id="macos-setup-heading">macOS Setup Assistant</h2>
        </div>
        <span className="status-pill">{setup.status}</span>
      </div>
      <p className="section-copy">
        Visual setup preview for a future native macOS first-launch flow. This
        surface shows planned setup state, bounded terminal-style details,
        local model choices, approval requirements, receipts, and rollback refs
        without running installer actions.
      </p>

      <div className="setup-summary-grid">
        <SetupFlag label="macOS first" value={setup.macosFirst} />
        <SetupFlag label="Local first" value={setup.localFirst} />
        <SetupFlag label="Disabled by default" value={setup.disabledByDefault} />
        <SetupFlag label="Native app ready" value={setup.nativeMacosAppReady} />
        <SetupFlag
          label="Installer side effects"
          value={setup.installerSideEffectsEnabled}
        />
        <SetupFlag
          label="Model output authority"
          value={setup.modelOutputAuthoritative}
        />
      </div>

      <div className="setup-layout">
        <article className="panel">
          <div className="panel-heading">
            <h3>Setup timeline</h3>
            <span>{setup.visualShellRef}</span>
          </div>
          <div className="setup-timeline">
            {setup.steps.map((step) => (
              <SetupStepCard key={step.stepId} step={step} />
            ))}
          </div>
        </article>

        <div className="trace-column">
          <article className="panel">
            <div className="panel-heading">
              <h3>Model choices</h3>
              <span>recommendation only</span>
            </div>
            <div className="stacked-list">
              {setup.modelRecommendations.map((model) => (
                <ModelRecommendationCard
                  key={model.recommendationRef}
                  model={model}
                />
              ))}
            </div>
          </article>

          <article className="panel">
            <div className="panel-heading">
              <h3>Receipts and rollback</h3>
              <span>planned refs</span>
            </div>
            <dl className="metadata-list">
              <div>
                <dt>Receipt plan</dt>
                <dd>{setup.receiptPlan.receiptPlanRef}</dd>
              </div>
              <div>
                <dt>Audit ref</dt>
                <dd>{setup.receiptPlan.auditRef}</dd>
              </div>
              <div>
                <dt>Latency ref</dt>
                <dd>{setup.receiptPlan.latencyRef}</dd>
              </div>
              <div>
                <dt>Rollback plan</dt>
                <dd>{setup.rollbackPlan.rollbackPlanRef}</dd>
              </div>
              <div>
                <dt>Uninstall ref</dt>
                <dd>{setup.rollbackPlan.uninstallRef}</dd>
              </div>
            </dl>
            <p className="safe-copy">
              {setup.receiptPlan.safeSummary} {setup.rollbackPlan.safeSummary}
            </p>
          </article>
        </div>
      </div>

      <div className="panel-grid">
        <article className="panel">
          <div className="panel-heading">
            <h3>Optional bridges</h3>
            <span>explicit local approval</span>
          </div>
          <ul className="compact-list">
            {setup.bridgePreviews.map((bridge) => (
              <li key={bridge.bridgeRef}>
                <strong>{bridge.label}</strong>
                <small>
                  {bridge.status} · default {bridge.enablementDefault} ·
                  approval required: {bridge.approvalRequired ? "yes" : "no"}
                </small>
                <span>{bridge.safeSummary}</span>
              </li>
            ))}
          </ul>
        </article>

        <article className="panel">
          <div className="panel-heading">
            <h3>Morning review</h3>
            <span>polish list</span>
          </div>
          <ul className="compact-list">
            {setup.morningReviewChecklist.map((item) => (
              <li key={item}>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </article>
      </div>
    </section>
  );
}

function SetupFlag({ label, value }: { label: string; value: boolean }) {
  return (
    <div className="setup-flag" role="status">
      <span>{label}</span>
      <strong>{value ? "yes" : "no"}</strong>
    </div>
  );
}

function SetupStepCard({ step }: { step: MacOSSetupAssistantStep }) {
  return (
    <article className={`setup-step ${step.status}`}>
      <div className="review-card-heading">
        <h3>{step.label}</h3>
        <span>{step.status}</span>
      </div>
      <p>{step.safeSummary}</p>
      <dl className="metadata-list">
        <div>
          <dt>Approval</dt>
          <dd>
            {step.approvalRequired ? step.setupApprovalRef : "not required"}
          </dd>
        </div>
        <div>
          <dt>Receipt</dt>
          <dd>{step.receiptRef}</dd>
        </div>
        <div>
          <dt>Rollback</dt>
          <dd>{step.rollbackRef}</dd>
        </div>
        <div>
          <dt>Next safe action</dt>
          <dd>{step.nextSafeAction}</dd>
        </div>
      </dl>
      <details>
        <summary>Details</summary>
        <div className="setup-detail-block">
          {step.routeRefs.length > 0 ? (
            <div className="note-list">
              {step.routeRefs.map((route) => (
                <span key={route}>{route}</span>
              ))}
            </div>
          ) : null}
          <ul className="compact-list">
            {[...step.detailPreview, ...step.logPreview].map((line) => (
              <li key={line}>
                <span>{line}</span>
              </li>
            ))}
          </ul>
        </div>
      </details>
    </article>
  );
}

function ModelRecommendationCard({
  model,
}: {
  model: MacOSSetupModelRecommendation;
}) {
  return (
    <article className="trace-row">
      <div className="review-card-heading">
        <h3>{model.displayName}</h3>
        <span>{model.selectedByDefault ? "default" : "choice"}</span>
      </div>
      <p>{model.fitSummary}</p>
      <dl className="metadata-list">
        <div>
          <dt>Model ref</dt>
          <dd>{model.modelRef}</dd>
        </div>
        <div>
          <dt>Memory</dt>
          <dd>{model.memoryBucket}</dd>
        </div>
        <div>
          <dt>Disk</dt>
          <dd>{model.diskBucket}</dd>
        </div>
        <div>
          <dt>Approval before download</dt>
          <dd>{model.approvalRequiredBeforeDownload ? "yes" : "no"}</dd>
        </div>
      </dl>
      <p>{model.privacySummary}</p>
    </article>
  );
}
