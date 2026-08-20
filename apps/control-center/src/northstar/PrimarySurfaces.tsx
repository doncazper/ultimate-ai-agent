import { useState } from "react";
import type { ControlCenterData } from "../api/types";
import { Avatar, Badge, Button, Icon, MetaRow, Panel, SearchField, Tabs, Toolbar } from "./primitives";
import { WORKSPACE_PREFIX } from "./model";

export function TodaySurface({ data }: { data: ControlCenterData }) {
  const today = data.founderToday;
  const backendOwned = data.connection.state === "online"
    && !data.connection.usingMockData
    && data.routeStates["/today"]?.state === "backend_owned";
  const actionCount = today.sections.action_inbox_count;
  const briefingItems = today.briefing_items.slice(0, 3);
  const attention = today.actions.slice(0, 5);
  const plans = today.plans.slice(0, 3);
  const evidenceCount = today.evidence_timeline.length;
  const [selectedAttentionRef, setSelectedAttentionRef] = useState(
    attention[0]?.item_ref ?? "",
  );
  const selectedAttention =
    attention.find((item) => item.item_ref === selectedAttentionRef) ?? attention[0];
  return (
    <div className="ns-surface ns-today">
      <Toolbar title="Today" subtitle="Your local founder loop">
        <a className="ns-button primary" href={`${WORKSPACE_PREFIX}/decisions`}>
          <Icon name="scale" size={17} /> Review {actionCount} decisions
        </a>
      </Toolbar>
      <div className="ns-today-grid">
        <Panel title="Morning Briefing" icon="sun" action={<Badge tone={backendOwned ? "green" : "orange"}>{backendOwned ? "Current" : "Preview only"}</Badge>}>
          <div className="ns-list roomy">
            {briefingItems.map((item, index) => <ListRow detail={item.safe_summary} icon={index === 1 ? "triangle-alert" : index === 2 ? "file-text" : "target"} key={item.briefing_ref} title={item.title} />)}
            {briefingItems.length === 0 ? <p className="ns-help-copy">No briefing items are ready yet.</p> : null}
          </div>
          <a className="ns-panel-link" href="/briefing">Open briefing <Icon name="external-link" size={13} /></a>
        </Panel>
        <Panel title="Needs your attention" icon="bell">
          <div className="ns-list attention-list">
            {attention.map((item) => <ListRow ariaLabel={`Show ${item.title}`} badge={item.approval_required ? "Approval required" : item.status} detail={item.safe_summary} icon="scale" key={item.item_ref} onSelect={() => setSelectedAttentionRef(item.item_ref)} selected={selectedAttention?.item_ref === item.item_ref} title={item.title} tone={item.approval_required ? "orange" : "blue"} />)}
            {attention.length === 0 ? <p className="ns-help-copy">Nothing needs your attention right now.</p> : null}
          </div>
          <a className="ns-panel-link" href={`${WORKSPACE_PREFIX}/decisions`}>Review all {actionCount}</a>
        </Panel>
        <Panel title="Why this matters" icon="info">
          {selectedAttention ? <div className="ns-selected-item">
            <small>{selectedAttention.surface} · selected from Needs your attention</small>
            <h3>{selectedAttention.title}</h3>
            <p>{selectedAttention.safe_summary}</p>
            <MetaRow icon="globe-2" label="Evidence" value={`${selectedAttention.evidence_refs.length} safe refs`} tone="green" />
            <MetaRow icon="shield-check" label="What can happen" value={selectedAttention.authority_boundary} />
            <MetaRow icon="clock" label="Next safe step" value={selectedAttention.next_safe_action} />
            <div className="ns-inline-actions">
              <a href={`${WORKSPACE_PREFIX}/work-board`}>Open Work Board</a>
              <Button disabled title="No exact Day Plan mutation contract is connected">Add to Day Plan</Button>
              <Button disabled tone="quiet" icon="message-square" title="No Today-to-assistant handoff contract is connected">Ask UAA</Button>
            </div>
          </div> : <p className="ns-help-copy">Select an attention item when the backend reports one.</p>}
        </Panel>
        <Panel title="Day Plan" icon="calendar-check">
          <div className="ns-plan-context"><Badge tone={backendOwned ? "green" : "orange"}>{backendOwned ? "Current" : "Preview only"}</Badge> <Badge tone="neutral">Plans</Badge> {today.sections.plan_count}</div>
          <div className="ns-list compact">
            {plans.map((plan, index) => <NumberedRow active={index === 0} key={plan.plan_ref} number={index + 1} text={plan.title} />)}
            {plans.length === 0 ? <p className="ns-help-copy">No plans are scheduled for today.</p> : null}
          </div>
          <a className="ns-panel-link" href={`${WORKSPACE_PREFIX}/work-board`}>Open full plan</a>
        </Panel>
        <Panel title="News" icon="newspaper" action={<Badge tone="neutral">Source required</Badge>}>
          <p className="ns-help-copy">No sourced news items are attached to the Today read model.</p>
          <a className="ns-panel-link" href={`${WORKSPACE_PREFIX}/news`}>View sourced brief</a>
        </Panel>
        <Panel title="Business pulse" icon="activity">
          <p className="ns-help-copy">No backend-owned business metrics are attached to the Today read model.</p>
          <a className="ns-panel-link" href={`${WORKSPACE_PREFIX}/activity-trust`}>View business pulse</a>
        </Panel>
      </div>
      <div className="ns-receipt-band"><Icon name="circle-check" size={18} tone={backendOwned ? "success" : "warning"} /> <strong>{backendOwned ? "Since your last check" : "Preview only"}</strong> · {evidenceCount} evidence updates · {today.sections.memory_review_count} memory reviews <a href={`${WORKSPACE_PREFIX}/activity-trust`}>View activity</a></div>
    </div>
  );
}

function ListRow({
  ariaLabel,
  badge,
  detail,
  icon,
  onSelect,
  selected = false,
  title,
  tone = "blue",
}: {
  ariaLabel?: string;
  badge?: string;
  detail?: string;
  icon: Parameters<typeof Icon>[0]["name"];
  onSelect?: () => void;
  selected?: boolean;
  title: string;
  tone?: "blue" | "orange" | "red" | "green";
}) {
  const content = (
    <>
      <Icon name={icon} size={18} />
      <span><strong>{title}</strong>{detail ? <small>{detail}</small> : null}</span>
      {badge ? <Badge tone={tone}>{badge}</Badge> : null}
    </>
  );
  return onSelect ? (
    <button
      aria-label={ariaLabel}
      aria-pressed={selected}
      className={`ns-list-row ns-list-row-button ${selected ? "selected" : ""}`}
      onClick={onSelect}
      type="button"
    >
      {content}
    </button>
  ) : <div className="ns-list-row">{content}</div>;
}

function NumberedRow({ active, number, text }: { active?: boolean; number: number; text: string }) {
  return (
    <div className={`ns-numbered-row ${active ? "active" : ""}`}>
      <span>{number}</span><strong>{text}</strong>{active ? <Button disabled tone="quiet" title="No exact task execution contract is connected">Start</Button> : null}<Icon name="ellipsis" size={15} />
    </div>
  );
}

const messages = [
  { initials: "R", tone: "purple" as const, source: "Relationship Alpha", subject: "Customer kickoff timing", preview: "Hi Alex, thanks for the great discussion...", time: "10:24 AM" },
  { initials: "#", tone: "teal" as const, source: "#sales-updates", subject: "Weekly pipeline update", preview: "Here’s the latest snapshot...", time: "9:47 AM" },
  { initials: "ML", tone: "blue" as const, source: "Morgan Lee", subject: "Re: Product demo feedback", preview: "Thanks for the demo yesterday...", time: "8:31 AM" },
  { initials: "DL", tone: "gray" as const, source: "Devon Lane", subject: "Contract review status", preview: "Checking in on the latest draft...", time: "Yesterday" },
];

export function CommunicationsSurface({ data }: { data: ControlCenterData }) {
  const [tab, setTab] = useState("Unified");
  const [selected, setSelected] = useState(0);
  const [query, setQuery] = useState("");
  const sourcePosture = data.founderSourceReadiness.source_readiness_posture;
  const visibleMessages = messages.filter((item) => `${item.source} ${item.subject} ${item.preview}`.toLowerCase().includes(query.trim().toLowerCase()));
  const message = visibleMessages[selected] ?? visibleMessages[0];
  return (
    <div className="ns-surface ns-communications">
      <Toolbar title="Communications" subtitle="Synthetic desktop fixture · no account messages are connected">
        <SearchField onChange={setQuery} placeholder="Search preview communications" value={query} />
        <Button disabled icon="filter" title="No backend message-filter contract is connected">Filters</Button>
        <a className="ns-button primary" href={`${WORKSPACE_PREFIX}/decisions`}><Icon name="scale" size={17} /> Review {data.founderActionsInbox.items.length} decisions</a>
      </Toolbar>
      <Tabs active={tab} items={["Unified", "Email", "Messages", "Follow-ups", "Drafts", "Waiting"]} onChange={setTab} />
      <div className="ns-communications-layout">
        <aside className="ns-message-list">
          <header>Preview messages <Badge tone="neutral">{visibleMessages.length}</Badge></header>
          {visibleMessages.map((item, index) => (
            <button className={selected === index ? "active" : ""} key={item.subject} onClick={() => setSelected(index)} type="button">
              <Avatar initials={item.initials} tone={item.tone} />
              <span><small>{item.source}</small><strong>{item.subject}</strong><em>{item.preview}</em></span>
              <time>{item.time}</time>
            </button>
          ))}
        </aside>
        <section className="ns-message-reader">
          {message ? <>
          <div className="ns-reader-actions">
            <Button disabled title="No message summarization runtime is connected" tone="quiet" icon="sparkles">Summarize</Button>
            <Button disabled title="No governed draft contract is connected" tone="quiet" icon="pencil">Draft reply</Button>
            <Button disabled title="No follow-up mutation contract is connected" tone="quiet" icon="clock">Add follow-up</Button>
            <Button disabled title="No communication-to-CRM mutation contract is connected" tone="quiet" icon="users">Link CRM</Button>
            <Button disabled title="Calendar writes remain blocked" tone="secondary" icon="calendar-days">Propose event</Button>
          </div>
          <header><h2>{message.subject}</h2><Icon name="reply" size={17} /><Icon name="forward" size={17} /></header>
          <div className="ns-message-body">
            <div className="ns-message-sender"><Avatar initials={message.initials} tone={message.tone} /><span><strong>{message.source}</strong><small>To: Alex Morgan</small></span><time>{message.time}</time></div>
            <p>Hi Alex,</p>
            <p>Thanks for the great discussion earlier this week. We&apos;re excited to move forward and would like to schedule our customer kickoff session.</p>
            <p>Are you available next Tuesday or Wednesday afternoon? We&apos;d like to align on objectives, key stakeholders, and a timeline for the first 90 days.</p>
            <p>Best,<br />Sara Patel<br />Relationship Alpha</p>
          </div>
          <Panel className="ns-summary-card" title="UAA summary · read-only" icon="sparkles">
            <p>Synthetic summary fixture only. No model call, source retrieval, or action proposal occurred.</p>
          </Panel>
          </> : <div className="ns-empty-lease"><Icon name="search" size={34} /><h3>No fixture matches</h3><p>Change the local preview search to inspect another synthetic item.</p></div>}
        </section>
        <aside className="ns-context-inspector">
          {message ? <>
          <Panel title="Relationship context" icon="users">
            <MetaRow icon="info" label="Posture" value="Synthetic fixture" tone="orange" />
            <MetaRow icon="lock" label="Account data" value="Not connected" />
          </Panel>
          <Panel title="Proposed event · preview" icon="calendar-days">
            <h3>Synthetic proposal card</h3>
            <p>No proposal envelope or conflict-check evidence is connected.</p>
            <MetaRow icon="lock" label="Calendar write" value="External write blocked" />
            <div className="ns-stack-actions"><Button disabled title="No calendar proposal envelope is connected" tone="primary">Review proposal</Button><Button disabled title="No communication handoff contract is connected">Ask UAA</Button></div>
          </Panel>
          </> : <p className="ns-help-copy">No fixture is selected.</p>}
        </aside>
      </div>
      <div className="ns-receipt-band"><Icon name="shield-check" size={18} tone="warning" /> Synthetic communication fixture · Backend source posture: {sourcePosture.status.replaceAll("_", " ")} ({sourcePosture.ready_source_count}/{sourcePosture.source_count} ready) · No account read, reply, or calendar write performed</div>
    </div>
  );
}

export function WorkBoardSurface({ data }: { data: ControlCenterData }) {
  const board = data.workBoard;
  const [selectedRef, setSelectedRef] = useState(data.workBoard.cards[0]?.card_ref ?? "");
  const [query, setQuery] = useState("");
  const backendOwned = data.connection.state === "online"
    && !data.connection.usingMockData
    && data.routeStates["/work-board"]?.state === "backend_owned"
    && board.backend_owned
    && board.read_only
    && board.safe_refs_only
    && !board.non_authoritative_mock_fallback;
  const selected = board.cards.find((card) => card.card_ref === selectedRef) ?? board.cards[0];
  const normalizedQuery = query.trim().toLowerCase();
  const visibleCards = board.cards.filter((card) => `${card.title} ${card.safe_summary} ${card.tags.join(" ")}`.toLowerCase().includes(normalizedQuery));
  const cardsForColumn = (columnRef: string) => visibleCards.filter((card) => card.column_ref === columnRef);

  return (
    <div className="ns-surface ns-work-board">
      <Toolbar title={board.title} subtitle="Backend-owned plans and exact local task records">
        <label className="ns-search"><span className="sr-only">Search Work Board</span><Icon name="search" size={16} /><input aria-label="Search Work Board" onChange={(event) => setQuery(event.target.value)} placeholder="Search tasks" type="search" value={query} /></label>
        <Button disabled title="Grouping is presentation-only and is not implemented in this representation">Group: Status</Button>
        <Button disabled icon="plus" title="An exact approved card-create envelope is not supplied by this surface">Create card unavailable</Button>
        <a className="ns-button primary" href={`${WORKSPACE_PREFIX}/decisions`}><Icon name="scale" size={17} /> Review {data.founderActionsInbox.items.length} decisions</a>
      </Toolbar>
      <Tabs active="Board" items={["Board"]} />
      <div className="ns-board-layout">
        <div className="ns-kanban" style={{ gridTemplateColumns: `repeat(${Math.max(board.columns.length, 1)}, minmax(180px, 1fr))` }}>
          {board.columns.map((column, columnIndex) => {
            const cards = cardsForColumn(column.column_ref);
            return (
            <section className={`ns-board-column ${column.status === "blocked" ? "red" : column.status === "in_progress" ? "blue" : column.status === "review" ? "purple" : columnIndex === 0 ? "gray" : ""}`} key={column.column_ref}>
              <header><strong>{column.label}</strong><Badge tone="neutral">{cards.length}</Badge></header>
              {cards.map((card) => (
                <button className={`ns-task-card priority-${card.priority} ${selected?.card_ref === card.card_ref ? "selected" : ""}`} key={card.card_ref} onClick={() => setSelectedRef(card.card_ref)} type="button">
                  <small>{card.priority}</small>
                  <strong>{card.title}</strong>
                  <span><Icon name="user" size={13} /> {card.owner_ref}</span>
                  <span><Icon name="shield-check" size={13} /> {card.authority_state.replaceAll("_", " ")}</span>
                  <span><Icon name="link" size={13} /> {card.progress_label}</span>
                  <footer><Icon name="file-check-2" size={13} /> {card.evidence_refs.length} evidence refs <time>{card.proof_refs.length} proof</time></footer>
                </button>
              ))}
              {cards.length === 0 ? <p className="ns-help-copy">No backend cards in this lane.</p> : null}
              <button className="ns-add-task" disabled title="An exact approved card-create envelope is not supplied by this surface" type="button"><Icon name="plus" size={15} /> Create card unavailable</button>
            </section>
          )})}
        </div>
        <aside className="ns-board-inspector">
          {selected ? <>
            <header><h2>{selected.title}</h2><Badge tone={backendOwned ? "green" : "orange"}>{backendOwned ? "Backend" : "Preview"}</Badge></header>
            <p>{selected.safe_summary}</p>
            <div className="ns-inline-actions"><Button disabled icon="play" title="No exact task execution contract">Start</Button><Button disabled icon="calendar" title="No Day Plan mutation contract">Add to Day Plan</Button></div>
            <MetaRow icon="list-todo" label="Lane" value={board.columns.find((column) => column.column_ref === selected.column_ref)?.label ?? selected.column_ref} />
            <MetaRow icon="user" label="Owner ref" value={selected.owner_ref} />
            <MetaRow icon="shield-check" label="Authority" value={selected.authority_state.replaceAll("_", " ")} tone={selected.authority_state === "blocked" ? "red" : selected.authority_state === "proposal_only" ? "orange" : "green"} />
            <MetaRow icon="receipt-text" label="Latest task receipt" value={board.latest_task_create_receipt_ref ?? "None recorded"} />
            <MetaRow icon="file-check-2" label="Evidence / proof" value={`${selected.evidence_refs.length} / ${selected.proof_refs.length}`} />
            <Button disabled icon="circle-check" title="An exact approved task-create envelope is not supplied by this surface">Create local task unavailable</Button>
            <p className="ns-help-copy">This surface is read-only. Card and task creation require a separately prepared exact approval envelope and fresh request-scoped authority evaluation.</p>
          </> : <p className="ns-help-copy">No Work Board card matches the current filter.</p>}
        </aside>
      </div>
      <div aria-live="polite" className="ns-receipt-band"><Icon name={backendOwned ? "receipt-text" : "triangle-alert"} size={18} tone={backendOwned ? "success" : "warning"} /> {board.safe_summary} · Mutations unavailable without an exact approval envelope</div>
    </div>
  );
}

export function CrmSurface({ data }: { data: ControlCenterData }) {
  const crm = data.crmLocalCommandCenter;
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [query, setQuery] = useState("");
  const relationships = crm.relationships.filter((relationship) => `${relationship.safe_display_label} ${relationship.safe_summary} ${relationship.relationship_kind_ref}`.toLowerCase().includes(query.trim().toLowerCase()));
  const selected = relationships[selectedIndex] ?? relationships[0];
  const selectedPerson = crm.people.find((person) => person.person_ref === selected?.person_ref);
  const selectedOrganization = crm.organizations.find((organization) => organization.organization_ref === selected?.organization_ref);
  const followUps = crm.follow_ups.filter((item) => item.relationship_ref === selected?.relationship_ref);
  const opportunities = crm.opportunities.filter((item) => item.relationship_ref === selected?.relationship_ref);
  const timeline = crm.timeline_events.filter((item) => item.relationship_ref === selected?.relationship_ref);
  const backendOwned = data.connection.state === "online"
    && !data.connection.usingMockData
    && data.routeStates["/crm"]?.state === "backend_owned"
    && crm.backend_owned
    && crm.read_only
    && crm.safe_refs_only;
  return (
    <div className="ns-surface ns-crm">
      <Toolbar title="CRM v3" subtitle="Relationships, opportunities, and commitments">
        <SearchField onChange={(value) => { setQuery(value); setSelectedIndex(0); }} placeholder="Search safe relationship summaries" value={query} />
        <Button disabled title="Smart-list selection is not yet a local presentation control">Smart views: {crm.smart_lists.length}</Button><Button disabled icon="filter" title="Backend CRM filters are not connected">Filters</Button>
        <a className="ns-button primary" href={`${WORKSPACE_PREFIX}/decisions`}>Review {data.founderActionsInbox.items.length} decisions</a>
      </Toolbar>
      <Tabs active="People" items={["People", "Organizations", "Opportunities", "Pipeline", "Follow-ups", "Reports"]} />
      <div className="ns-kpi-strip">
        {[`Relationships|${crm.relationships.length}|backend`, `Follow-ups|${crm.follow_ups.length}|safe refs`, `Opportunities|${crm.opportunities.length}|read only`, `Pipelines|${crm.pipelines.length}|local`, `Reports|${crm.reports.length}|evidence`, `Timeline events|${crm.timeline_events.length}|redacted`].map((value) => {
          const [label, number, trend] = value.split("|");
          return <div key={label}><small>{label}</small><strong>{number}</strong><span>{trend}</span></div>;
        })}
      </div>
      <div className="ns-crm-layout">
        <aside className="ns-smart-views">
          <strong>Smart views</strong>
          {crm.smart_lists.map((item, index) => <button className={index === 0 ? "active" : ""} disabled key={item.smart_list_ref} title="Backend smart-list membership is visible but selection is not connected" type="button"><span>{item.safe_label}</span><small>{item.relationship_refs.length}</small></button>)}
          <hr /><strong>Pipelines</strong>
          {crm.pipelines.flatMap((pipeline) => pipeline.stages).map((stage, index) => <span className="ns-pipeline-key" key={stage.stage_ref}><i className={`tone-${["blue", "green", "purple", "orange"][index % 4]}`} />{stage.safe_label}<small>{stage.opportunity_refs.length}</small></span>)}
        </aside>
        <section className="ns-crm-table-wrap">
          <header><Button disabled title="All backend relationships are shown" tone="quiet" icon="list-filter">All relationships</Button><span>{backendOwned ? "Backend-owned read model" : "Preview fallback"}</span><Button disabled title="Column customization is not persisted" tone="quiet" icon="table-2">Columns</Button></header>
          <table className="ns-data-table">
            <thead><tr><th>Person / organization</th><th>Type</th><th>Stage</th><th>Last contact</th><th>Next commitment</th><th>Opportunity / value</th><th>Health</th></tr></thead>
            <tbody>{relationships.map((row, index) => { const followUp = crm.follow_ups.find((item) => item.relationship_ref === row.relationship_ref); const opportunity = crm.opportunities.find((item) => item.relationship_ref === row.relationship_ref); const organization = crm.organizations.find((item) => item.organization_ref === row.organization_ref); return <tr className={selectedIndex === index ? "selected" : ""} key={row.relationship_ref}><td><button aria-pressed={selectedIndex === index} className="ns-crm-row-select" onClick={() => setSelectedIndex(index)} type="button"><Avatar initials={initialsFor(row.safe_display_label)} tone={index % 2 ? "green" : "blue"} /><span><strong>{row.safe_display_label}</strong><small>{organization?.safe_display_label ?? "Safe relationship ref"}</small></span></button></td><td>{row.relationship_kind_ref}</td><td><Badge tone={row.health_state === "warm" || row.health_state === "steady" ? "green" : row.health_state === "blocked" ? "red" : "orange"}>{row.health_state.replaceAll("_", " ")}</Badge></td><td>{row.timeline_event_refs.length} events</td><td>{followUp?.due_ref ?? "None"}</td><td>{opportunity?.stage_label ?? "None"}</td><td><Badge tone={row.stale_state === "fresh" ? "green" : row.stale_state === "conflict" ? "red" : "orange"}>{row.stale_state.replaceAll("_", " ")}</Badge></td></tr>})}{relationships.length === 0 ? <tr><td colSpan={7}>No backend relationship matches the search.</td></tr> : null}</tbody>
          </table>
          <div className="ns-crm-analytics"><MiniAnalytics title="Pipeline by stage" /><MiniAnalytics title="Relationship health" /><MiniAnalytics title="Today’s commitments" /></div>
        </section>
        <aside className="ns-crm-inspector">
          {selected ? <><header><Avatar initials={initialsFor(selected.safe_display_label)} tone="blue" /><span><h2>{selected.safe_display_label}</h2><small>{selectedOrganization?.safe_display_label ?? selectedPerson?.safe_display_label ?? selected.relationship_ref}</small></span><Icon name="shield-check" size={17} /></header>
          <div className="ns-health-summary"><Icon name={selected.health_state === "blocked" ? "circle-alert" : "circle-check"} size={26} tone={selected.health_state === "blocked" ? "danger" : "success"} /><span><small>Relationship posture</small><strong>{selected.health_state.replaceAll("_", " ")} · {selected.stale_state.replaceAll("_", " ")}</strong></span></div>
          <div className="ns-inline-actions"><Button disabled title="CRM sends are blocked" tone="primary" icon="phone">Call</Button><Button disabled title="CRM sends are blocked" icon="mail">Message</Button><Button disabled title="No exact follow-up mutation is connected" icon="calendar">Add follow-up</Button></div>
          <Tabs active="Overview" items={["Overview", "Activity"]} />
          <p>{selected.safe_summary}</p>
          <MetaRow icon="users" label="Related people" value={selectedPerson ? "1 safe person ref" : "None"} />
          <MetaRow icon="briefcase-business" label="Opportunities" value={String(opportunities.length)} />
          <MetaRow icon="calendar" label="Follow-ups" value={String(followUps.length)} />
          <MetaRow icon="list-todo" label="Timeline events" value={String(timeline.length)} />
          <Panel title="Suggested actions" icon="sparkles">
            {(crm.ai_proposals.filter((item) => item.relationship_ref === selected.relationship_ref).slice(0, 3)).map((proposal) => <p key={proposal.proposal_ref}>{proposal.safe_summary} <Badge tone="orange">Proposal only</Badge></p>)}
            {crm.ai_proposals.filter((item) => item.relationship_ref === selected.relationship_ref).length === 0 ? <p>No proposal is attached to this relationship.</p> : null}
          </Panel>
          </> : <p className="ns-help-copy">No backend relationship matches the search.</p>}
        </aside>
      </div>
      <div className="ns-receipt-band"><Icon name="shield-check" size={18} tone={backendOwned ? "success" : "warning"} /> {backendOwned ? "Backend-owned CRM read model" : "Non-authoritative CRM fallback"} · Sends, calendar writes, connector writes, and external CRM writes remain blocked</div>
    </div>
  );
}

function MiniAnalytics({ title }: { title: string }) {
  return <Panel title={title}><div className="ns-mini-bars"><span style={{ width: "74%" }} /><span style={{ width: "58%" }} /><span style={{ width: "86%" }} /></div><small>Preview-safe summary</small></Panel>;
}

function initialsFor(label: string) { return label.split(/\s+/).slice(0, 2).map((part) => part[0] ?? "").join("").toUpperCase() || "R"; }

export function CalendarSurface({ data }: { data: ControlCenterData }) {
  const calendarSource = data.founderSourceReadiness.source_readiness_items.find((item) => item.source_kind.toLowerCase().includes("calendar"));
  return (
    <div className="ns-surface ns-calendar">
      <Toolbar title="Calendar" subtitle="Synthetic desktop fixture · no calendar account is connected">
        <Button disabled title="Preview calendar navigation is not connected">Today</Button><Button disabled icon="chevron-left" title="Preview calendar navigation is not connected">Previous</Button><Button disabled icon="chevron-right" title="Preview calendar navigation is not connected">Next</Button><Button disabled tone="primary" title="Only the week preview is implemented">Week</Button><Button disabled icon="calendar-days" title="Calendar writes remain blocked">Propose event</Button><a className="ns-button primary" href={`${WORKSPACE_PREFIX}/decisions`}>Review {data.founderActionsInbox.items.length} decisions</a>
      </Toolbar>
      <div className="ns-calendar-layout">
        <section className="ns-week-calendar">
          <header><span><i className="blue" /> Work</span><span><i className="green" /> CRM</span><span><i className="purple" /> Focus</span><span><i className="orange" /> Personal</span><strong>Pacific Time</strong></header>
          <div className="ns-calendar-grid">
            <div className="ns-time-column">{["All day", "8 AM", "9 AM", "10 AM", "11 AM", "12 PM", "1 PM", "2 PM", "3 PM", "4 PM", "5 PM", "6 PM"].map((time) => <span key={time}>{time}</span>)}</div>
            {["MON 13", "TUE 14", "WED 15", "THU 16", "FRI 17", "SAT 18", "SUN 19"].map((day, index) => <div className="ns-day-column" key={day}><header>{day}</header>{index < 5 ? <CalendarEvent day={index} /> : null}</div>)}
            <div className="ns-now-line"><span>11:24 AM</span></div>
          </div>
        </section>
        <aside className="ns-calendar-inspector">
          <h2>Calendar candidate</h2><Badge tone="neutral">Synthetic fixture</Badge>
          <MetaRow icon="mail" label="Source" value="No backend source" />
          <MetaRow icon="calendar" label="Candidate" value="Illustrative only" />
          <MetaRow icon="users" label="Participants" value="No safe refs" />
          <MetaRow icon="circle-help" label="Conflict check" value="Not performed" />
          <MetaRow icon="shield-check" label="Authority" value="No proposal authority" tone="orange" />
          <MetaRow icon="lock" label="External sync" value="Blocked" />
          <Panel title="Why this is shown"><p>This render fixture demonstrates layout only. UAA did not read a message or propose an event.</p></Panel>
          <a className="ns-button primary" href={`${WORKSPACE_PREFIX}/decisions`}>Review in Action Inbox</a><Button disabled icon="pencil" title="No calendar proposal mutation contract is connected">Edit proposal</Button><Button disabled tone="quiet" icon="message-square" title="No calendar-to-agent handoff contract is connected">Ask UAA</Button>
        </aside>
      </div>
      <div className="ns-receipt-band"><Icon name="info" size={18} /> Synthetic calendar fixture · Backend source posture: {calendarSource?.status.replaceAll("_", " ") ?? "missing"} · No account read or calendar write performed</div>
    </div>
  );
}

function CalendarEvent({ day }: { day: number }) {
  const events = [
    ["9:00–10:00 AM", "Customer planning call", "work"],
    ["10:00–12:00 PM", "Q3 focus block", "crm"],
    ["9:00–10:30 AM", "Product review", "focus"],
    ["11:00–12:00 PM", "CRM sync", "work"],
    ["1:00–2:00 PM", "Q3 focus block", "crm"],
  ];
  const [time, title, type] = events[day];
  return <button className={`ns-calendar-event ${type}`} disabled style={{ top: `${90 + day * 42}px` }} title="Synthetic fixture event; no backend event record is connected" type="button"><small>{time}</small><strong>{title}</strong><span>Fixture only</span></button>;
}
