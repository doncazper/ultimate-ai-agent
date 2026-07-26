import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  fetchControlCenterSettingsStatus,
  fetchFounderActionsInbox,
  fetchFounderMemoryReview,
  recordManualMemoryCandidate,
  recordMemoryReviewDecision,
  revokeAuthorityLease,
  submitActionDecision,
} from "../api/client";
import { useBackendTruthMutationBinding } from "../backendTruthMutationBinding";
import type {
  ControlCenterData,
  ControlCenterSettingsStatus,
  FounderLoopActionDecisionKind,
  FounderLoopActionDecisionReceipt,
  FounderLoopActionsInbox,
  FounderLoopMemoryReview,
  MemoryReviewDecisionKind,
  MemoryReviewDecisionReceipt,
  ManualMemoryCandidateReceipt,
  TrustAuthorityState,
} from "../api/types";
import { Avatar, Badge, Button, Icon, MetaRow, Panel, SearchField, Tabs, Toolbar } from "./primitives";
import { WORKSPACE_PREFIX, workspaceNavItems } from "./model";

const newsItems = [
  { icon: "scale" as const, tone: "purple", title: "AI policy outlook shifts", source: "Source A · 2h", summary: "New guidance narrows the focus on frontier safety standards while expanding support for state-led AI initiatives." },
  { icon: "chart-line" as const, tone: "green", title: "Market and funding pulse", source: "Source B · 4h", summary: "Early-stage AI software funding holds steady while enterprise budgets remain selective." },
  { icon: "shield-check" as const, tone: "orange", title: "Security product bulletin", source: "Bulletin source · 7h", summary: "Patch advisory for privilege escalation in identity connectors; mitigations and timeline included." },
  { icon: "building-2" as const, tone: "blue", title: "Customer industry update", source: "Source C · 8h", summary: "Customer-sector organizations are accelerating planning for automation and document workflows." },
];

export function NewsSurface({ data }: { data: ControlCenterData }) {
  const [selected, setSelected] = useState(0);
  const [tab, setTab] = useState("For You");
  const [query, setQuery] = useState("");
  const [topic, setTopic] = useState("Morning brief");
  const visibleItems = newsItems.filter((item) => `${item.title} ${item.source} ${item.summary}`.toLowerCase().includes(query.trim().toLowerCase()));
  const article = visibleItems[selected] ?? visibleItems[0];
  const source = data.founderSourceReadiness.source_readiness_items.find((item) => item.source_kind.toLowerCase().includes("news"));
  return (
    <div className="ns-surface ns-news">
      <Toolbar title="News" subtitle="Synthetic desktop fixture · no news retrieval occurred">
        <SearchField onChange={(value) => { setQuery(value); setSelected(0); }} placeholder="Search preview news and briefings" value={query} /><Button disabled title="Topic filters are represented by the local topic list">All topics</Button><Button disabled title="No source freshness filter contract is connected">Last 24 hours</Button><a className="ns-button primary" href={`${WORKSPACE_PREFIX}/decisions`}>Review {data.founderActionsInbox.items.length} decisions</a>
      </Toolbar>
      <Tabs active={tab} items={["For You", "Business", "Technology", "Markets", "Saved", "Sources"]} onChange={setTab} />
      <div className="ns-news-layout">
        <aside className="ns-news-topics">
          {["Morning brief", "Your business", "Relationship watchlist", "AI & policy", "Security", "Funding", "Saved"].map((item, index) => <button className={topic === item ? "active" : ""} key={item} onClick={() => setTopic(item)} type="button"><Icon name={["sun", "building-2", "users", "scale", "shield-check", "badge-dollar-sign", "bookmark"][index] as Parameters<typeof Icon>[0]["name"]} size={19} /><span><strong>{item}</strong><small>Fixture topic</small></span><Badge tone="neutral">Fixture</Badge></button>)}
          <Button disabled icon="settings" title="No durable interest-preference contract is connected">Manage interests</Button>
        </aside>
        <section className="ns-news-feed">
          {visibleItems.map((item, index) => <article className={selected === index ? "selected" : ""} key={item.title}><button aria-label={`Select ${item.title}`} onClick={() => setSelected(index)} type="button"><span className={`ns-news-art tone-${item.tone}`}><Icon name={item.icon} size={30} /></span><span><h2>{item.title}</h2><small>{item.source}</small><p>{item.summary}</p><em><Icon name="target" size={13} /> Preview selection · {topic}</em></span></button><Button disabled title="No governed source-opening contract is connected">Open source</Button></article>)}
          {visibleItems.length === 0 ? <p className="ns-help-copy">No preview article matches this search.</p> : null}
        </section>
        <aside className="ns-news-inspector">
          {article ? <>
          <Panel title="Briefing context" icon="info">
            <strong>Why this is here</strong><p>Synthetic render fixture; it is not based on operator interests or activity.</p>
            <div className="ns-tag-list"><Badge tone="neutral">AI policy watchlist</Badge><Badge tone="neutral">Policy & regulation</Badge><Badge tone="neutral">AI & policy</Badge></div>
          </Panel>
          <Panel title="Relationship & business links"><MetaRow icon="table-2" label="Work Board" value="AI Policy monitor" /><MetaRow icon="users" label="CRM" value="Policy partner tracking" /><MetaRow icon="calendar" label="Calendar" value="Regulatory briefings" /></Panel>
          <Panel title={article.title}><MetaRow icon="circle-check" label="Backend source posture" value={source?.status.replaceAll("_", " ") ?? "missing"} tone={source?.status === "ready" ? "green" : "orange"} /><MetaRow icon="clock" label="Fixture freshness" value="Illustrative only" /><MetaRow icon="shield-check" label="Runtime authority" value="None" tone="green" /><div className="ns-grid-actions"><Button disabled title="No governed source-opening contract is connected">Open source</Button><Button disabled icon="bookmark" title="No durable saved-news contract is connected">Save for later</Button><Button disabled icon="message-square" title="No news-to-agent handoff contract is connected">Ask UAA</Button><Button disabled icon="eye-off" title="No durable source preference contract is connected">Mute source</Button></div></Panel>
          </> : <p className="ns-help-copy">No fixture is selected.</p>}
        </aside>
      </div>
      <div className="ns-receipt-band"><Icon name="shield-check" size={18} tone="warning" /> Synthetic news fixture · Backend source posture: {source?.status.replaceAll("_", " ") ?? "missing"} · No source retrieved, opened, or saved</div>
    </div>
  );
}

const memoryDecisionOptions: Array<{ kind: MemoryReviewDecisionKind; label: string }> = [
  { kind: "accept", label: "Accept as reviewed context" },
  { kind: "correct", label: "Correct" },
  { kind: "reject", label: "Exclude" },
  { kind: "defer", label: "Defer" },
];

const memoryDecisionRequiredRefFields = [
  "actor_ref",
  "source_refs",
  "provenance_refs",
  "evidence_refs",
  "stale_state",
  "retention_posture",
  "audit_refs",
  "receipt_refs",
  "blocked_state_refs",
];

export function KnowledgeSurface({ data }: { data: ControlCenterData }) {
  const mutationBinding = useBackendTruthMutationBinding();
  const [review, setReview] = useState<FounderLoopMemoryReview>(data.founderMemoryReview);
  const [decision, setDecision] = useState<MemoryReviewDecisionKind>("correct");
  const [selected, setSelected] = useState(0);
  const [correction, setCorrection] = useState("");
  const [noteOpen, setNoteOpen] = useState(false);
  const [noteTitle, setNoteTitle] = useState("");
  const [noteSummary, setNoteSummary] = useState("");
  const [noteReceipt, setNoteReceipt] = useState<ManualMemoryCandidateReceipt>();
  const [pending, setPending] = useState(false);
  const [receipt, setReceipt] = useState<MemoryReviewDecisionReceipt>();
  const [feedback, setFeedback] = useState("No knowledge decision recorded yet.");
  useEffect(() => {
    setReview(data.founderMemoryReview);
    setSelected(0);
    setReceipt(undefined);
    setFeedback("No knowledge decision recorded yet.");
  }, [data.founderMemoryReview]);
  const reviewAuthoritative = data.connection.state === "online"
    && !data.connection.usingMockData
    && data.routeStates["/memory"]?.state === "backend_owned"
    && review.safe_refs_only
    && !review.raw_content_stored
    && !review.context_injection_authorized
    && !review.connector_write_authorized
    && !review.external_crm_sync_authorized
    && !review.automatic_action_execution_authorized
    && !review.production_authority_enabled
    && review.idempotency_replay_enabled
    && review.idempotency_conflict_rejected
    && review.route_ref === "GET /control-center/memory/review"
    && review.contract_ref === "contract-ref:control-center-memory-review:v1"
    && review.legacy_decision_contract_ref === "contract-ref:fcc-v1-005-memory-review-decisions:v1"
    && review.decision_route_refs.length > 0;
  const candidate = review.items[selected];
  const candidateAuthoritative = Boolean(
    reviewAuthoritative
    && candidate?.safe_summary_only
    && candidate.source_refs.length > 0
    && candidate.provenance_refs.length > 0
    && candidate.evidence_refs.length > 0
    && candidate.source_policy_ref === "contract-ref:memory-source-provenance:v1"
    && candidate.source_refs_status === "safe_source_refs_present"
    && candidate.provenance_refs_status === "safe_provenance_refs_present"
    && candidate.source_review_required
    && candidate.source_trust_posture === "untrusted_until_reviewed"
    && candidate.decision_contract_ref === "contract-ref:memory-review-decision:v1"
    && sameSafeRefs(candidate.decision_required_ref_fields, memoryDecisionRequiredRefFields)
    && candidate.decision_actor_ref === "actor-ref:local-operator-review-required"
    && candidate.decision_source_provenance_contract_ref === "contract-ref:memory-source-provenance:v1"
    && candidate.decision_source_trust_posture === "untrusted_until_reviewed"
    && candidate.decision_redaction_status === "redacted_summary_only"
    && candidate.decision_audit_refs.length > 0
    && candidate.decision_receipt_refs.length > 0
    && candidate.decision_blocked_state_refs.length > 0
    && candidate.decision_review_only
    && !candidate.source_truth_authority
    && !candidate.memory_write_authorized
    && !candidate.automatic_memory_write_authorized
    && !candidate.context_injection_authorized
    && !candidate.connector_runtime_allowed
    && !candidate.provider_or_model_authority_allowed
    && !candidate.accepted_as_truth
    && !candidate.memory_delete_authorized
    && !candidate.memory_export_authorized
    && !candidate.retention_execution_authorized
    && !candidate.production_authority_enabled
    && !candidate.source_payload_storage_allowed
    && !candidate.prompt_body_storage_allowed
    && !candidate.response_body_storage_allowed
    && !candidate.provider_body_storage_allowed
    && !candidate.path_body_storage_allowed
    && !candidate.log_body_storage_allowed
    && !candidate.account_ref_storage_allowed
    && !candidate.private_content_storage_allowed
    && candidate.business_memory_safe_refs_only
    && candidate.business_memory_review_required_before_recall
    && !candidate.business_memory_write_authorized
    && !candidate.business_memory_delete_authorized
    && !candidate.business_memory_export_authorized
    && !candidate.business_memory_crm_write_authorized
    && !candidate.business_memory_account_sync_authorized
    && !candidate.business_memory_context_injection_authorized
  );
  const availableDecisions = new Set(candidate?.available_decision_states ?? review.decision_kinds);

  async function saveDecision() {
    if (!candidateAuthoritative || !candidate || !availableDecisions.has(decision) || (decision === "correct" && !correction.trim())) return;
    setPending(true);
    try {
      const candidateRef = candidate.business_memory_candidate_ref || candidate.review_ref;
      const recorded = await recordMemoryReviewDecision(
        candidateRef,
        decision,
        {
          reviewer_ref: "actor-ref:northstar-memory-review",
          corrected_summary_ref: decision === "correct" ? `safe-summary-ref:northstar-memory-correction:${candidate.review_ref.replace(/[^a-zA-Z0-9_.@-]+/g, "-")}` : undefined,
          corrected_safe_summary: decision === "correct" ? correction.trim() : undefined,
          source_refs: candidate.source_refs,
          evidence_refs: candidate.evidence_refs,
          metadata_refs: [`metadata-ref:northstar-memory-review:${decision}`, candidate.review_ref],
          blocked_state_refs: review.blocked_state_refs,
        },
        mutationBinding,
      );
      setReceipt(recorded);
      setFeedback(`${recorded.replayed ? "Replayed" : "Recorded"} ${decision} receipt · ${recorded.receipt_ref}.`);
      try {
        const refreshed = await fetchFounderMemoryReview();
        setReview(refreshed);
        const nextIndex = refreshed.items.findIndex((item) => item.review_ref === candidate.review_ref);
        setSelected(nextIndex >= 0 ? nextIndex : 0);
        setFeedback(`${recorded.replayed ? "Replayed" : "Recorded"} ${decision} receipt · ${recorded.receipt_ref}. Backend queue refreshed.`);
      } catch (refreshError) {
        setFeedback(`${recorded.replayed ? "Replayed" : "Recorded"} ${decision} receipt · ${recorded.receipt_ref}. Refresh pending: ${refreshError instanceof Error ? refreshError.message : "backend queue unavailable"}`);
      }
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : "Memory Review decision receipt was not recorded safely.");
    } finally {
      setPending(false);
    }
  }

  async function addManualNote() {
    if (!reviewAuthoritative || !noteTitle.trim() || !noteSummary.trim()) return;
    setPending(true);
    try {
      const recorded = await recordManualMemoryCandidate(
        {
          candidate_kind: "operator_note",
          title: noteTitle.trim(),
          safe_summary: noteSummary.trim(),
          priority: "medium",
          reviewer_ref: "actor-ref:northstar-memory-review",
          source_refs: ["source-ref:northstar-manual-note"],
          provenance_refs: ["provenance-ref:northstar-manual-note"],
          missing_evidence_refs: ["missing-evidence-ref:northstar-manual-note"],
          tag_refs: ["tag-ref:manual-memory-candidate"],
          blocked_state_refs: ["blocked-state-ref:no-automatic-memory-write", "blocked-state-ref:no-context-injection"],
        },
        mutationBinding,
      );
      setNoteReceipt(recorded);
      setNoteOpen(false);
      setNoteTitle("");
      setNoteSummary("");
      setFeedback(`Manual review candidate recorded · ${recorded.receipt_ref}. No recall record or memory write was created.`);
      try {
        const refreshed = await fetchFounderMemoryReview();
        setReview(refreshed);
      } catch (refreshError) {
        setFeedback(`Manual review candidate recorded · ${recorded.receipt_ref}. Refresh pending: ${refreshError instanceof Error ? refreshError.message : "backend queue unavailable"}`);
      }
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : "Manual review candidate was not recorded safely.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="ns-surface ns-knowledge">
      <Toolbar title="Knowledge" subtitle="Reviewed memory, files, and context with provenance"><SearchField placeholder="Search is not connected to the backend review queue" /><Badge tone={reviewAuthoritative ? "green" : "orange"}>{reviewAuthoritative ? "Backend-owned" : "Preview"}</Badge><Button disabled={!reviewAuthoritative || pending} onClick={() => setNoteOpen((open) => !open)} title={reviewAuthoritative ? "Create a review candidate only; no memory write" : "Backend-owned Memory Review is required"}>{noteOpen ? "Close note" : "Add local note"}</Button><a className="ns-button primary" href={`${WORKSPACE_PREFIX}/decisions`}>Review {data.founderActionsInbox.items.length} decisions</a></Toolbar>
      <Tabs active="Memory" items={["Memory"]} />
      {noteOpen ? <form className="ns-board-create" onSubmit={(event) => { event.preventDefault(); void addManualNote(); }}><label>Note title<input autoFocus maxLength={120} onChange={(event) => setNoteTitle(event.target.value)} required value={noteTitle} /></label><label>Bounded safe summary<textarea maxLength={500} onChange={(event) => setNoteSummary(event.target.value)} required value={noteSummary} /></label><p className="ns-help-copy">Creates a backend review candidate only. It does not create a recall record, write memory, inject context, or contact a connector.</p><Button disabled={pending || !noteTitle.trim() || !noteSummary.trim()} tone="primary" type="submit">{pending ? "Recording…" : "Record review candidate"}</Button><Button onClick={() => setNoteOpen(false)}>Cancel</Button></form> : null}
      <div className="ns-knowledge-layout">
        <aside className="ns-review-queue">
          <header><strong>Review queue</strong><Icon name="list-filter" size={16} /></header>
          <small>Backend review items <Badge tone={review.items.length > 0 ? "orange" : "neutral"}>{review.items.length}</Badge></small>
          {review.items.map((item, index) => <button className={selected === index ? "active" : ""} key={item.review_ref} onClick={() => { setSelected(index); setCorrection(""); setReceipt(undefined); setNoteReceipt(undefined); setFeedback(item.next_safe_action); }} type="button"><Icon name="file-text" size={17} /><span><strong>{item.title}</strong><small>{item.source_kind} · {item.priority}</small></span><Badge tone={item.review_state.includes("conflict") ? "red" : item.stale_state.includes("stale") ? "neutral" : "blue"}>{item.review_state}</Badge></button>)}
          {review.items.length === 0 ? <p className="ns-help-copy">No backend memory items require review.</p> : null}
        </aside>
        <section className="ns-knowledge-detail">
          {candidate ? <>
          <header><Icon name="file-text" size={22} /><h2>{candidate.title}</h2><Badge tone="blue">{candidate.candidate_kind}</Badge></header>
          <blockquote>{candidate.safe_summary}</blockquote>
          <strong>Proposed use</strong><p>{candidate.next_safe_action}</p>
          <strong>Related safe references</strong><div className="ns-reference-grid">{candidate.source_refs.slice(0, 4).map((sourceRef, index) => <div className="ns-reference-card" key={sourceRef}><Icon name={index % 2 ? "link" : "file-text"} size={17} /><span><strong>Source ref {index + 1}</strong><small>{sourceRef}</small></span></div>)}</div>
          <strong>Provenance timeline</strong><div className="ns-provenance">{candidate.provenance_refs.slice(0, 4).map((sourceRef, index) => <div key={sourceRef}><span /><small>Provenance {index + 1}</small><p><strong>{sourceRef}</strong><br />Safe reference from the backend review model.</p></div>)}</div>
          <div className="ns-info-callout"><Icon name="info" size={18} tone="info" /><span><strong>Memory is recall, not truth</strong><small>Knowledge is proposed from sources and may be incomplete or outdated.</small></span></div>
          </> : <div className="ns-empty-lease"><Icon name="circle-check" size={34} tone="success" /><h3>Review queue is clear</h3><p>No backend-owned memory candidate is selected.</p></div>}
        </section>
        <aside className="ns-review-decision">
          <header><h2>Review decision</h2>{candidate ? <Badge tone="orange">Unsaved draft</Badge> : <Badge tone="neutral">No selection</Badge>}</header>
          {candidate ? <><strong>Why this is shown</strong><p>{candidate.correction_posture}</p>
          <MetaRow icon="clock" label="Stale posture" value={candidate.stale_state} tone={candidate.stale_state.includes("stale") ? "orange" : "green"} /><MetaRow icon="signal" label="Confidence" value={candidate.confidence_posture} tone="orange" /><MetaRow icon="triangle-alert" label="Review state" value={candidate.review_state} tone={candidate.review_state.includes("conflict") ? "red" : "blue"} />
          <strong>Your decision · local draft</strong>{memoryDecisionOptions.map((option) => <label className="ns-radio-row" key={option.kind}><input checked={decision === option.kind} disabled={!availableDecisions.has(option.kind)} onChange={() => setDecision(option.kind)} type="radio" /> {option.label}</label>)}
          {decision === "correct" ? <textarea aria-label="Correction" onChange={(event) => setCorrection(event.target.value)} value={correction} /> : null}
          <Button disabled={!candidateAuthoritative || pending || !availableDecisions.has(decision) || (decision === "correct" && !correction.trim())} onClick={() => void saveDecision()} tone="primary">{pending ? "Recording…" : `Record ${decision} receipt`}</Button>
          {!candidateAuthoritative ? <p className="ns-help-copy">A complete backend-owned, safe-ref-only Memory Review item is required before decisions can be recorded.</p> : null}</> : <p className="ns-help-copy">No decision is available.</p>}
        </aside>
      </div>
      <div aria-live="polite" className="ns-receipt-band"><Icon name={receipt || noteReceipt ? "receipt-text" : "loader-circle"} size={18} /> {feedback}</div>
    </div>
  );
}

export function ActivityTrustSurface({ data }: { data: ControlCenterData }) {
  const mutationBinding = useBackendTruthMutationBinding();
  const matrix = data.trustAuthorityMatrix;
  const [settings, setSettings] = useState<ControlCenterSettingsStatus>(data.settingsStatus);
  const [selectedLeaseRef, setSelectedLeaseRef] = useState(() => data.settingsStatus.authority_lease_state.active_leases.find((lease) => lease.status === "active" && lease.mode !== "read_only")?.lease_ref ?? "");
  const [confirmationLeaseRef, setConfirmationLeaseRef] = useState<string>();
  const [revoking, setRevoking] = useState(false);
  const [feedback, setFeedback] = useState(matrix.operator_summary);
  useEffect(() => {
    setSettings(data.settingsStatus);
    setSelectedLeaseRef((current) => data.settingsStatus.authority_lease_state.active_leases.some((lease) => lease.lease_ref === current && lease.status === "active" && lease.mode !== "read_only") ? current : data.settingsStatus.authority_lease_state.active_leases.find((lease) => lease.status === "active" && lease.mode !== "read_only")?.lease_ref ?? "");
    setConfirmationLeaseRef(undefined);
    setFeedback(data.trustAuthorityMatrix.operator_summary);
  }, [data.settingsStatus, data.trustAuthorityMatrix]);
  const liveBackend = data.connection.state === "online" && !data.connection.usingMockData;
  const backendOwned = liveBackend && data.routeStates["/trust"]?.state === "backend_owned" && matrix.backend_owned && matrix.local_read_model_only && matrix.safe_refs_only && !matrix.control_center_grants_authority;
  const settingsAuthoritative = liveBackend && data.routeStates["/settings"]?.state === "backend_owned" && settings.authority_lease_state.backend_owned;
  const elevatedActiveLeases = settings.authority_lease_state.active_leases.filter((lease) => lease.status === "active" && lease.mode !== "read_only");
  const activeLease = elevatedActiveLeases.find((lease) => lease.lease_ref === selectedLeaseRef);
  const canRevoke = Boolean(settingsAuthoritative && activeLease);
  const confirmRevoke = Boolean(confirmationLeaseRef);
  const tierColumns = [...matrix.tier_summaries].sort((left, right) => left.tier - right.tier);
  const recentDecisions = settings.authority_lease_state.sample_decisions.slice(0, 8);

  async function revokeActiveLease() {
    if (!canRevoke || !activeLease) return;
    if (!confirmationLeaseRef) {
      setConfirmationLeaseRef(activeLease.lease_ref);
      setFeedback(`Confirm revocation of exact lease ${activeLease.lease_ref}.`);
      return;
    }
    const exactLease = settings.authority_lease_state.active_leases.find((lease) => lease.lease_ref === confirmationLeaseRef && lease.status === "active" && lease.mode !== "read_only");
    if (!exactLease || confirmationLeaseRef !== selectedLeaseRef || activeLease.lease_ref !== confirmationLeaseRef) {
      setConfirmationLeaseRef(undefined);
      setFeedback("Lease selection or active posture changed before confirmation. Revocation was not sent.");
      return;
    }
    setRevoking(true);
    try {
      const result = await revokeAuthorityLease(
        {
          lease_ref: exactLease.lease_ref,
          decision_reason_ref: "reason-ref:northstar-authority-revoke",
          safe_summary:
            "Control Center revoked the exact active authority lease after operator confirmation.",
        },
        mutationBinding,
      );
      setConfirmationLeaseRef(undefined);
      setFeedback(`Lease revoked · ${result.receipt.receipt_ref}. Refreshing authority state.`);
      try {
        const refreshed = await fetchControlCenterSettingsStatus(
          mutationBinding,
        );
        setSettings(refreshed);
        setFeedback(`Lease revoked · ${result.receipt.receipt_ref}. Authority state refreshed.`);
      } catch (refreshError) {
        setFeedback(`Lease revoked · ${result.receipt.receipt_ref}. Refresh pending: ${refreshError instanceof Error ? refreshError.message : "authority state unavailable"}`);
      }
    } catch (error) {
      setConfirmationLeaseRef(undefined);
      setFeedback(error instanceof Error ? error.message : "Authority lease revoke receipt was not recorded safely.");
    } finally {
      setRevoking(false);
    }
  }
  return (
    <div className="ns-surface ns-trust">
      <Toolbar title="Trust" subtitle="Authority, leases, policy, and safe-disable"><SearchField placeholder="Search domains or decisions" /><a className="ns-button primary" href={`${WORKSPACE_PREFIX}/decisions`}>Review {data.founderActionsInbox.items.length} decisions</a><Button disabled tone="danger" icon="octagon-alert" title="Kill-switch status is read-only; this surface has no mutation handler or exact request contract">Kill switch unavailable</Button></Toolbar>
      <Tabs active="Trust" items={["Trust"]} />
      <div className="ns-trust-layout">
        <Panel className="ns-authority-matrix" title="Mode / domain authority matrix" icon="info">
          <div className="ns-trust-legend"><span><i className="green" /> Allow</span><span><i className="orange" /> Ask</span><span><i className="red" /> Deny</span><span><i className="gray" /> Planned</span></div>
          <table><thead><tr><th>Domain</th>{tierColumns.map((tier) => <th key={tier.tier_id} title={tier.label}>{shortAuthorityTierLabel(tier.label)}</th>)}</tr></thead><tbody>{matrix.authority_domain_coverage.map((domain) => <tr key={domain.domain_ref}><td title={domain.operator_summary}>{domain.label}</td>{tierColumns.map((tier) => { const lane = matrix.lanes.find((candidate) => candidate.authority_domain_ref === domain.domain_ref && candidate.tier === tier.tier); return <td key={tier.tier_id} title={lane?.current_posture ?? "No backend mapping for this domain and tier"}><AuthorityStateIcon state={lane?.authority_state ?? "planned"} /></td>; })}</tr>)}</tbody></table>
          <p>This matrix reports {backendOwned ? "backend-owned" : "preview-only"} truth and cannot grant authority.</p>
        </Panel>
        <Panel className="ns-lease-detail" title="Lease detail">
          {activeLease ? <div className="ns-selected-item"><Badge tone="orange">Active exact lease</Badge>{elevatedActiveLeases.length > 1 ? <label>Select exact lease<select aria-label="Select exact active lease" onChange={(event) => { setSelectedLeaseRef(event.target.value); setConfirmationLeaseRef(undefined); }} value={selectedLeaseRef}>{elevatedActiveLeases.map((lease) => <option key={lease.lease_ref} value={lease.lease_ref}>{lease.lease_ref}</option>)}</select></label> : null}<h3>{activeLease.mode.replaceAll("_", " ")}</h3><MetaRow icon="file-text" label="Lease ref" value={activeLease.lease_ref} /><MetaRow icon="clock" label="Expires" value={activeLease.expires_at} /><MetaRow icon="shield-check" label="Scope" value={activeLease.scope} /></div> : <div className="ns-empty-lease"><Icon name="clock" size={34} /><h3>No active elevated lease</h3><p>All authority requires an exact lease with scoped capabilities, time window, and constraints.</p><Button disabled title="Lease requests are planned in a separate exact approval flow">Review lease request</Button></div>}
          <hr /><strong>Ask if · examples</strong><ul><li>Modify files outside allowed workspace</li><li>Create or send external communications</li><li>Launch external actions or model calls</li></ul>
          <strong>Hard deny</strong><ul className="danger"><li>Arbitrary terminal or script execution</li><li>Install or modify system software</li><li>Access production or external networks</li></ul>
        </Panel>
        <Panel className="ns-live-decisions" title="Live policy decisions" action={<a className="ns-button secondary" href={`${WORKSPACE_PREFIX}/decisions`}><Icon name="activity" size={16} /> View review queue</a>}>
          {recentDecisions.map((decision) => <div key={decision.decision_ref}><Icon name={decision.outcome === "allow" ? "folder" : decision.outcome === "ask" ? "calendar" : "terminal"} size={18} /><span><strong>{decision.action_ref}</strong><small>{decision.operator_message}</small></span><Badge tone={decision.outcome === "allow" ? "green" : decision.outcome === "ask" || decision.outcome === "degrade_to_draft" ? "orange" : "red"}>{decision.outcome.replaceAll("_", " ")}</Badge><code>{decision.decision_ref}</code><time>{decision.decided_at}</time></div>)}
          {recentDecisions.length === 0 ? <p className="ns-help-copy">No backend policy decisions are currently reported.</p> : null}
        </Panel>
      </div>
      <div className="ns-emergency-actions"><EmergencyCard busy={revoking} confirming={confirmRevoke} disabled={!canRevoke} tone="red" icon="shield-alert" title="Revoke lease" button={revoking ? "Revoking…" : confirmRevoke ? "Confirm revoke" : "Revoke lease"} onAction={() => void revokeActiveLease()} onCancel={() => { setConfirmationLeaseRef(undefined); setFeedback("Lease revocation cancelled; authority state is unchanged."); }} /><EmergencyCard disabled tone="orange" icon="circle-pause" title="Pause activity" button="Unavailable" /><EmergencyCard disabled tone="red" icon="octagon-alert" title="Kill switch" button="Unavailable" /><EmergencyCard disabled tone="blue" icon="shield-check" title="Safe-disable posture" button="Read-only status" /></div>
      <div aria-live="polite" className="ns-receipt-band"><Icon name={canRevoke ? "shield-check" : "lock"} size={18} /> {feedback}</div>
    </div>
  );
}

function shortAuthorityTierLabel(label: string) {
  return label.replace(/local read\/?preview/i, "Read").replace(/draft\/?proposal/i, "Draft").replace(/reversible local mutation/i, "Local mutate").replace(/external mutation/i, "External").replace(/background standing authority/i, "Standing");
}

function AuthorityStateIcon({ state }: { state: TrustAuthorityState }) {
  if (state === "available_now") return <Icon name="circle-check" size={14} tone="success" />;
  if (state === "approval_required") return <Icon name="circle-alert" size={14} tone="warning" />;
  if (state === "blocked") return <Icon name="circle-minus" size={14} tone="danger" />;
  return <Icon name="circle" size={14} />;
}

function EmergencyCard({ busy = false, button, confirming = false, disabled = false, icon, onAction, onCancel, title, tone }: { busy?: boolean; button: string; confirming?: boolean; disabled?: boolean; icon: Parameters<typeof Icon>[0]["name"]; onAction?: () => void; onCancel?: () => void; title: string; tone: string }) {
  return <section className={`ns-emergency-card ${tone}`}><Icon name={icon} size={30} /><span><strong>{title}</strong><p>{disabled ? "Backend contract unavailable · no action performed" : confirming ? "Confirm the exact lease revocation; a receipt will be recorded" : "Exact scope · confirmation required · receipt recorded"}</p><div className="ns-inline-actions"><Button disabled={disabled || busy} onClick={onAction} tone={tone === "red" ? "danger" : "secondary"}>{button}</Button>{confirming ? <Button disabled={busy} onClick={onCancel}>Cancel</Button> : null}</div></span></section>;
}

export function CustomizeSurface() {
  const [density, setDensity] = useState("Comfortable");
  const [visible, setVisible] = useState(() => new Set(workspaceNavItems.map((item) => item.id)));
  const toggle = (id: (typeof workspaceNavItems)[number]["id"]) => setVisible((current) => { const next = new Set(current); if (next.has(id)) next.delete(id); else next.add(id); return next; });
  const restoreDefaults = () => { setDensity("Comfortable"); setVisible(new Set(workspaceNavItems.map((item) => item.id))); };
  return (
    <div className="ns-surface ns-customize"><Toolbar title="Customize" subtitle="Preview navigation visibility without changing capability"><Button onClick={restoreDefaults}>Cancel draft</Button><Button onClick={restoreDefaults}>Restore defaults</Button><Button disabled title="No durable layout-preference contract is connected" tone="primary">Save layout unavailable</Button></Toolbar><div className="ns-customize-layout"><Panel title="Navigation visibility"><p>Toggle items for this live preview. Reordering is not implemented.</p><div className="ns-customize-list">{workspaceNavItems.map((item) => <div key={item.id}><Icon name="eye" size={16} /><Icon name={item.icon} size={18} /><strong>{item.label}</strong><small>{item.section === "primary" ? "Daily workspace" : "Supporting utility"}</small><input aria-label={`Show ${item.label} in sidebar`} checked={visible.has(item.id)} disabled={item.id === "today"} onChange={() => toggle(item.id)} type="checkbox" /></div>)}</div></Panel><Panel title="Live preview"><div className="ns-sidebar-preview"><strong>Control Center</strong>{workspaceNavItems.filter((item) => visible.has(item.id)).map((item) => <span key={item.id}><Icon name={item.icon} size={17} /> {item.label}</span>)}</div><div className="ns-preview-controls"><strong>Density</strong><div className="ns-segmented">{["Compact", "Comfortable"].map((item) => <button className={density === item ? "active" : ""} key={item} onClick={() => setDensity(item)} type="button">{item}</button>)}</div><Panel title="What customization changes" icon="info"><p>Local preview visibility and density only.</p></Panel><Panel title="What it never changes" icon="lock"><p>Routes, capability, approvals, authority rules, safeguards, or durable preferences.</p></Panel></div></Panel></div><div className="ns-receipt-band"><Icon name="info" size={18} /> {workspaceNavItems.length - visible.size} local preview changes · Nothing saved <Button onClick={restoreDefaults}>Undo draft</Button><Button disabled title="No durable layout-preference contract is connected" tone="primary">Save unavailable</Button></div></div>
  );
}

export function SettingsSurface({ data }: { data: ControlCenterData }) {
  const [category, setCategory] = useState("General");
  const [density, setDensity] = useState("Comfortable");
  const status = data.settingsStatus;
  const routeBacked = data.routeStates["/settings"]?.state === "backend_owned" && status.authority_lease_state.backend_owned;
  const categories = ["General", "Appearance", "Notifications", "Communications", "Calendar", "Studio", "Privacy & Authority", "Data & Storage", "Integrations", "Accessibility", "Advanced"];
  const postureItems = status.authority_postures;
  const showAuthority = category === "Privacy & Authority" || category === "Integrations" || category === "Advanced";
  return (
    <div className="ns-surface ns-settings">
      <Toolbar title="Settings" subtitle="Read-only backend posture and local presentation preferences">
        <Badge tone={routeBacked ? "green" : "orange"}>{routeBacked ? "Backend-owned status" : "Preview"}</Badge>
        <Button disabled title="The backend settings status explicitly disables settings mutation">Review changes unavailable</Button>
      </Toolbar>
      <div className="ns-settings-layout">
        <aside>{categories.map((item, index) => <button className={category === item ? "active" : ""} key={item} onClick={() => setCategory(item)} type="button"><Icon name={["settings", "shapes", "bell", "mail", "calendar", "sparkles", "shield-check", "database", "plug", "user-check", "sliders-horizontal"][index] as Parameters<typeof Icon>[0]["name"]} size={18} /> {item}</button>)}</aside>
        <section>
          {category === "General" || category === "Appearance" ? <>
            <Panel title="Application presentation">
              <SettingRow icon="house" label="Launch surface" help="No writable backend preference contract yet"><select defaultValue="Today" disabled><option>Today</option></select></SettingRow>
              <SettingRow icon="list-filter" label="Density" help="Local presentation preview; it does not change authority or backend state"><div className="ns-segmented">{["Compact", "Comfortable"].map((item) => <button className={density === item ? "active" : ""} key={item} onClick={() => setDensity(item)} type="button">{item}</button>)}</div></SettingRow>
              <SettingRow icon="monitor" label="Theme" help="No writable backend preference contract yet"><select defaultValue="System" disabled><option>System</option></select></SettingRow>
              <SettingRow icon="clock" label="Start-of-day time" help="No writable backend preference contract yet"><input defaultValue="8:00 AM" disabled /></SettingRow>
              <SettingRow icon="cloud-sun" label="Weather location" help="No source-backed weather settings contract"><strong>Missing contract</strong></SettingRow>
            </Panel>
            <Panel title="Backend settings status"><MetaRow icon="shield-check" label="Status" value={status.status.replaceAll("_", " ")} /><MetaRow icon="lock" label="Settings mutation" value={status.settings_mutation_enabled ? "Enabled" : "Disabled"} tone={status.settings_mutation_enabled ? "orange" : "green"} /><MetaRow icon="octagon-alert" label="Kill-switch mutation" value={status.kill_switch_mutation_enabled ? "Enabled" : "Disabled"} tone={status.kill_switch_mutation_enabled ? "orange" : "green"} /><MetaRow icon="plug" label="Provider configuration" value={status.provider_configuration_enabled ? "Enabled" : "Blocked"} tone={status.provider_configuration_enabled ? "orange" : "green"} /></Panel>
          </> : showAuthority ? <Panel title={`${category} posture`}>{postureItems.map((posture) => <div className="ns-setting-posture" key={posture.posture_ref}><Icon name={posture.state_label === "Blocked" ? "lock" : "shield-check"} size={19} /><span><strong>{posture.label}</strong><small>{posture.safe_summary}</small></span><Badge tone={posture.state_label === "Blocked" ? "red" : posture.state_label === "Partial" || posture.state_label === "Degraded" ? "orange" : "neutral"}>{posture.state_label}</Badge></div>)}</Panel> : <Panel title={category}><div className="ns-empty-lease"><Icon name="lock" size={34} /><h3>Read-only status only</h3><p>No writable backend contract exists for this settings category. No change is simulated in React state.</p></div></Panel>}
        </section>
        <aside className="ns-settings-inspector">
          <Panel title="Backend contract" icon="shield-check"><p>{status.safe_summary}</p><MetaRow icon="file-text" label="Route" value={status.route_ref} /><MetaRow icon="shield-check" label="Authority lease mode" value={status.authority_lease_state.active_mode.replaceAll("_", " ")} /><MetaRow icon="receipt-text" label="Receipts required" value={status.authority_lease_state.receipts_required ? "Yes" : "No"} /><MetaRow icon="lock" label="Unknown authority" value={status.authority_lease_state.unknown_authority_default} /></Panel>
          <Panel title="Current posture"><MetaRow icon="circle-check" label="Source" value={routeBacked ? "Backend owned" : "Preview only"} tone={routeBacked ? "green" : "orange"} /><MetaRow icon="shield" label="Feature flags" value={status.feature_flag_posture.replaceAll("_", " ")} /><MetaRow icon="lock" label="Kill switch" value={status.kill_switch_posture.replaceAll("_", " ")} /></Panel>
        </aside>
      </div>
      <div className="ns-receipt-band"><Icon name="circle-check" size={18} tone={routeBacked ? "success" : "warning"} /> Settings status loaded from {routeBacked ? "the local backend" : "non-authoritative fallback"} · Density is presentation-only · Backend mutation is disabled</div>
    </div>
  );
}

function SettingRow({ children, help, icon, label }: { children: ReactNode; help: string; icon: Parameters<typeof Icon>[0]["name"]; label: string }) { return <div className="ns-setting-row"><Icon name={icon} size={19} /><span><strong>{label}</strong><small>{help}</small></span><div>{children}</div></div>; }

export function DeveloperToolsSurface({ data }: { data: ControlCenterData }) {
  const [tab, setTab] = useState(() => window.location.pathname.endsWith("/terminal") ? "Terminal" : "Runtime");
  if (tab === "Terminal") return <TerminalSurface onBack={() => setTab("Runtime")} />;
  const patch = data.codingPatchApplyReadiness;
  const diagnosticsBackendOwned = data.connection.state === "online"
    && !data.connection.usingMockData
    && data.routeStates["/coding"]?.state === "backend_owned"
    && data.routeStates["/models"]?.state === "backend_owned";
  const runtimeLanes = [
    ["Local read model", data.runtimeReadiness.status, "Read only", data.runtimeReadiness.report_id],
    ["Exact local patch", patch.patch_apply_enabled ? "Enabled" : "Blocked", patch.readiness_only ? "Readiness only" : "Approval required", patch.readiness_ref],
    ["Model invocation", data.runtimeReadiness.real_model_runtime_ready ? "Ready" : "Blocked", "Python Core", "runtime readiness"],
    ["Arbitrary shell", data.codingSession.shell_subprocess_execution_enabled ? "Enabled" : "Blocked", "Exact lane required", data.codingSession.session_ref],
    ["External connector write", data.founderSourceReadiness.write_authority_enabled ? "Enabled" : "Blocked", "Exact lane required", data.founderSourceReadiness.route_ref],
  ];
  const inspectPaths = ["/runtime", "/actions", "/models", "/runtime", "/settings"];
  return <div className="ns-surface ns-developer"><Toolbar title="Developer Tools" subtitle="Technical diagnostics and exact local lanes"><Button disabled icon="refresh-cw" title="Use the canonical runtime route to refresh backend diagnostics">Refresh on canonical route</Button><Button disabled icon="copy" title="No governed clipboard bridge is connected">Copy unavailable</Button><a className="ns-button primary" href={`${WORKSPACE_PREFIX}/decisions`}>Review {data.founderActionsInbox.items.length} decisions</a></Toolbar><Tabs active={tab} items={["Runtime", "Terminal"]} onChange={setTab} /><div className="ns-developer-layout"><section><Panel title="Runtime lanes"><table className="ns-runtime-table"><thead><tr><th>Lane</th><th>State</th><th>Authority</th><th>Backend ref</th><th>Action</th></tr></thead><tbody>{runtimeLanes.map((row, index) => <tr className={index === 1 ? "selected" : ""} key={row[0]}><td><Icon name={index === 0 ? "box" : index === 1 ? "square-pen" : index === 2 ? "zap" : index === 3 ? "terminal" : "plug"} size={17} /> {row[0]}</td><td><Badge tone={String(row[1]).toLowerCase().includes("blocked") ? "red" : String(row[1]).toLowerCase().includes("ready") || row[1] === "Enabled" ? "green" : "orange"}>{row[1]}</Badge></td><td>{row[2]}</td><td>{row[3]}</td><td><a className="ns-button secondary" href={inspectPaths[index]}>Inspect</a></td></tr>)}</tbody></table></Panel><div className="ns-two-panels"><Panel title="Backend checks"><MetaRow icon="shield-check" label="Foundation gate" value={`${data.dashboard.foundation_gate_summary.status} · ${data.dashboard.foundation_gate_summary.passed_count} passed`} tone={data.dashboard.foundation_gate_summary.failed_count ? "orange" : "green"} /><MetaRow icon="triangle-alert" label="Runtime blockers" value={String(data.runtimeReadiness.blockers.length)} tone={data.runtimeReadiness.blockers.length ? "orange" : "green"} /><MetaRow icon="file-check-2" label="Patch prerequisites" value={`${patch.prerequisites.filter((item) => item.status === "present").length}/${patch.prerequisites.length} present`} tone="orange" /></Panel><Panel title="Resource posture"><MetaRow icon="shield-check" label="Foundation readiness signal" value={data.runtimeReadiness.production_ready ? "Reported" : "Not reported"} tone={data.runtimeReadiness.production_ready ? "orange" : "green"} /><MetaRow icon="terminal" label="Shell execution" value={data.codingSession.shell_subprocess_execution_enabled ? "Enabled" : "Blocked"} tone={data.codingSession.shell_subprocess_execution_enabled ? "orange" : "green"} /><MetaRow icon="cloud" label="Connector writes" value={data.founderSourceReadiness.write_authority_enabled ? "Enabled" : "Blocked"} tone={data.founderSourceReadiness.write_authority_enabled ? "orange" : "green"} /></Panel></div></section><aside><Panel title="Selected lane"><Badge tone="orange">{patch.status.replaceAll("_", " ")}</Badge><p>{patch.safe_summary}</p><MetaRow icon="file-text" label="Readiness ref" value={patch.readiness_ref} /><MetaRow icon="file-check-2" label="Prerequisites" value={String(patch.prerequisites.length)} /><MetaRow icon="shield" label="Apply enabled" value={patch.patch_apply_enabled ? "Yes" : "No"} tone={patch.patch_apply_enabled ? "orange" : "green"} /><MetaRow icon="receipt-text" label="Expected receipts" value={String(patch.expected_receipt_refs.length)} /><MetaRow icon="rotate-ccw" label="Rollback refs" value={String(patch.rollback_refs.length)} /><div className="ns-stack-actions"><a className="ns-button secondary" href="/action-preview">Preview lane</a><a className="ns-button primary" href="/actions">Review approval</a><Button disabled icon="copy" title="No governed clipboard bridge is connected">Copy command unavailable</Button></div></Panel></aside></div><div aria-live="polite" className="ns-receipt-band"><Icon name={diagnosticsBackendOwned ? "shield-check" : "triangle-alert"} size={18} tone={diagnosticsBackendOwned ? "success" : "warning"} /> {diagnosticsBackendOwned ? "Backend diagnostics loaded" : "Diagnostics are non-authoritative fallback"} · No command executed · {data.connection.state}</div></div>;
}

function TerminalSurface({ onBack }: { onBack: () => void }) {
  return <div className="ns-surface ns-terminal"><Toolbar title="Developer Tools · Terminal" subtitle="Reference-only command lanes with visible scope"><Button disabled icon="plus" title="No governed terminal-session create contract is wired">New governed session unavailable</Button><a className="ns-button primary" href={`${WORKSPACE_PREFIX}/decisions`}>Review decisions</a></Toolbar><Tabs active="Sessions" items={["Sessions"]} /><div className="ns-terminal-layout"><aside className="ns-session-list"><header><strong>Reference sessions</strong></header>{["UI verification", "Docs checks", "Frontend tests"].map((item, index) => <button className={index === 0 ? "active" : ""} disabled key={item} title="Reference fixture; no selectable terminal session exists" type="button"><strong>{item}</strong><small>Render fixture</small></button>)}</aside><section><div className="ns-terminal-console"><header><strong>UI verification · reference lane</strong><span>No command authority</span></header><code>&gt; npm run typecheck</code><p>Reference output only · no command executed from this surface.</p><code>&gt; docs:verify</code><p>Reference output only · use the canonical CLI inspection path.</p><code>&gt; playwright test --project=desktop</code><p>Reference output only · no test process was started.</p><footer><Icon name="lock" size={14} /> Terminal execution is not wired. Use an approved CLI lane outside this representation.</footer></div><Panel title="Allowed command references" icon="info"><div className="ns-grid-actions"><Button disabled icon="code-2">Typecheck</Button><Button disabled icon="play">Focused tests</Button><Button disabled icon="book-open">Docs verifier</Button><Button disabled icon="git-branch">Git diff check</Button></div></Panel></section><aside><Panel title="Session authority"><MetaRow icon="shield" label="Lane" value="Reference only" /><MetaRow icon="wifi-off" label="Network" value="Denied" /><MetaRow icon="terminal" label="Arbitrary shell" value="Blocked" tone="red" /><MetaRow icon="lock" label="Environment" value="Redacted" /><div className="ns-stack-actions"><Button disabled tone="primary">Review command unavailable</Button><Button tone="quiet" onClick={onBack}>Back to Runtime</Button></div></Panel></aside></div><div className="ns-receipt-band"><Icon name="lock" size={18} /> Not backend-wired · No command executed · No receipt claimed</div></div>;
}

export function DecisionReviewSurface({ data }: { data: ControlCenterData }) {
  const mutationBinding = useBackendTruthMutationBinding();
  const [inbox, setInbox] = useState<FounderLoopActionsInbox>(data.founderActionsInbox);
  const [selected, setSelected] = useState(0);
  const [pending, setPending] = useState<FounderLoopActionDecisionKind>();
  const [receipt, setReceipt] = useState<FounderLoopActionDecisionReceipt>();
  const [feedback, setFeedback] = useState("Select an exact backend action envelope to review.");
  useEffect(() => {
    setInbox(data.founderActionsInbox);
    setSelected(0);
    setReceipt(undefined);
    setFeedback("Select an exact backend action envelope to review.");
  }, [data.founderActionsInbox]);
  const authoritative = data.connection.state === "online" && !data.connection.usingMockData && data.routeStates["/actions"]?.state === "backend_owned";
  const items = inbox.items;
  const item = items[selected];
  const expectedReceiptRefs = item?.action_expected_receipt_refs ?? item?.approval_envelope?.expected_receipt_refs ?? [];
  const exactActionEnvelopeRef = item?.action_envelope_ref;
  const exactApprovalEnvelopeRef = item?.approval_envelope_ref;
  const exactScopeRef = item?.action_scope_ref ?? item?.approval_envelope?.exact_scope;
  const backendEnvelope = Boolean(
    item?.approval_envelope?.backend_owned
    && item.approval_envelope.source === "python_core_action_inbox_read_model"
    && hasNoMissingFieldStates(item.approval_envelope.missing_field_states)
    && item.receipt_visibility?.backend_owned
    && item.receipt_visibility.source === "python_core_action_inbox_read_model"
    && exactActionEnvelopeRef
    && exactApprovalEnvelopeRef
    && exactScopeRef
    && expectedReceiptRefs.length > 0
    && item.approval_envelope.exact_scope === exactScopeRef
    && sameSafeRefs(item.approval_envelope.expected_receipt_refs, expectedReceiptRefs)
  );
  const decisionLaneReadModel = inbox.action_inbox_decision_lane_read_model;
  const decisionLaneItem = decisionLaneReadModel?.items.find((candidate) => candidate.item_ref === item?.item_ref);
  const decisionLane = Boolean(
    decisionLaneReadModel?.contract_ref === "contract-ref:product-loop-005-action-inbox-decision-lanes:v1"
    && inbox.action_inbox_decision_lane_contract_ref === decisionLaneReadModel.contract_ref
    && decisionLaneReadModel.source === "python_core_action_inbox_decision_lane_read_model"
    && decisionLaneReadModel.backend_owned
    && decisionLaneReadModel.local_read_model_only
    && decisionLaneReadModel.safe_refs_only
    && !decisionLaneReadModel.raw_content_included
    && decisionLaneReadModel.missing_envelope_fields_fail_safe
    && decisionLaneReadModel.cost_posture_visible_before_approval
    && decisionLaneReadModel.provider_authority_visible_before_approval
    && decisionLaneReadModel.approval_scope_visible_before_approval
    && decisionLaneReadModel.expected_receipts_visible_before_approval
    && !decisionLaneReadModel.approval_alone_executes
    && !decisionLaneReadModel.action_execution_enabled
    && !decisionLaneReadModel.connector_write_enabled
    && !decisionLaneReadModel.shell_subprocess_execution_enabled
    && !decisionLaneReadModel.browser_execution_enabled
    && !decisionLaneReadModel.provider_model_call_enabled
    && !decisionLaneReadModel.memory_write_enabled
    && !decisionLaneReadModel.context_injection_authorized
    && !decisionLaneReadModel.hidden_memory_write_authorized
    && !decisionLaneReadModel.production_authority_enabled
    && decisionLaneItem?.backend_owned
    && decisionLaneItem.safe_refs_only
    && !decisionLaneItem.raw_content_included
    && decisionLaneItem.lane_id === "needs_approval"
    && decisionLaneItem.approval_required
    && decisionLaneItem.approval_envelope_ref === exactApprovalEnvelopeRef
    && decisionLaneItem.approval_scope_ref === exactScopeRef
    && decisionLaneItem.missing_envelope_field_states.length === 0
    && decisionLaneItem.expected_receipt_refs_visible
    && sameSafeRefs(decisionLaneItem.expected_receipt_refs, expectedReceiptRefs)
    && decisionLaneItem.rollback_ref === (item?.action_rollback_ref ?? item?.rollback_ref)
    && decisionLaneItem.safe_disable_ref === (item?.action_safe_disable_ref ?? item?.safe_disable_ref)
    && decisionLaneItem.cost_blocked_state_refs.length === 0
    && !decisionLaneItem.approval_alone_executes
    && !decisionLaneItem.approval_ref_authority
    && !decisionLaneItem.approval_grants_runtime_authority
    && !decisionLaneItem.action_execution_enabled
    && !decisionLaneItem.connector_write_enabled
    && !decisionLaneItem.shell_subprocess_execution_enabled
    && !decisionLaneItem.browser_execution_enabled
    && !decisionLaneItem.provider_model_call_enabled
    && !decisionLaneItem.memory_write_enabled
    && !decisionLaneItem.context_injection_authorized
    && !decisionLaneItem.hidden_memory_write_authorized
    && !decisionLaneItem.production_authority_enabled
  );
  const canRecord = Boolean(authoritative && inbox.mutating_controls_enabled && inbox.decision_receipts_required && backendEnvelope && decisionLane);
  const availableDecisions = useMemo(() => {
    const allowed = item?.action_review_actions ?? [];
    return allowed.filter((decision): decision is FounderLoopActionDecisionKind => ["approve", "edit", "reject", "defer"].includes(decision));
  }, [item]);
  const costApproved = item ? actionApprovalCostIsReady(item, decisionLaneItem) : false;

  async function recordDecision(decision: FounderLoopActionDecisionKind) {
    if (!item || !canRecord || !availableDecisions.includes(decision) || (decision === "approve" && !costApproved)) return;
    setPending(decision);
    try {
      const recorded = await submitActionDecision(
        item.item_ref,
        decision,
        {
          decision_reason_ref: `decision-reason-ref:northstar-action:${decision}`,
          edited_envelope_ref:
            decision === "edit"
              ? (item.action_envelope_ref ?? item.approval_envelope_ref ?? null)
              : undefined,
          defer_until_ref:
            decision === "defer"
              ? "defer-until-ref:operator-selected-later"
              : undefined,
          metadata_refs: [
            `metadata-ref:northstar-action-decision:${decision}`,
            item.item_ref,
          ],
        },
        mutationBinding,
      );
      setReceipt(recorded);
      setFeedback(`${recorded.replayed ? "Replayed" : "Recorded"} ${decision} receipt · ${recorded.receipt_ref}. Refreshing backend queue.`);
      try {
        const refreshed = await fetchFounderActionsInbox(mutationBinding);
        setInbox(refreshed);
        const nextIndex = refreshed.items.findIndex((candidate) => candidate.item_ref === item.item_ref);
        const refreshedItem = nextIndex >= 0 ? refreshed.items[nextIndex] : undefined;
        const reconciled = Boolean(refreshedItem?.receipt_refs.includes(recorded.receipt_ref) || refreshedItem?.receipt_visibility?.decision_receipt_ref === recorded.receipt_ref);
        setSelected(nextIndex >= 0 ? nextIndex : 0);
        setFeedback(`${recorded.replayed ? "Replayed" : "Recorded"} ${decision} receipt · ${recorded.receipt_ref}. ${reconciled ? "Backend read model reconciled." : "Backend reconciliation is still pending."}`);
      } catch (refreshError) {
        setFeedback(`${recorded.replayed ? "Replayed" : "Recorded"} ${decision} receipt · ${recorded.receipt_ref}. Refresh pending: ${refreshError instanceof Error ? refreshError.message : "backend queue unavailable"}`);
      }
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : "Action decision receipt was not recorded safely.");
    } finally {
      setPending(undefined);
    }
  }

  return <div className="ns-surface ns-decisions"><Toolbar title={`Review ${items.length} decisions`} subtitle="Record only the exact decision the action envelope communicates"><Badge tone={authoritative ? "green" : "orange"}>{authoritative ? "Backend-owned" : "Preview"}</Badge><Button disabled>Filter: All</Button><Button disabled>Sort: Backend order</Button></Toolbar><div className="ns-decision-layout"><aside className="ns-decision-list"><header><h2>Action inbox ({items.length})</h2><p>Backend-classified review queue</p></header>{items.map((candidate, index) => <button className={selected === index ? "active" : ""} key={candidate.item_ref} onClick={() => { setSelected(index); setReceipt(undefined); setFeedback(candidate.next_safe_action); }} type="button"><Icon name={candidate.surface.toLowerCase().includes("memory") ? "book-open" : candidate.surface.toLowerCase().includes("plan") ? "table-2" : "scale"} size={18} /><span><small>{candidate.action_group_label ?? candidate.surface}</small><strong>{candidate.title}</strong><span><Badge tone={candidate.priority === "high" || candidate.priority === "critical" ? "red" : "orange"}>{candidate.priority}</Badge><Badge tone={candidate.risk_class === "low" ? "green" : candidate.risk_class === "high" ? "red" : "orange"}>{candidate.risk_class}</Badge></span><em>{candidate.status.replaceAll("_", " ")}</em></span><Icon name="chevron-right" size={15} /></button>)}{items.length === 0 ? <p className="ns-help-copy">No backend action item is waiting for review.</p> : null}</aside><section className="ns-decision-detail">{item ? <><header><Icon name="scale" size={22} /><h2>{item.title}</h2><Badge tone={item.approval_required ? "orange" : "neutral"}>{item.approval_required ? "Approval required" : "Review only"}</Badge></header><div className="ns-source-line">{item.surface} · {item.item_ref}</div><Panel title="Safe summary"><p>{item.safe_summary}</p></Panel><div className="ns-decision-facts"><MetaRow icon="target" label="Exact scope" value={item.action_scope_ref ?? item.approval_envelope?.exact_scope ?? "Missing"} /><MetaRow icon="shield-check" label="Authority boundary" value={item.authority_boundary} /><MetaRow icon="activity" label="Side effects" value={item.side_effect_class} /><MetaRow icon="receipt-text" label="Expected receipts" value={item.action_expected_receipt_refs?.length ?? item.receipt_refs.length} /></div><Panel title="Backend action envelope"><MetaRow icon="file-text" label="Envelope" value={item.action_envelope_ref ?? item.approval_envelope_ref ?? "Missing"} /><MetaRow icon="clock" label="Expiry / stale" value={item.action_expires_at ?? item.expires_at ?? item.stale_state} /><MetaRow icon="rotate-ccw" label="Rollback" value={item.action_rollback_ref ?? item.rollback_ref ?? "Missing"} /><MetaRow icon="shield-check" label="Safe disable" value={item.action_safe_disable_ref ?? item.safe_disable_ref ?? "Missing"} /></Panel><Panel title="Decision effect"><p>These controls record a decision receipt through Python Core. Approval alone does not execute the action unless the returned receipt explicitly reports execution.</p></Panel><div className="ns-decision-actions">{(["reject", "defer", "edit", "approve"] as FounderLoopActionDecisionKind[]).map((decision) => <Button disabled={!canRecord || !availableDecisions.includes(decision) || Boolean(pending) || (decision === "approve" && !costApproved)} icon={decision === "approve" ? "shield-check" : decision === "reject" ? "shield-alert" : decision === "defer" ? "clock" : "pencil"} key={decision} onClick={() => void recordDecision(decision)} title={decision === "approve" && !costApproved ? "Approval is blocked by the backend cost posture" : !canRecord ? "Authoritative backend envelope and decision lane required" : undefined} tone={decision === "approve" ? "primary" : decision === "reject" ? "danger" : "secondary"}>{pending === decision ? "Recording…" : `Record ${decision}`}</Button>)}</div></> : <div className="ns-empty-lease"><Icon name="circle-check" size={34} tone="success" /><h3>Action inbox is clear</h3><p>No exact decision is selected.</p></div>}</section><aside className="ns-decision-inspector"><Panel title="Authority & consequences" icon="shield-check">{item ? <><MetaRow icon="target" label="Queue group" value={item.action_group_label ?? item.action_group_id ?? "Unclassified"} /><MetaRow icon="lock" label="Backend envelope" value={backendEnvelope ? "Verified" : "Unavailable"} tone={backendEnvelope ? "green" : "red"} /><MetaRow icon="activity" label="Decision lane" value={decisionLane ? "Eligible" : "Read-only"} tone={decisionLane ? "green" : "orange"} /><MetaRow icon="receipt-text" label="Receipt required" value={inbox.decision_receipts_required ? "Yes" : "No"} /><MetaRow icon="badge-dollar-sign" label="Cost gate" value={costApproved ? "Cost approved" : "Approval blocked"} tone={costApproved ? "green" : "orange"} /><div className="ns-info-callout"><Icon name="info" size={17} /><span>{item.next_safe_action}</span></div></> : <p>No item selected.</p>}</Panel><Panel title="Activity" icon="activity"><p>{feedback}</p>{receipt ? <><MetaRow icon="receipt-text" label="Receipt" value={receipt.receipt_ref} /><MetaRow icon="shield-check" label="Decision" value={receipt.decision} /><MetaRow icon="activity" label="Action executed" value={receipt.action_executed ? "Yes" : "No"} tone={receipt.action_executed ? "orange" : "green"} /></> : null}</Panel><Panel title="Receipts" icon="receipt-text"><p>{receipt ? receipt.safe_summary : "A backend receipt appears here after a supported decision is recorded."}</p></Panel></aside></div><div aria-live="polite" className="ns-receipt-band"><Icon name={receipt ? "receipt-text" : "shield-check"} size={18} /> {feedback}</div></div>;
}

function sameSafeRefs(left: string[], right: string[]): boolean {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}

function hasNoMissingFieldStates(states: string[]): boolean {
  return states.length === 0 || (states.length === 1 && states[0] === "none");
}

function actionApprovalCostIsReady(
  item: FounderLoopActionsInbox["items"][number],
  laneItem: NonNullable<FounderLoopActionsInbox["action_inbox_decision_lane_read_model"]>["items"][number] | undefined,
) {
  if (!laneItem || !laneItem.cost_telemetry_complete || laneItem.cost_blocked_state_refs.length > 0) return false;
  const envelope = item.approval_envelope;
  const state = item.action_envelope_cost_state_label ?? envelope?.cost_state_label;
  const estimated = item.action_envelope_estimated_cost_usd ?? envelope?.estimated_cost_usd;
  const maximum = item.action_envelope_max_approved_cost_usd ?? envelope?.max_approved_cost_usd;
  const receipts = item.action_envelope_cost_receipt_refs ?? envelope?.cost_receipt_refs ?? [];
  const blockedRefs = item.action_envelope_cost_blocked_state_refs ?? envelope?.cost_blocked_state_refs ?? [];
  const providerRef = item.action_envelope_provider_ref ?? envelope?.provider_ref ?? null;
  const modelProfileRef = item.action_envelope_model_profile_ref ?? envelope?.model_profile_ref ?? null;
  const inputUnits = item.action_envelope_input_metered_units ?? envelope?.input_metered_units ?? 0;
  const outputUnits = item.action_envelope_output_metered_units ?? envelope?.output_metered_units ?? 0;
  const totalUnits = item.action_envelope_total_metered_units ?? envelope?.total_metered_units ?? 0;
  const costEstimateRef = item.action_envelope_cost_estimate_ref ?? envelope?.cost_estimate_ref ?? null;
  const capturedUsageRef = item.action_envelope_captured_usage_ref ?? envelope?.captured_usage_ref ?? null;
  const budgetDecisionRef = item.action_envelope_budget_decision_ref ?? envelope?.budget_decision_ref ?? null;
  const providerAuthorityState = item.action_envelope_provider_authority_state_label ?? envelope?.provider_authority_state_label;
  const unknownPaidCost = item.action_envelope_unknown_paid_cost_requires_explicit_approval ?? envelope?.unknown_paid_cost_requires_explicit_approval ?? true;
  const frontierUsage = item.action_envelope_frontier_usage_claimed ?? envelope?.frontier_usage_claimed ?? false;
  const paidOrMetered = Boolean(frontierUsage || (estimated ?? 0) > 0 || totalUnits > 0);
  return state === "Cost approved"
    && laneItem.cost_state_label === state
    && typeof estimated === "number"
    && typeof maximum === "number"
    && estimated >= 0
    && estimated <= maximum
    && laneItem.estimated_cost_usd === estimated
    && laneItem.max_approved_cost_usd === maximum
    && laneItem.provider_ref === providerRef
    && laneItem.model_profile_ref === modelProfileRef
    && laneItem.input_metered_units === inputUnits
    && laneItem.output_metered_units === outputUnits
    && laneItem.total_metered_units === totalUnits
    && laneItem.cost_estimate_ref === costEstimateRef
    && laneItem.captured_usage_ref === capturedUsageRef
    && laneItem.budget_decision_ref === budgetDecisionRef
    && laneItem.provider_authority_state_label === providerAuthorityState
    && laneItem.unknown_paid_cost_requires_explicit_approval === unknownPaidCost
    && laneItem.frontier_usage_claimed === frontierUsage
    && sameSafeRefs(laneItem.cost_receipt_refs, receipts)
    && sameSafeRefs(laneItem.cost_blocked_state_refs, blockedRefs)
    && receipts.length > 0
    && (!paidOrMetered || (
      !unknownPaidCost
      && laneItem.provider_model_refs_present
      && isKnownCostRef(costEstimateRef)
      && isKnownCostRef(capturedUsageRef)
      && isKnownCostRef(budgetDecisionRef)
    ));
}

function isKnownCostRef(value: string | null): value is string {
  return Boolean(value && !["missing", "unknown", "planned", "not_applicable"].includes(value));
}
