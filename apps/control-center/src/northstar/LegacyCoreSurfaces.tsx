import { Badge, Button, Icon } from "./primitives";
import { NorthStarIconBadge } from "../components/NorthStarIcon";
import { LegacyListRow, LegacyMeta, LegacyPanel, LegacyProgress, LegacyStatus } from "./LegacyPrimitives";

const approvalItems = [
  ["Create onboarding plan for Acme Corp", "Plan · CRM", "High impact", "red"],
  ["Update pricing in proposal", "Document · Proposals", "Medium", "orange"],
  ["Add 2 new testimonials to site", "Content · Website", "Low", "green"],
] as const;

export function LegacyTodaySurface() {
  return (
    <div className="legacy-surface legacy-today">
      <div className="legacy-six-grid">
        <LegacyPanel icon="sun" title="Morning Briefing" action={<small>8:42 AM</small>}>
          <p>Here&apos;s your operational snapshot for today.</p>
          <LegacyMeta icon="circle-check" label="Foundation Gate posture is Cautious" value="No critical risks" tone="green" />
          <LegacyMeta icon="info" label="7 items need review" value="3 approvals" tone="blue" />
          <LegacyMeta icon="chart-line" label="Evidence updated overnight" value="5 areas" tone="blue" />
          <LegacyMeta icon="users" label="CRM follow-ups due" value="6" tone="orange" />
          <Button>Open full briefing</Button>
        </LegacyPanel>
        <LegacyPanel icon="alarm-clock" title="Pending approval" action={<Badge tone="orange">3</Badge>}>
          {approvalItems.map(([title, detail, status, tone]) => <LegacyListRow detail={detail} key={title} status={<LegacyStatus tone={tone}>{status}</LegacyStatus>} title={title} />)}
          <Button>Open approvals</Button>
        </LegacyPanel>
        <LegacyPanel icon="brain" title="Memory shown">
          <LegacyListRow detail="Last confirmed May 12" status={<LegacyStatus tone="green">Verified</LegacyStatus>} title="Acme Corp prefers quarterly billing" />
          <LegacyListRow detail="Last confirmed May 10" status={<LegacyStatus tone="green">Verified</LegacyStatus>} title="John Smith is the economic buyer" />
          <LegacyListRow detail="Last confirmed Apr 29" status={<LegacyStatus tone="green">Verified</LegacyStatus>} title="They use HubSpot and Slack" />
          <Button>View memory</Button>
        </LegacyPanel>
        <LegacyPanel icon="target" title="Today priorities">
          {["Review pending approvals", "Follow up with 3 prospects", "Finalize Acme onboarding plan", "Publish case study", "Update pricing page"].map((item, index) => <LegacyMeta key={item} label={`${index + 1}. ${item}`} value={`~${[20, 45, 60, 30, 30][index]} min`} />)}
          <Button>View all priorities</Button>
        </LegacyPanel>
        <LegacyPanel icon="users" title="CRM follow-ups" action={<Badge tone="blue">6</Badge>}>
          {["Alex Carter — Acme Corp", "Jamie Moore — Brightline", "Sarah Patel — Northwind", "David Lee — Summit Ops"].map((item, index) => <LegacyListRow detail={["Onboarding discussion", "Proposal follow-up", "Check-in", "Demo feedback"][index]} key={item} status={<LegacyStatus tone={index < 2 ? "red" : "orange"}>{index < 2 ? "High" : "Medium"}</LegacyStatus>} title={item} />)}
          <Button>Open CRM</Button>
        </LegacyPanel>
        <LegacyPanel icon="database" title="Evidence updated" action={<Badge tone="green">5</Badge>}>
          {["Market research report", "Competitor pricing snapshot", "Acme onboarding doc", "Q2 pipeline analysis", "Customer case study"].map((item, index) => <LegacyMeta icon="circle" key={item} label={item} value={`${index * 2 + 2}h ago`} tone="green" />)}
          <Button>View evidence</Button>
        </LegacyPanel>
      </div>
      <div className="legacy-bottom-pair">
        <LegacyPanel icon="lock" title="Read-only sources">
          <div className="legacy-source-chips">{["Salesforce", "HubSpot", "Google Drive", "Confluence"].map((source) => <span key={source}><Icon name="circle-check" size={14} tone="success" /> {source} · read-only</span>)}</div>
          <LegacyMeta label="4 sources connected" value="All read-only" tone="green" />
          <Button>Manage sources</Button>
        </LegacyPanel>
        <LegacyPanel className="danger-soft" icon="lock" title="No connector writes"><p>All connectors are in read-only mode. No data will be created or changed.</p><Button>Manage permissions</Button></LegacyPanel>
      </div>
    </div>
  );
}

export function LegacyActionInboxSurface() {
  const queue = [
    ["Update issue status", "Issue Triage Agent", "Ready", "orange"],
    ["Create pull request", "Code Assistant", "Ready", "orange"],
    ["Generate summary", "Doc Assistant", "Approved", "green"],
    ["Delete file", "Repository Cleaner", "Blocked", "red"],
    ["Add label to issue", "Issue Triage Agent", "Receipt", "green"],
  ] as const;
  return <div className="legacy-surface legacy-action-inbox">
    <aside className="legacy-queue"><h1>Action Inbox</h1><h2>Ready for decision <Badge tone="blue">2</Badge></h2>{queue.map(([title, detail, status, tone], index) => <LegacyListRow detail={detail} key={title} selected={index === 0} status={<LegacyStatus tone={tone}>{status}</LegacyStatus>} title={title} />)}</aside>
    <section className="legacy-approval-envelope"><header><div><Icon name="mail-open" size={24} /><h1>Approval Envelope</h1></div><Badge tone="orange">Ask before changes</Badge></header><h2>Update issue status</h2><p>Agent: Issue Triage Agent · Requested today, 10:24 AM</p><LegacyPanel icon="target" title="Exact scope"><p>Update status and add a single label to one issue in this workspace.</p><LegacyMeta label="Workspace" value="acme/roadmap" /><LegacyMeta label="Resource" value="Issue #742" /><LegacyMeta label="Allowed actions" value="update_status, add_label" /></LegacyPanel><div className="legacy-inline-panels"><LegacyPanel icon="fingerprint" title="Idempotent"><code>iss-742-status-done-v1</code></LegacyPanel><LegacyPanel icon="shield-check" title="Safe-disable"><p>Revert status and remove label.</p></LegacyPanel></div><LegacyPanel icon="eye-off" title="Redacted preview"><pre>Issue #742 “Improve onboarding flow”{`\n`}− Status: In Progress → Done{`\n`}− Add label: triage/accepted</pre></LegacyPanel><div className="legacy-command-row"><Button disabled tone="primary" icon="check">Review approval</Button><Button disabled icon="pencil">Edit proposal</Button><Button disabled icon="clock">Defer proposal</Button><Button disabled tone="danger" icon="shield-alert">Reject proposal</Button></div><div className="legacy-receipt-pending"><Icon name="clock" size={18} tone="warning" /><strong>Receipt pending</strong><span>No execution yet</span></div></section>
    <aside className="legacy-authority-evaluation"><h1>Authority Evaluation</h1><LegacyMeta label="Active mode" value={<LegacyStatus tone="orange">Ask before changes</LegacyStatus>} /><LegacyMeta label="Required capability" value="workspace/write" /><LegacyMeta label="Approval reference" value="apr_8f3c7d2a" /><LegacyMeta label="Receipt reference" value="Receipt pending" /><LegacyPanel icon="scale" title="Policy result" action={<LegacyStatus tone="green">Allowed</LegacyStatus>}>{["Workspace match", "Action allowed", "Resource in scope", "No deny rules triggered"].map((item) => <p key={item}><Icon name="circle-check" size={15} tone="success" /> {item}</p>)}</LegacyPanel><LegacyPanel icon="clipboard-list" title="Audit trail"><LegacyMeta label="10:24 AM" value="Agent requested action" /><LegacyMeta label="10:24 AM" value="Authority check started" /><LegacyMeta label="Pending" value="Awaiting operator decision" /></LegacyPanel></aside>
    <LegacyPanel className="legacy-wide-band" icon="receipt-text" title="Recent receipt events"><div className="legacy-receipt-cards">{["Status updated", "Comment added", "Label added", "File created", "Status updated"].map((item, index) => <span key={`${item}-${index}`}><Icon name="circle-check" size={22} tone="success" /><strong>{item}</strong><small>Receipt: rct_safe_{index + 1}</small></span>)}</div></LegacyPanel>
  </div>;
}

const planGroups = [
  ["1. Guardrails & Policy", ["1.1 Policy schema v2", "1.2 Approval matrix", "1.3 Guardrail tests", "1.4 Violation handling"]],
  ["2. Change Safety", ["2.1 Preflight checks", "2.2 Canaries & rollbacks", "2.3 Blast radius limits"]],
  ["3. Evidence & Receipts", ["3.1 Receipt schema", "3.2 Evidence pipeline", "3.3 Verification rules"]],
] as const;

const boardColumns = [
  ["Review", "orange", ["Add policy schema v2", "Guardrail test coverage", "Rollback playbook"]],
  ["Ready", "blue", ["Approval matrix config", "Preflight checks", "Evidence schema"]],
  ["In progress", "purple", ["Guardrail tests v2", "Canary deployment", "Evidence pipeline"]],
  ["Receipts", "green", ["Policy schema v2", "Approval matrix", "Preflight checks"]],
] as const;

export function LegacyPlansWorkBoardSurface() {
  return <div className="legacy-surface legacy-plans-board"><aside className="legacy-plan-outline"><header><h1>Plans</h1><Button icon="plus">New</Button></header><h2>Q2 Platform Hardening</h2><strong>68% complete</strong><LegacyProgress value={68} tone="green" />{planGroups.map(([group, items]) => <section key={group}><h3>{group}</h3>{items.map((item) => <p className={item.includes("Guardrail tests") ? "selected" : ""} key={item}>{item}<Icon name={item.includes("tests") ? "circle" : "circle-check"} size={13} tone={item.includes("tests") ? "info" : "success"} /></p>)}</section>)}</aside><section className="legacy-board"><header><h1>Work Board</h1><span>Receipts</span><span>Plan details</span><Button icon="filter">Filters</Button></header><div className="legacy-board-columns">{boardColumns.map(([name, tone, items]) => <section className={`legacy-board-column ${tone}`} key={name}><header><h2>{name}</h2><Badge tone="neutral">3</Badge></header>{items.map((item, index) => <article className={item === "Guardrail tests v2" ? "selected" : ""} key={item}><strong>{item}</strong><small>{index + 1}.{index + 1} Plan step</small><span><Badge tone={tone === "green" ? "green" : tone === "orange" ? "orange" : "blue"}>{tone === "green" ? "RECEIPT" : name.toUpperCase()}</Badge>{tone !== "green" ? `${35 + index * 15}%` : `R-safe-${index + 1}`}</span></article>)}</section>)}</div></section><aside className="legacy-board-detail"><header><h1>Guardrail tests v2</h1><Badge tone="red">P1</Badge></header><LegacyProgress value={60} /><LegacyPanel icon="link" title="Action envelope"><a>AE-2024-05-18-0042</a></LegacyPanel><LegacyPanel icon="git-branch" title="Dependencies"><p>✓ Policy schema v2</p><p>✓ Approval matrix</p><p>○ Violation handling</p></LegacyPanel><LegacyPanel icon="shield-check" title="Review state"><Badge tone="orange">ASK · Security review</Badge><p>workspace/write · scoped</p></LegacyPanel><LegacyPanel icon="rotate-ccw" title="Rollback ready"><p>Blue/Green · main safe ref</p></LegacyPanel></aside><div className="legacy-plan-timeline"><strong>Plan timeline</strong><LegacyProgress value={68} tone="green" /><span>On track 68% · At risk 2 · Blocked 1 · Completed 8</span></div></div>;
}

const trustModes = [
  ["Read", "Read-only"],
  ["Ask", "Ask before changes"],
  ["Safe local", "Safe local work"],
  ["Work space", "Full workspace"],
  ["Machine", "Full machine"],
  ["Mission", "Delegated mission"],
] as const;

const trustRows = [
  ["Workspace", "Workspace"],
  ["Files", "Files"],
  ["Shell", "Shell"],
  ["Apps", "Apps"],
  ["Browser", "Browser"],
  ["Email", "Email"],
  ["Calendar", "Calendar"],
  ["Contacts", "Contacts"],
  ["Payments", "Shopping / Payments"],
  ["Model calls", "Provider / Model calls"],
  ["Memory", "Memory"],
  ["Production", "Cloud Production"],
] as const;

const trustPolicyEvents = ["Shell: run approved script", "File: write summary.xlsx", "Browser: external bank", "Email: send report", "Shell: curl external API", "File: delete archive", "App: open spreadsheet", "Model call: local summary", "Browser: open approved docs", "Calendar: create event"];

const trustEmergencyActions = [
  ["Revoke lease", "Immediately revoke all granted capabilities for this lease.", "octagon-alert", "danger", "Revoke lease"],
  ["Pause mission", "Pause mission execution. State is preserved.", "circle-pause", "warning", "Pause mission"],
  ["Kill switch", "Stop all agent activity across every active lease.", "octagon-alert", "danger", "Kill switch"],
  ["Safe-disable posture", "Restrict agents to read-only; no changes possible.", "shield-check", "info", "Enable safe-disable"],
] as const;

export function LegacyTrustSurface() {
  return <div className="legacy-surface legacy-trust"><section className="legacy-trust-matrix"><header><h1>Mode / Domain authority matrix</h1><span><i className="allow" /> Allow <i className="ask" /> Ask <i className="deny" /> Deny</span></header><table><colgroup><col className="legacy-trust-domain-column" />{trustModes.map(([, label]) => <col key={label} />)}</colgroup><thead><tr><th scope="col">Domain</th>{trustModes.map(([shortLabel, fullLabel]) => <th key={fullLabel} scope="col" title={fullLabel}><span aria-hidden="true">{shortLabel}</span><span className="legacy-sr-only">{fullLabel}</span></th>)}</tr></thead><tbody>{trustRows.map(([shortLabel, fullLabel], row) => <tr key={fullLabel}><td title={fullLabel}>{shortLabel}</td>{trustModes.map(([, mode], col) => <td key={mode}><Icon name={row < 2 || row === 10 ? "circle-check" : col < 2 || row > 10 ? "circle-minus" : "circle-alert"} size={14} tone={row < 2 || row === 10 ? "success" : col < 2 || row > 10 ? "danger" : "warning"} /></td>)}</tr>)}</tbody></table></section><section className="legacy-lease"><h1>Active lease: Delegated mission</h1><LegacyPanel title="Mission"><strong>Monthly financial close — automate reconciliation</strong><LegacyMeta icon="calendar" label="Time window" value="10:30 AM–12:15 PM" /><LegacyMeta icon="dollar-sign" label="Budget" value="$46.60 remaining" /><LegacyProgress value={37} tone="green" /></LegacyPanel><LegacyPanel title="Granted capabilities"><div className="legacy-chip-grid">{["Read files", "Write in safe workspace", "Run local scripts", "Use approved apps"].map((item) => <LegacyStatus tone="green" key={item}>✓ {item}</LegacyStatus>)}</div></LegacyPanel><LegacyPanel title="Ask if"><div className="legacy-chip-grid">{["Modify outside scope", "Delete any file", "Send email", "Access calendar"].map((item) => <LegacyStatus tone="orange" key={item}>{item}</LegacyStatus>)}</div></LegacyPanel><LegacyPanel title="Hard deny"><div className="legacy-chip-grid">{["Production systems", "Browser navigation", "Install software", "Modify settings"].map((item) => <LegacyStatus tone="red" key={item}>{item}</LegacyStatus>)}</div></LegacyPanel><LegacyPanel icon="shield" title="Constraints"><div className="legacy-chip-grid">{["No admin elevation", "No persistence", "Max 2 concurrent tasks", "Local only", "Log all actions", "Receipts required"].map((item) => <LegacyStatus tone="neutral" key={item}>{item}</LegacyStatus>)}</div></LegacyPanel></section><section className="legacy-policy-stream"><header><h1>Live policy decisions</h1><Button icon="activity">View stream</Button></header>{trustPolicyEvents.map((item, index) => <LegacyListRow detail={`Receipt · R-7F2A${index}`} icon={index % 2 ? "file-text" : "terminal"} key={item} status={<LegacyStatus tone={index % 3 === 0 ? "red" : index % 3 === 1 ? "orange" : "green"}>{index % 3 === 0 ? "Deny" : index % 3 === 1 ? "Ask" : "Allow"}</LegacyStatus>} title={item} />)}</section><div className="legacy-emergency-row">{trustEmergencyActions.map(([item, copy, icon, iconTone, action]) => <LegacyPanel className={`tone-${iconTone === "warning" ? "orange" : iconTone === "info" ? "blue" : "red"}`} key={item}><div className="legacy-emergency-content"><NorthStarIconBadge icon={icon} shape="circle" size="2xl" tone={iconTone} variant={iconTone === "danger" ? "solid" : "soft"} /><span><h2>{item}</h2><p>{copy}</p><Button tone={iconTone === "danger" ? "danger" : "secondary"}>{action}</Button></span></div></LegacyPanel>)}</div></div>;
}

const evidenceEvents = [["Proposed", "Plan to update pricing service"], ["Approved", "Change approved by operator"], ["Happened", "Deploy pricing-service v1.42.0"], ["Changed", "Config limits updated"], ["Undo ready", "Rollback target captured"], ["Stale", "Drift detected"], ["Blocked", "Waiting on manual approval"]] as const;

export function LegacyEvidenceProofSurface() {
  return <div className="legacy-surface legacy-evidence"><aside className="legacy-evidence-timeline"><header><h1>Evidence</h1><Button icon="filter">Filter</Button></header>{evidenceEvents.map(([state, detail], index) => <LegacyListRow detail={detail} icon={state === "Blocked" ? "circle-stop" : state === "Stale" ? "triangle-alert" : state === "Undo ready" ? "rotate-ccw" : "circle-check"} key={state} selected={index === 2} status={<time>09:{12 + index}:31</time>} title={state} />)}</aside><section className="legacy-proof-detail"><header><p>Receipt (selected)</p><h1>RCT-2025-05-20-09-13-02-7F3A <Badge tone="green">Happened</Badge></h1><p>Deploy pricing-service v1.42.0 by Deploy Agent</p></header><div className="legacy-tabs"><strong>Summary</strong><span>What changed</span><span>Artifacts</span><span>Checks</span><span>Notes</span></div><div className="legacy-proof-columns"><section>{["Run", "Action", "Agent", "Plan step", "Start time", "End time", "Outcome", "Receipt ID", "Integrity", "Authority"].map((item, index) => <LegacyMeta key={item} label={item} value={["RUN-safe-0017", "deploy_service", "Deploy Agent", "Deploy pricing-service", "09:12:58 UTC", "09:13:02 UTC", "Succeeded", "RCT-safe-7F3A", "Tamper-evident", "Evidence only"][index]} tone={item === "Outcome" || item === "Integrity" ? "green" : undefined} />)}</section><section><h2>What happened</h2><p>Deployed pricing-service version v1.42.0. All health checks passed.</p><h3>Key details</h3><ul><li>Instances: 5 rolling updates</li><li>Health: 5/5 healthy</li><li>Canary passed</li><li>Limits: 1000 → 1200 RPS</li></ul><h3>Linked receipts</h3><a>Undo ready · RCT-safe-91AA</a><a>Changed · RCT-safe-2B19</a></section></div><div className="legacy-ledger"><h2>Receipt ledger</h2><table><thead><tr><th>Time</th><th>Status</th><th>Action</th><th>Agent</th><th>Receipt ID</th><th>Undo</th></tr></thead><tbody>{evidenceEvents.map(([state], index) => <tr className={index === 2 ? "selected" : ""} key={state}><td>09:{12 + index}:02</td><td>{state}</td><td>{["plan_change", "approve_change", "deploy_service", "update_config", "capture_rollback", "update_limits", "db_migrate"][index]}</td><td>Local agent</td><td>RCT-safe-{index + 1}</td><td>{index > 1 && index < 5 ? "Yes" : "—"}</td></tr>)}</tbody></table></div></section><aside className="legacy-proof-inspector"><LegacyPanel icon="eye-off" title="Redacted refs"><LegacyMeta label="Secret store" value="safe-ref:omitted" /><LegacyMeta label="KMS key" value="safe-ref:redacted" /></LegacyPanel><LegacyPanel icon="shield-check" title="Approval refs"><LegacyMeta label="Approval ID" value="APR-safe-C391" /><LegacyMeta label="Policy" value="Change-Standard v2.1" /><LegacyMeta label="Approved by" value="Operator" /></LegacyPanel><LegacyPanel icon="rotate-ccw" title="Rollback target"><LegacyMeta label="State" value="Ready" tone="green" /><Button>Initiate rollback</Button></LegacyPanel><LegacyPanel icon="shield-check" title="Foundation Gate"><LegacyMeta label="Status" value="All gates pass" tone="green" /><Button>View gate details</Button></LegacyPanel></aside></div>;
}
