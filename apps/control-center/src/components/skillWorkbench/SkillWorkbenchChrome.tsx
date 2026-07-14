import { NorthStarIcon } from "../NorthStarIcon";

const CREATE_ITEMS = [
  ["Presentations", "file-text"],
  ["Documents", "file-text"],
  ["Spreadsheets", "file-spreadsheet"],
  ["Media", "image"],
  ["Brand", "shield"],
] as const;

export function WorkbenchHeader({
  authoritative,
}: {
  authoritative: boolean;
}) {
  return (
    <header className="skill-workbench-header">
      <div>
        <p className="skill-breadcrumbs">Studio / Create / Skill Workbench</p>
        <h1>Skill Workbench</h1>
        <span>Discover ideas. Adapt safely. Keep the result yours.</span>
      </div>
      <div className="skill-header-actions">
        <span className="skill-local-posture">
          <NorthStarIcon name="shield-check" size="lg" />
          {authoritative ? "Backend snapshot" : "Catalog unavailable"}
          <span aria-hidden="true">·</span> Review before adaptation
        </span>
        <button
          disabled
          title="Saved ideas require a later backend-owned persistence lane"
          type="button"
        >
          Saved ideas
        </button>
        <a className="primary" href="/chat">
          Start from a brief
        </a>
      </div>
    </header>
  );
}

export function StudioRail() {
  return (
    <aside className="studio-rail" aria-label="UAA Studio navigation">
      <div className="studio-window-controls" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <div className="studio-brand">
        <span className="studio-brand-mark">
          <NorthStarIcon name="shield-check" size="xl" />
        </span>
        <strong>UAA Studio</strong>
      </div>
      <a className="studio-back-link" href="/today">
        <NorthStarIcon name="arrow-left" size="sm" /> Back to Control Center
      </a>
      <p className="studio-rail-label">Modes</p>
      <nav className="studio-mode-nav" aria-label="Studio modes">
        <a href="/chat">
          <NorthStarIcon name="message-square" size="lg" />
          <span>
            <strong>Chat</strong>
            <small>Talk, decide, hand off</small>
          </span>
        </a>
        <a href="/coding">
          <NorthStarIcon name="code-2" size="lg" />
          <span>
            <strong>Code</strong>
            <small>Propose, review, validate</small>
          </span>
        </a>
        <span className="active" aria-current="page">
          <NorthStarIcon name="square-pen" size="lg" />
          <span>
            <strong>Create</strong>
            <small>Design, version, review</small>
          </span>
        </span>
      </nav>
      <div className="studio-create-nav">
        <p className="studio-rail-label">Create</p>
        <button
          disabled
          title="New asset requires a later Create contract"
          type="button"
        >
          <NorthStarIcon name="circle-plus" size="md" /> New asset
        </button>
        <span className="active">
          <NorthStarIcon name="shield-question" size="md" /> Skill Workbench
        </span>
        {CREATE_ITEMS.map(([label, icon]) => (
          <button
            disabled
            key={label}
            title={`${label} remains planned in the accepted Studio direction`}
            type="button"
          >
            <NorthStarIcon name={icon} size="md" /> {label}
          </button>
        ))}
      </div>
      <div className="studio-projects">
        <p className="studio-rail-label">Projects</p>
        <a href="/plans">
          <NorthStarIcon name="folder" size="md" /> Founder Command Center
        </a>
        <span>Founder pitch deck</span>
        <span>Launch brief</span>
        <span>Quarterly model</span>
        <span>Brand story</span>
      </div>
      <a className="studio-settings-link" href="/settings">
        <NorthStarIcon name="settings" size="lg" /> Settings
      </a>
    </aside>
  );
}

export function StudioComposer() {
  return (
    <div className="studio-composer" aria-label="Studio proposal handoff">
      <span className="studio-composer-shield">
        <NorthStarIcon name="shield-check" size="lg" />
      </span>
      <a href="/chat">
        <span>Ask UAA to propose, compare, or prepare a review…</span>
        <small>Continue in Chat</small>
      </a>
      <span className="studio-route-status">Auto route</span>
      <a aria-label="Open Studio settings" href="/settings">
        <NorthStarIcon name="sliders-horizontal" size="lg" />
      </a>
      <a aria-label="Continue in Chat" className="send" href="/chat">
        <NorthStarIcon name="send" size="lg" />
      </a>
    </div>
  );
}

export function StudioStatusBand({
  authoritative,
}: {
  authoritative: boolean;
}) {
  const items = [
    ["shield-check", "Studio · Create"],
    [
      "shield",
      authoritative ? "Sanitized metadata snapshot" : "Catalog unavailable",
    ],
    ["activity", "Popularity is a signal"],
    ["shield-alert", "External code blocked"],
    ["shield-question", "Review before adaptation"],
  ] as const;
  return (
    <footer className="studio-status-band" aria-label="Studio safety posture">
      {items.map(([icon, label]) => (
        <span key={label}>
          <NorthStarIcon name={icon} size="lg" /> {label}
        </span>
      ))}
    </footer>
  );
}
