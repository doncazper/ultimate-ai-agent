import { useState } from "react";
import type { ControlCenterData } from "../api/types";
import { Badge, Button, Icon, Panel, SearchField, Tabs } from "./primitives";
import { WORKSPACE_PREFIX } from "./model";

const skillIdeas = [
  ["Sonoscli", "Control Sonos speakers for discovery, status, playback, volume, and grouping.", "Uncategorized", "#1 this week", "56 stars", "86K downloads", "May 11, 2026"],
  ["Gog", "Google Workspace CLI for Gmail, Calendar, Drive, Contacts, Sheets, and Docs.", "Gmail", "#2 this week", "940 stars", "188.7K downloads", "May 11, 2026"],
  ["GitHub", "Interact with GitHub through the gh CLI for issues, pull requests, and CI runs.", "GitHub", "#3 this week", "651 stars", "192.9K downloads", "Jun 12, 2026"],
  ["Weather", "Get current weather and forecasts without an API key.", "Current Weather", "#4 this week", "422 stars", "163.8K downloads", "May 11, 2026"],
  ["OpenAI Whisper", "Local speech-to-text with the Whisper CLI and no API key.", "Speech-to-Text", "#5 this week", "332 stars", "86K downloads", "May 11, 2026"],
  ["Skill Creator", "Guide for creating modular skills with focused workflows and references.", "Uncategorized", "#6 this week", "327 stars", "94.7K downloads", "May 16, 2026"],
  ["Notion", "Use the Notion API to manage pages, databases, and blocks.", "Notion", "#7 this week", "266 stars", "95.1K downloads", "May 11, 2026"],
  ["Obsidian", "Work with Obsidian vaults and plain Markdown notes.", "Uncategorized", "#8 this week", "443 stars", "104.9K downloads", "May 18, 2026"],
  ["Gemini", "Use the Gemini CLI for one-shot questions, summaries, and generation.", "Uncategorized", "#9 this week", "56 stars", "35.4K downloads", "May 11, 2026"],
  ["Mcporter", "Inspect, configure, authenticate, and call MCP servers and tools through a review lane.", "Uncategorized", "#10 this week", "196 stars", "68.1K downloads", "May 18, 2026"],
];

export function StudioSurface({ data }: { data: ControlCenterData }) {
  const [mode, setMode] = useState<"Chat" | "Code" | "Create">("Create");
  const [createView, setCreateView] = useState<"skills" | "presentations">("skills");
  const backendSnapshot = data.connection.state === "online" && !data.connection.usingMockData;

  return (
    <div className="ns-studio-app">
      <StudioRail mode={mode} onMode={setMode} createView={createView} onCreateView={setCreateView} />
      {mode === "Create" && createView === "skills" ? (
        <SkillWorkbench backendSnapshot={backendSnapshot} />
      ) : mode === "Create" ? (
        <PresentationWorkspace />
      ) : mode === "Code" ? <StudioCodeWorkspace data={data} /> : <StudioChatWorkspace data={data} />}
    </div>
  );
}

function StudioRail({
  createView,
  mode,
  onCreateView,
  onMode,
}: {
  createView: "skills" | "presentations";
  mode: "Chat" | "Code" | "Create";
  onCreateView: (value: "skills" | "presentations") => void;
  onMode: (value: "Chat" | "Code" | "Create") => void;
}) {
  return (
    <aside className="ns-studio-rail">
      <div className="ns-window-controls"><span /><span /><span /></div>
      <a className="ns-studio-brand" href={`${WORKSPACE_PREFIX}/today`}><Icon name="shield-check" size={27} /><strong>UAA Studio</strong></a>
      <a className="ns-back-link" href={`${WORKSPACE_PREFIX}/today`}><Icon name="arrow-left" size={14} /> Back to Control Center</a>
      <small>Modes</small>
      {([[
        "Chat", "message-square", "Talk, decide, hand off"],
        ["Code", "code-2", "Propose, review, validate"],
        ["Create", "square-pen", "Design, version, review"],
      ] as const).map(([label, icon, subtitle]) => (
        <button className={mode === label ? "active" : ""} key={label} onClick={() => onMode(label)} type="button"><Icon name={icon} size={19} /><span><strong>{label}</strong><small>{subtitle}</small></span></button>
      ))}
      {mode === "Create" ? <>
        <hr /><small>Create</small>
        <button disabled title="Choose an implemented asset surface below" type="button"><Icon name="circle-plus" size={17} /><span><strong>New asset</strong></span></button>
        <button className={createView === "skills" ? "active secondary" : "secondary"} onClick={() => onCreateView("skills")} type="button"><Icon name="shield-question" size={17} /><span><strong>Skill Workbench</strong></span></button>
        <button className={createView === "presentations" ? "active secondary" : "secondary"} onClick={() => onCreateView("presentations")} type="button"><Icon name="monitor" size={17} /><span><strong>Presentations</strong></span></button>
        {[["Documents", "file-text"], ["Spreadsheets", "file-spreadsheet"], ["Media", "image"], ["Brand", "shield"]].map(([label, icon]) => <button className="secondary" disabled key={label} title={`${label} surface is not implemented`} type="button"><Icon name={icon as Parameters<typeof Icon>[0]["name"]} size={17} /><span><strong>{label}</strong></span></button>)}
        <hr /><small>Projects</small>
        <div className="ns-studio-projects"><strong><Icon name="folder" size={15} /> Founder Command Center</strong><span>Founder pitch deck</span><span>Launch brief</span><span>Quarterly model</span><span>Brand story</span></div>
      </> : null}
      <a className="ns-studio-settings" href={`${WORKSPACE_PREFIX}/settings`}><Icon name="settings" size={18} /> Settings</a>
    </aside>
  );
}

function SkillWorkbench({ backendSnapshot }: { backendSnapshot: boolean }) {
  const [selected, setSelected] = useState(0);
  const [tab, setTab] = useState("Discover");
  const [query, setQuery] = useState("");
  const visibleSkills = skillIdeas.filter((row) => `${row[0]} ${row[1]} ${row[2]}`.toLowerCase().includes(query.trim().toLowerCase()));
  const skill = visibleSkills[selected] ?? visibleSkills[0] ?? skillIdeas[0];
  return (
    <section className="ns-studio-workspace ns-skill-workbench">
      <header className="ns-studio-header">
        <div><small>Studio / Create / Skill Workbench</small><h1>Skill Workbench</h1><p>Discover ideas. Adapt safely. Keep the result yours.</p></div>
        <span className="ns-studio-posture"><Icon name="shield-check" size={16} /> {backendSnapshot ? "Backend snapshot" : "Sanitized preview"} · Review before adaptation</span>
        <Button disabled title="No durable saved-ideas contract is connected">Saved ideas</Button><Button tone="primary" disabled title="No governed skill-brief contract is connected">Start from a brief</Button>
      </header>
      <Tabs active={tab} items={["Discover", "For You", "Categories", "Saved", "Adaptations", "Local Skills"]} onChange={setTab} />
      <div className="ns-skill-body">
        <section className="ns-skill-results">
          <SearchField onChange={(value) => { setQuery(value); setSelected(0); }} placeholder="Search source-derived skill metadata" value={query} />
          <div className="ns-skill-filters"><select aria-label="Source" disabled title="Source filtering is not connected"><option>Source: All</option></select><select aria-label="Category" disabled title="Category filtering is not connected"><option>Category: All</option></select><select aria-label="Freshness" disabled title="Freshness filtering is not connected"><option>Freshness: Any</option></select><button disabled title="Search can be cleared directly" type="button">Clear</button></div>
          <div className="ns-skill-count"><strong>31 skill ideas</strong><span>Sanitized snapshot · Jul 13, 2026</span><span>Sort by: Relevance</span><Icon name="table-2" size={16} /><Icon name="list-filter" size={16} /></div>
          <div className="ns-skill-table" role="table" aria-label="Skill discovery metadata">
            <div className="ns-skill-table-head" role="row"><span>Skill</span><span>Category</span><span>Source</span><span>Rank</span><span>Source signal</span><span>Popularity</span><span>Updated</span></div>
            {tab === "Discover" ? visibleSkills.map((row, index) => <button className={selected === index ? "selected" : ""} key={row[0]} onClick={() => setSelected(index)} role="row" type="button"><span><Icon name="file-text" size={17} /><span><strong>{row[0]}</strong><small>{row[1]}</small></span></span><span>{row[2]}</span><span><i /> ClawHub</span><span>{row[3]}</span><span>★ {row[4]}</span><span>{row[5]}</span><span>{row[6]}</span></button>) : <p className="ns-help-copy">{tab} has no connected catalog contract yet. Discover remains the accepted preview surface.</p>}
          </div>
          <footer className="ns-table-pagination"><label>Rows per page: <select disabled><option>25</option></select></label><span>1–{visibleSkills.length} of {visibleSkills.length}</span><Button disabled tone="primary">1</Button><Button disabled title="No second preview page is available">2</Button><Icon name="chevron-right" size={15} /></footer>
          <StudioComposer />
        </section>
        <aside className="ns-skill-inspector">
          <h2>{skill[0]}</h2><section><h3>Why it may fit</h3><p>{skill[1]}</p></section>
          <section><h3>Source signals</h3>{[["Source", "ClawHub"], ["Rank", skill[3]], ["Stars", skill[4].replace(" stars", "")], ["Average rating", "Not provided"], ["Rating count", "Not provided"], ["Downloads", skill[5]], ["Comments", "1"], ["Updated", skill[6]], ["License", "Not provided"]].map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}</section>
          <section><h3>Permissions & review</h3><div><span>External code</span><strong>Not imported</strong></div><div><span>Data access</span><strong>Not assessed</strong></div><div><span>Permissions</span><strong>Review required</strong></div><div><span>Risk</span><strong>Not assessed</strong></div></section>
          <section><h3>UAA posture</h3><div><span>Adaptation</span><strong>Not started</strong></div><div><span>Safeguards</span><strong>External code blocked</strong></div><div><span>Review</span><strong>Required before adaptation</strong></div></section>
          <div className="ns-skill-warning">External and agent-created skills are discovery signals only until quarantined, reviewed, converted into UAA-owned adaptations, and separately granted activation authority.</div>
        </aside>
      </div>
      <div className="ns-studio-status"><span><Icon name="shield-check" size={16} /> Studio · Create</span><span><Icon name="shield" size={16} /> Sanitized metadata snapshot</span><span><Icon name="activity" size={16} /> Popularity is a signal</span><span><Icon name="shield-alert" size={16} /> External code blocked</span><span><Icon name="shield-question" size={16} /> Review before adaptation</span></div>
    </section>
  );
}

function StudioComposer() {
  return <div className="ns-studio-composer"><Icon name="shield-check" size={18} /><span>Ask UAA to propose, compare, or prepare a review...</span><small>Continue in Chat</small><Button disabled>Auto route</Button><Button disabled tone="quiet" icon="sliders-horizontal">Options</Button><Button disabled tone="primary" icon="send">Prepare prompt</Button></div>;
}

function PresentationWorkspace() {
  return <section className="ns-studio-workspace ns-presentation"><header className="ns-studio-header"><div><small>Studio / Create / Presentations</small><h1>Founder pitch deck</h1><p>Presentation · 12 slides · PowerPoint</p></div><span className="ns-studio-posture"><Icon name="shield-check" size={16} /> Local preview · Review before export</span><Button disabled title="No presentation version contract is connected">Compare versions</Button><Button disabled title="No presentation review-envelope contract is connected" tone="primary">Prepare review proposal</Button></header><Tabs active="Canvas" items={["Canvas", "Versions", "References"]} /><div className="ns-presentation-body"><aside className="ns-slide-strip">{[1, 2, 3, 4, 5, 6].map((item) => <button className={item === 1 ? "active" : ""} disabled key={item} title="Slide selection is not implemented in this preview" type="button"><small>{item}</small><span><strong>{item === 1 ? "One calm operating system" : `Slide ${item}`}</strong><i /></span></button>)}</aside><div className="ns-slide-canvas"><h2>One calm<br />operating system<br />for founder work</h2><p>Today, relationships, work, and proof—connected without hidden authority.</p><div className="ns-slide-flow">{[["eye", "Observe"], ["clipboard-list", "Plan"], ["send", "Act"], ["shield-check", "Prove"]].map(([icon, label]) => <span key={label}><Icon name={icon as Parameters<typeof Icon>[0]["name"]} size={30} /><strong>{label}</strong></span>)}</div></div><aside className="ns-presentation-inspector"><Panel title="Presentation details"><p>Format <strong>PowerPoint (.pptx)</strong></p><p>Canvas <strong>Widescreen (16:9)</strong></p><p>Slides <strong>12</strong></p></Panel><Panel title="Mode ownership"><p>Create owns assets, versions, and references.</p><p>Hands off to Work Board, Calendar, and Evidence.</p></Panel><Button disabled icon="lock">Export blocked — exact lane not implemented</Button></aside></div><StudioComposer /><div className="ns-studio-status"><span>Studio · Create</span><span>Preview fixture</span><span>v4 · 12 slides</span><span>Review required</span><span>External delivery blocked</span></div></section>;
}

function StudioChatWorkspace({ data }: { data: ControlCenterData }) {
  const thread = data.founderAgentLoopThread;
  return <section className="ns-studio-workspace ns-studio-placeholder"><header className="ns-studio-header"><div><small>Studio / Chat</small><h1>Agent loop thread</h1><p>{thread.work_request.safe_summary}</p></div><span className="ns-studio-posture"><Icon name="shield-check" size={16} /> {thread.backend_owned ? "Backend-owned read model" : "Preview fallback"}</span><a className="ns-button secondary" href="/chat">Open canonical Chat</a></header><div className="ns-placeholder-canvas"><Icon name="message-square" size={48} /><h2>{thread.status.replaceAll("_", " ")}</h2><p>{thread.current_state.next_safe_operator_decision}</p><div className="ns-tag-list"><Badge tone="neutral">{thread.facts.length} facts</Badge><Badge tone="orange">{thread.unknowns.length} unknowns</Badge><Badge tone="blue">{thread.proposed_actions.length} proposed actions</Badge></div></div><StudioComposer /><div className="ns-studio-status"><span>Studio · Chat</span><span>{thread.local_read_model_only ? "Read only" : "Review required"}</span><span>{thread.evidence.event_count} evidence events</span><span>No execution authority</span></div></section>;
}

function StudioCodeWorkspace({ data }: { data: ControlCenterData }) {
  const session = data.codingSession;
  const panels = [session.workspace_context, session.task_thread, session.diff_preview, session.test_output_preview, session.git_preview, session.live_preview];
  return <section className="ns-studio-workspace ns-studio-placeholder"><header className="ns-studio-header"><div><small>Studio / Code</small><h1>{session.project_model.project_label}</h1><p>{session.full_strength_goal}</p></div><span className="ns-studio-posture"><Icon name="shield-check" size={16} /> {session.backend_owned ? "Backend-owned read model" : "Preview fallback"}</span><a className="ns-button secondary" href="/coding">Open canonical Coding</a></header><div className="ns-placeholder-canvas"><Icon name="code-2" size={48} /><h2>{session.status.replaceAll("_", " ")} · {session.branch_label}</h2><p>{session.next_safe_action}</p><div className="ns-grid-actions">{panels.map((panel) => <Panel icon="file-text" key={panel.panel_ref} title={panel.title}><Badge tone={panel.state === "blocked" ? "red" : panel.state === "proposal_only" ? "orange" : "green"}>{panel.state.replaceAll("_", " ")}</Badge><p>{panel.safe_summary}</p></Panel>)}</div></div><StudioComposer /><div className="ns-studio-status"><span>Studio · Code</span><span>{session.local_read_model_only ? "Read only" : "Review required"}</span><span>File writes {session.file_write_enabled ? "enabled" : "blocked"}</span><span>Shell {session.shell_subprocess_execution_enabled ? "enabled" : "blocked"}</span><span>Git mutation {session.git_mutation_enabled ? "enabled" : "blocked"}</span></div></section>;
}
