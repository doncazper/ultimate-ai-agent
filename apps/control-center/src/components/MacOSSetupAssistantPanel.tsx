import type {
  MacOSSetupAssistantData,
  MacOSSetupAssistantStep,
  MacOSSetupApprovalEnvelope,
  MacOSSetupModelRecommendation,
  ProviderCatalog,
  ProviderCredentialReadinessSummary,
} from "../api/types";
import { ProviderCatalogPanel } from "./ProviderCatalogPanel";

export function MacOSSetupAssistantPanel({
  providerCatalog,
  providerCredentialReadiness,
  setup,
}: {
  providerCatalog: ProviderCatalog;
  providerCredentialReadiness: ProviderCredentialReadinessSummary;
  setup: MacOSSetupAssistantData;
}) {
  const prerequisiteRefs = uniqueRefs(
    setup.steps.flatMap((step) => step.routeRefs),
  );
  const envelopesByStepId = new Map(
    setup.approvalEnvelopes.map((envelope) => [
      envelope.setupStepId,
      envelope,
    ]),
  );

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
        local prerequisite refs, recommendation-only model choices, dry-run
        approval envelopes, receipts, and rollback refs without running
        installer actions.
      </p>

      <ProviderCatalogPanel catalog={providerCatalog} mode="setup" />
      <ProviderCredentialSetupSummary readiness={providerCredentialReadiness} />

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

      <div className="panel-grid">
        <article className="panel">
          <div className="panel-heading">
            <h3>Local prerequisites</h3>
            <span>read-only refs</span>
          </div>
          <p>
            Setup visibility comes from existing local status routes only. No
            lifecycle, model download, bridge, or installer control is exposed.
          </p>
          <div className="note-list" aria-label="Local prerequisite route refs">
            {prerequisiteRefs.map((route) => (
              <span key={route}>{route}</span>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel-heading">
            <h3>Blocked setup authority</h3>
            <span>not scoped</span>
          </div>
          <ul className="compact-list">
            {setup.blockedCapabilities.map((capability) => (
              <li key={capability}>
                <span>{capability}</span>
              </li>
            ))}
          </ul>
        </article>
      </div>

      <div className="setup-layout">
        <article className="panel">
          <div className="panel-heading">
            <h3>Setup timeline</h3>
            <span>{setup.visualShellRef}</span>
          </div>
          <div className="setup-timeline">
            {setup.steps.map((step) => (
              <SetupStepCard
                key={step.stepId}
                step={step}
                envelope={envelopesByStepId.get(step.stepId)}
              />
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
            <h3>Dry-run approval envelopes</h3>
            <span>validation only</span>
          </div>
          <div className="stacked-list">
            {setup.approvalEnvelopes.map((envelope) => (
              <ApprovalEnvelopeCard
                key={envelope.envelopeRef}
                envelope={envelope}
              />
            ))}
          </div>
        </article>

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

function uniqueRefs(refs: string[]) {
  return Array.from(new Set(refs));
}

function ProviderCredentialSetupSummary({
  readiness,
}: {
  readiness: ProviderCredentialReadinessSummary;
}) {
  return (
    <article className="panel provider-credential-readiness-panel">
      <div className="panel-heading">
        <h3>Provider credential and cost posture</h3>
        <span>{readiness.status}</span>
      </div>
      <p>{readiness.safe_summary}</p>
      <dl className="metadata-list">
        <div>
          <dt>Configured</dt>
          <dd>{readiness.posture_counts.configured}</dd>
        </div>
        <div>
          <dt>Not configured</dt>
          <dd>{readiness.posture_counts.not_configured}</dd>
        </div>
        <div>
          <dt>Revoked</dt>
          <dd>{readiness.posture_counts.revoked}</dd>
        </div>
        <div>
          <dt>Blocked</dt>
          <dd>{readiness.posture_counts.blocked}</dd>
        </div>
        <div>
          <dt>Unknown paid cost</dt>
          <dd>
            {readiness.unknown_paid_cost_requires_approval
              ? "approval required"
              : "blocked posture missing"}
          </dd>
        </div>
        <div>
          <dt>CostGovernor binding</dt>
          <dd>
            {readiness.cost_governor_binding_required
              ? "required"
              : "blocked posture missing"}
          </dd>
        </div>
        <div>
          <dt>Future receipt refs</dt>
          <dd>
            {readiness.future_receipt_refs_required
              ? "required"
              : "receipt posture missing"}
          </dd>
        </div>
        <div>
          <dt>Tiny provider lane</dt>
          <dd>{readiness.tiny_invocation_readiness.status}</dd>
        </div>
        <div>
          <dt>Provider authority</dt>
          <dd>
            {readiness.tiny_invocation_readiness.invocation_enabled
              ? "exact scope required"
              : "No provider authority"}
          </dd>
        </div>
        <div>
          <dt>Redacted receipts</dt>
          <dd>
            {readiness.tiny_invocation_readiness.redacted_receipts_only
              ? "required"
              : "receipt posture missing"}
          </dd>
        </div>
      </dl>
      <div className="note-list" aria-label="Provider credential cost blockers">
        {[
          ...readiness.blocker_codes.slice(0, 8),
          ...readiness.tiny_invocation_readiness.ui_states,
        ].map((code) => (
          <span key={code}>{code}</span>
        ))}
      </div>
    </article>
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

function SetupStepCard({
  step,
  envelope,
}: {
  step: MacOSSetupAssistantStep;
  envelope?: MacOSSetupApprovalEnvelope;
}) {
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
        {step.approvalRequired ? (
          <div>
            <dt>Dry-run envelope</dt>
            <dd>{envelope?.envelopeRef ?? "dry-run envelope pending"}</dd>
          </div>
        ) : null}
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
        {envelope ? (
          <div>
            <dt>Idempotency</dt>
            <dd>{envelope.idempotencyKeyRef}</dd>
          </div>
        ) : null}
      </dl>
      <details>
        <summary>Bounded preview and route refs</summary>
        <div className="setup-detail-block">
          {step.routeRefs.length > 0 ? (
            <>
              <strong>Local prerequisite refs</strong>
              <div className="note-list">
                {step.routeRefs.map((route) => (
                  <span key={route}>{route}</span>
                ))}
              </div>
            </>
          ) : null}
          <strong>Bounded terminal/log preview</strong>
          <p>
            Preview only. Raw logs, raw paths, credentials, prompts,
            transcripts, provider payloads, usernames, hostnames, and
            environment dumps are omitted.
          </p>
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

function ApprovalEnvelopeCard({
  envelope,
}: {
  envelope: MacOSSetupApprovalEnvelope;
}) {
  return (
    <article className="trace-row">
      <div className="review-card-heading">
        <h3>{envelope.setupStepKind}</h3>
        <span>{envelope.status}</span>
      </div>
      <p>{envelope.safeSummary}</p>
      <dl className="metadata-list">
        <div>
          <dt>Envelope ref</dt>
          <dd>{envelope.envelopeRef}</dd>
        </div>
        <div>
          <dt>Approval ref</dt>
          <dd>{envelope.approvalRequestRef}</dd>
        </div>
        <div>
          <dt>Receipt ref</dt>
          <dd>{envelope.expectedReceiptRef}</dd>
        </div>
        <div>
          <dt>Rollback ref</dt>
          <dd>{envelope.rollbackPlanRef}</dd>
        </div>
        <div>
          <dt>Side effect class</dt>
          <dd>{envelope.sideEffectClass}</dd>
        </div>
        <div>
          <dt>Next safe action</dt>
          <dd>{envelope.operatorNextAction}</dd>
        </div>
      </dl>
      <div className="note-list">
        {envelope.requestedScopeRefs.map((ref) => (
          <span key={ref}>{ref}</span>
        ))}
      </div>
      <ul className="compact-list">
        <li>
          <strong>Not scoped</strong>
          <span>{envelope.notScopedActions.join(", ")}</span>
        </li>
        <li>
          <strong>Blocked runtime authority</strong>
          <span>{envelope.blockedRuntimeAuthority.join(", ")}</span>
        </li>
        <li>
          <strong>Stale-state handling</strong>
          <span>{envelope.staleStateHandling}</span>
        </li>
        <li>
          <strong>Redaction</strong>
          <span>{envelope.redactionSummary}</span>
        </li>
      </ul>
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
