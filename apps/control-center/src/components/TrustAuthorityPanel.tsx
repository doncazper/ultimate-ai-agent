import type {
  TrustAuthorityCapabilityCatalogEntry,
  TrustAuthorityDomainCoverage,
  TrustAuthorityLane,
  TrustAuthorityMatrix,
  TrustAuthorityState,
} from "../api/types";

interface TrustAuthorityPanelProps {
  matrix: TrustAuthorityMatrix;
  authoritative: boolean;
}

export function TrustAuthorityPanel({
  authoritative,
  matrix,
}: TrustAuthorityPanelProps) {
  const compatibilityRows = authoritative ? matrix.lanes : [];
  const availableRows = compatibilityRows.filter(
    (capability) => capability.authority_state === "available_now",
  );
  const approvalRows = compatibilityRows.filter(
    (capability) => capability.authority_state === "approval_required",
  );
  const plannedRows = compatibilityRows.filter(
    (capability) => capability.authority_state === "planned",
  );
  const blockedRows = compatibilityRows.filter(
    (capability) => capability.authority_state === "blocked",
  );
  const fallbackCompatibilityRefs = matrix.lanes.map((lane) => lane.lane_ref);
  const domainCoverageRows = authoritative ? matrix.authority_domain_coverage : [];
  const capabilityRows = authoritative ? matrix.authority_capability_catalog : [];
  return (
    <section className="page-section" aria-labelledby="trust-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Authority by tier</p>
          <h2 id="trust-heading">Trust</h2>
        </div>
        <span className="status-pill compact">
          {authoritative ? matrix.status : "mock fallback"}
        </span>
      </div>

      <div className="hero-panel">
        <div>
          <p className="eyebrow">
            {authoritative ? "Repo-safe authority map" : "Fallback posture only"}
          </p>
          <h3>
            {authoritative
              ? matrix.doctrine
              : "Reconnect to the local backend before relying on Trust"}
          </h3>
          <p className="muted">
            {authoritative
              ? matrix.operator_summary
              : "Mock fallback data is non-authoritative; no authority capability is available until Python Core returns the backend-owned Trust matrix."}
          </p>
        </div>
        <div className="detail-grid compact">
          <DetailTerm label="Route" value={matrix.route_ref} />
          <DetailTerm label="CLI" value={matrix.cli_ref} />
          <DetailTerm
            label="Control Center grants authority"
            value={matrix.control_center_grants_authority ? "yes" : "no"}
          />
          <DetailTerm
            label="Production authority"
            value={matrix.production_authority_enabled ? "enabled" : "blocked"}
          />
        </div>
      </div>

      <div className="metric-grid">
        <MetricCard
          label="Available now"
          tone="green"
          value={authoritative ? String(matrix.available_now_lane_refs.length) : "0"}
        />
        <MetricCard
          label="Needs approval"
          tone="orange"
          value={
            authoritative ? String(matrix.approval_required_lane_refs.length) : "0"
          }
        />
        <MetricCard
          label="Planned"
          tone="blue"
          value={authoritative ? String(matrix.planned_lane_refs.length) : "0"}
        />
        <MetricCard
          label="Blocked"
          tone="blue"
          value={
            authoritative
              ? String(matrix.blocked_lane_refs.length)
              : String(fallbackCompatibilityRefs.length)
          }
        />
      </div>

      <div className="stacked-list" aria-label="Usable authority tiers">
        {(authoritative ? matrix.tier_summaries : []).map((tier) => (
          <article className="list-card" key={tier.tier_id}>
            <div className="list-card-header">
              <div>
                <strong>
                  Tier {tier.tier}: {tier.label}
                </strong>
                <p>{tier.operator_summary}</p>
              </div>
              <span className="status-pill compact">
                {tier.available_now_count} now
              </span>
            </div>
          </article>
        ))}
      </div>

      <DomainCoveragePanel rows={domainCoverageRows} />

      <CapabilityCatalogPanel rows={capabilityRows} />

      <div className="two-column-grid">
        <CapabilityColumn
          capabilities={availableRows}
          title={authoritative ? "Available Now" : "Fallback Capabilities Hidden"}
          tone="available"
        />
        <CapabilityColumn
          capabilities={approvalRows}
          title="Requires Approval"
          tone="approval"
        />
      </div>
      <div className="two-column-grid">
        <CapabilityColumn
          capabilities={plannedRows}
          title="Planned"
          tone="planned"
        />
        <CapabilityColumn
          capabilities={blockedRows}
          title="Blocked"
          tone="blocked"
        />
      </div>
      {!authoritative ? (
        <div className="panel-card">
          <h3>Mock Fallback Compatibility Refs</h3>
          <p className="muted">
            These refs show fallback shape only. Python Core must return the
            Trust read model before any capability can be treated as enabled,
            approval-ready, planned, or blocked product truth.
          </p>
          <RefList refs={fallbackCompatibilityRefs} />
        </div>
      ) : null}

      <div className="two-column-grid">
        <div className="panel-card">
          <h3>Proof And Verifiers</h3>
          <RefList
            refs={authoritative ? [...matrix.proof_refs, ...matrix.verifier_refs] : []}
          />
        </div>
        <div className="panel-card">
          <h3>Blocked Authority</h3>
          <RefList refs={authoritative ? matrix.blocked_authority_refs : []} />
        </div>
      </div>
      <p className="muted">
        {authoritative
          ? matrix.next_safe_action
          : "Reconnect to the local backend before using Trust to choose a next safe action."}
      </p>
    </section>
  );
}

function CapabilityCatalogPanel({
  rows,
}: {
  rows: TrustAuthorityCapabilityCatalogEntry[];
}) {
  return (
    <div className="panel-card" aria-label="AuthorityLease capability catalog">
      <div className="list-card-header">
        <div>
          <h3>AuthorityLease Capability Catalog</h3>
          <p>
            Legacy Trust rows are projected into governed mode, domain, and
            capability entries. Unknown authority stays denied; an active lease
            is required before non-read effects.
          </p>
        </div>
        <span className="status-pill compact">{rows.length} capabilities</span>
      </div>
      <div className="stacked-list compact">
        {rows.map((row) => (
          <article className="list-card compact" key={row.catalog_ref}>
            <div className="list-card-header">
              <div>
                <strong>{row.label}</strong>
                <p>{row.safe_summary}</p>
              </div>
              <span className="status-pill compact">
                {formatTrustLabel(row.authority_state)}
              </span>
            </div>
            <div className="detail-grid compact">
              <DetailTerm
                label="Capability"
                value={formatAuthorityRef(row.authority_capability_ref)}
              />
              <DetailTerm
                label="Domain"
                value={formatAuthorityRef(row.authority_domain_ref)}
              />
              <DetailTerm
                label="Mode"
                value={formatTrustLabel(row.required_authority_mode)}
              />
              <DetailTerm
                label="Lease"
                value={row.active_lease_required ? "required" : "missing"}
              />
              <DetailTerm
                label="Policy"
                value={
                  row.authority_state_decision_outcome
                    ? formatTrustLabel(row.authority_state_decision_outcome)
                    : "unmapped"
                }
              />
              <DetailTerm
                label="State"
                value={
                  row.authority_state_status
                    ? formatTrustLabel(row.authority_state_status)
                    : "unmapped"
                }
              />
              <DetailTerm
                label="Unknown"
                value={row.unknown_authority_denied ? "denied" : "allowed"}
              />
              <DetailTerm
                label="Execution"
                value={row.execution_claimed ? "claimed" : "not claimed"}
              />
            </div>
            {row.authority_state_operator_message ? (
              <p className="muted">{row.authority_state_operator_message}</p>
            ) : null}
            <RefGroup
              title="Catalog and source"
              refs={[row.catalog_ref, row.source_lane_ref]}
            />
            <RefGroup
              title="AuthorityState decision"
              refs={[
                row.authority_state_catalog_ref,
                row.authority_state_mapping_ref,
                row.authority_state_decision_ref,
                ...row.authority_state_reason_refs,
              ].filter((ref): ref is string => Boolean(ref))}
            />
            <RefGroup
              title="Unsupported adapters"
              refs={row.unsupported_adapter_refs}
            />
            <RefGroup
              title="AuthorityLease requirement"
              refs={[
                row.authority_lease_requirement_ref,
                row.authority_domain_ref,
                row.authority_capability_ref,
              ]}
            />
            <RefGroup
              title="CLI, proof, and verifiers"
              refs={[...row.cli_inspection_refs, ...row.proof_refs, ...row.verifier_refs]}
            />
            <RefGroup
              title="Safe-disable and rollback"
              refs={[...row.safe_disable_refs, ...row.rollback_refs]}
            />
            {row.blocked_authority_refs.length > 0 ? (
              <RefGroup
                title="Blocked authority"
                refs={row.blocked_authority_refs}
              />
            ) : null}
          </article>
        ))}
        {rows.length === 0 ? <p className="muted">none</p> : null}
      </div>
    </div>
  );
}

function DomainCoveragePanel({ rows }: { rows: TrustAuthorityDomainCoverage[] }) {
  return (
    <div className="panel-card" aria-label="AuthorityLease domain coverage">
      <div className="list-card-header">
        <div>
          <h3>AuthorityLease Domain Coverage</h3>
          <p>
            Domain capabilities are governed by the Python Core AuthorityState
            map. Known authority still requires an active lease; unsupported
            adapters stay planned unsupported or blocked.
          </p>
        </div>
        <span className="status-pill compact">{rows.length} domains</span>
      </div>
      <div className="stacked-list compact">
        {rows.map((row) => (
          <article className="list-card compact" key={row.domain_ref}>
            <div className="list-card-header">
              <div>
                <strong>{row.label}</strong>
                <p>{row.operator_summary}</p>
              </div>
              <span className="status-pill compact">
                {formatTrustLabel(row.status)}
              </span>
            </div>
            <div className="detail-grid compact">
              <DetailTerm label="Domain" value={formatAuthorityRef(row.domain_ref)} />
              <DetailTerm
                label="Known"
                value={row.known_authority ? "yes" : "denied"}
              />
              <DetailTerm label="Mappings" value={String(row.mapping_count)} />
              <DetailTerm
                label="Implemented"
                value={String(row.implemented_mapping_count)}
              />
              <DetailTerm label="Partial" value={String(row.partial_mapping_count)} />
              <DetailTerm label="Planned" value={String(row.planned_mapping_count)} />
              <DetailTerm
                label="Hidden refs"
                value={String(row.hidden_mapping_ref_count)}
              />
              <DetailTerm
                label="Lease"
                value={row.active_lease_required ? "required" : "missing"}
              />
            </div>
            <RefGroup
              title="AuthorityState route and CLI"
              refs={[row.authority_state_route_ref, row.authority_state_cli_ref]}
            />
            <RefGroup title="Visible mappings" refs={row.visible_mapping_refs} />
            <RefGroup
              title="Unsupported adapters"
              refs={row.unsupported_adapter_refs}
            />
          </article>
        ))}
        {rows.length === 0 ? <p className="muted">none</p> : null}
      </div>
    </div>
  );
}

function CapabilityColumn({
  capabilities,
  title,
  tone,
}: {
  capabilities: TrustAuthorityLane[];
  title: string;
  tone: "available" | "approval" | "planned" | "blocked";
}) {
  return (
    <div className="panel-card">
      <h3>{title}</h3>
      <div className="stacked-list compact">
        {capabilities.map((capability) => (
          <article className="list-card compact" key={capability.lane_ref}>
            <div className="list-card-header">
              <div>
                <strong>{capability.label}</strong>
                <p>{capability.current_posture}</p>
              </div>
              <span className="status-pill compact">
                {capability.authority_state_label ||
                  stateLabel(capability.authority_state)}
              </span>
            </div>
            <div className="detail-grid compact">
              <DetailTerm
                label="Tier"
                value={`${capability.tier}: ${capability.tier_label}`}
              />
              <DetailTerm
                label="Capability kind"
                value={formatTrustLabel(capability.lane_kind)}
              />
              <DetailTerm
                label="Posture"
                value={formatTrustLabel(capability.operator_posture)}
              />
              <DetailTerm
                label="Lease mode"
                value={formatTrustLabel(capability.required_authority_mode)}
              />
              <DetailTerm
                label="Domain"
                value={formatAuthorityRef(capability.authority_domain_ref)}
              />
              <DetailTerm
                label="Capability"
                value={formatAuthorityRef(capability.authority_capability_ref)}
              />
              <DetailTerm
                label="Approval"
                value={
                  capability.requires_exact_approval
                    ? "exact required"
                    : "not required"
                }
              />
              <DetailTerm
                label="Safe disable"
                value={
                  capability.requires_safe_disable ? "required" : "not required"
                }
              />
              <DetailTerm
                label="Rollback"
                value={
                  capability.requires_rollback_posture
                    ? "posture required"
                    : capability.rollback_execution_enabled
                      ? "execution enabled"
                      : "execution blocked"
                }
              />
            </div>
            <p className="muted">{capability.operator_can_do_now}</p>
            <p className="muted">{capability.approval_posture}</p>
            <p className="muted">{capability.next_safe_action}</p>
            <RefGroup
              title="Routes and proof"
              refs={[...capability.route_refs, ...capability.proof_refs]}
            />
            <RefGroup
              title="CLI and verifiers"
              refs={[
                ...capability.cli_inspection_refs,
                ...capability.verifier_refs,
              ]}
            />
            <RefGroup
              title="Safe-disable and rollback"
              refs={[...capability.safe_disable_refs, ...capability.rollback_refs]}
            />
            <RefGroup
              title="AuthorityLease requirement"
              refs={authorityLeaseRequirementRefs(capability)}
            />
            <RefGroup
              title="Capability path"
              refs={capability.promotion_path_refs}
            />
            {tone === "blocked" || capability.blocked_authority_refs.length > 0 ? (
              <RefGroup
                title="Blocked authority"
                refs={capability.blocked_authority_refs}
              />
            ) : null}
          </article>
        ))}
        {capabilities.length === 0 ? <p className="muted">none</p> : null}
      </div>
    </div>
  );
}

function stateLabel(state: TrustAuthorityState): string {
  return state.replaceAll("_", " ");
}

function formatTrustLabel(value: string | undefined): string {
  return (value ?? "unknown").replaceAll("_", " ");
}

function formatAuthorityRef(value: string | undefined): string {
  return (value ?? "authority-domain-ref:unknown")
    .replace(/^authority-(domain|capability)-ref:/, "")
    .replaceAll("_", " ");
}

function authorityLeaseRequirementRefs(lane: TrustAuthorityLane): string[] {
  return [
    lane.authority_lease_requirement_ref ??
      "authority-lease-requirement-ref:unknown",
    lane.authority_domain_ref ?? "authority-domain-ref:unknown",
    lane.authority_capability_ref ?? "authority-capability-ref:unknown",
  ];
}

function DetailTerm({ label, value }: { label: string; value: string }) {
  return (
    <div className="detail-term">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function MetricCard({
  label,
  tone,
  value,
}: {
  label: string;
  tone: "blue" | "green" | "orange";
  value: string;
}) {
  return (
    <div className={`metric-card ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function RefList({ refs }: { refs: string[] }) {
  if (refs.length === 0) {
    return <p className="muted">none</p>;
  }
  return (
    <ul className="ref-list compact">
      {refs.slice(0, 10).map((ref, index) => (
        <li key={`${ref}-${index}`}>{ref}</li>
      ))}
    </ul>
  );
}

function RefGroup({ refs, title }: { refs: string[]; title: string }) {
  return (
    <div className="compact-stack">
      <p className="muted">{title}</p>
      <RefList refs={refs} />
    </div>
  );
}
