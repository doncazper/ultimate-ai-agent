import { Fragment, useState } from "react";
import type { ControlCenterData } from "../api/types";
import { Badge, Button, Icon, Panel } from "./primitives";
import { WORKSPACE_PREFIX } from "./model";

const sources = [
  ["Email", "Planned", "Headers, subjects, senders, dates, and message bodies.", "Sending, deleting, moving, labels, attachments write."],
  ["Calendar", "Planned", "Event titles, times, locations, participants.", "Creating, editing, deleting events."],
  ["Local files", "Available", "Files and text you select or reference.", "Any file modifications or writes."],
  ["Weather", "Optional", "Local forecast and weather conditions.", "Location sharing and writes."],
  ["News sources", "Proposal-only", "Article titles, summaries, and metadata.", "Opening links, downloads, and writes."],
];

export function OnboardingSurface({ data }: { data: ControlCenterData }) {
  const [selected, setSelected] = useState<string[]>([]);
  const [stage, setStage] = useState<"sources" | "review">("sources");
  const setup = data.macosSetupAssistant;
  const readiness = data.founderSourceReadiness.source_readiness_posture;
  return (
    <div className="ns-onboarding-app">
      <aside className="ns-onboarding-rail">
        <div className="ns-window-controls"><span /><span /><span /></div>
        <a className="ns-brand" href={`${WORKSPACE_PREFIX}/today`}><Icon name="shield-check" size={34} /><span><strong>Control Center</strong><small>Founder Command Center</small></span></a>
        <div className="ns-onboarding-steps">{["Local runtime", "Your workspace", "Read-only sources", "Review & finish"].map((item, index) => <div className={index === (stage === "sources" ? 2 : 3) ? "active" : index < (stage === "sources" ? 2 : 3) ? "complete" : ""} key={item}><span>{index + 1}</span><strong>{item}</strong><small>{index < 2 ? "Backend status loaded" : index === (stage === "sources" ? 2 : 3) ? "In progress" : "Not started"}</small></div>)}</div>
        <hr /><h3><Icon name="shield-check" size={18} /> Privacy summary</h3>{[["house", "Local only", "All data stays on this Mac"], ["shield", "No external access", "External actions blocked"], ["shield-alert", "Ask before changes", "You approve every change"], ["receipt-text", "Receipts required", "Evidence for every change"]].map(([icon, title, copy]) => <div className="ns-onboarding-posture" key={title}><Icon name={icon as Parameters<typeof Icon>[0]["name"]} size={19} /><span><strong>{title}</strong><small>{copy}</small></span></div>)}
      </aside>
      <div className="ns-onboarding-workspace">
        <header className="ns-onboarding-topbar"><span><Icon name="shield-check" size={19} tone={setup.controlCenterPreviewReady ? "success" : "warning"} /> Local setup · {setup.status.replaceAll("_", " ")}</span><span><Icon name="shield" size={19} /> {setup.blockedAuthoritySummary}</span><span><Icon name="user" size={19} /> Operator · You</span></header>
        <main>
          <header><h1>{stage === "sources" ? "Set up your Control Center" : "Review your local setup"}</h1><p>A private, local workspace you can expand deliberately.</p><small>Step {stage === "sources" ? 3 : 4} of 4 · selections are local and unsaved</small></header>
          <div className="ns-onboarding-content">
            {stage === "sources" ? <>
            <Panel title="Select read-only sources"><p>Your data stays on this Mac. Sources are read-only by default.</p><div className="ns-source-list">{sources.map(([name, state, reads, blocked], index) => <label key={name}><Icon name={["mail", "calendar", "file-text", "cloud-sun", "newspaper"][index] as Parameters<typeof Icon>[0]["name"]} size={22} /><input checked={selected.includes(name)} onChange={(event) => setSelected((current) => event.target.checked ? [...current, name] : current.filter((item) => item !== name))} type="checkbox" /><span><strong>{name} <Badge tone={state === "Available" ? "green" : "neutral"}>{state}</Badge></strong><small>Read-only contract</small><p><b>What will be read:</b> {reads}</p><p><b>What remains blocked:</b> {blocked}</p></span><button disabled title="Use the checkbox to include or exclude this local draft choice" type="button">Setup later</button></label>)}</div></Panel>
            <Panel title="Your default safety posture"><p>These rules protect your data and your Mac.</p>{[["shield-check", "Local only", "All data stays on this Mac. Nothing leaves your device."], ["shield-alert", "Ask before changes", "You approve every change before it happens."], ["link", "Safe refs", "Work with references, not copies, wherever possible."], ["receipt-text", "Receipts required for changes", "Every change produces a receipt you can review."], ["globe-2", "External actions blocked", "No external writes, API calls, or account changes."], ["server", "Data stays on this Mac", "No syncing or off-device backups by default."]].map(([icon, title, copy]) => <div className="ns-safety-row" key={title}><Icon name={icon as Parameters<typeof Icon>[0]["name"]} size={22} /><span><strong>{title}</strong><small>{copy}</small></span></div>)}<hr /><strong>How work flows in Control Center</strong><div className="ns-flow-steps">{[["file-text", "Read source"], ["sparkles", "UAA proposal"], ["shield-alert", "Your approval"], ["receipt-text", "Receipt"]].map(([icon, title], index) => <Fragment key={title}><div><Icon name={icon as Parameters<typeof Icon>[0]["name"]} size={27} /><strong>{title}</strong></div>{index < 3 ? <Icon name="arrow-right" size={20} /> : null}</Fragment>)}</div><div className="ns-info-callout"><Icon name="globe-2" size={18} /><span><strong>External write blocked</strong><small>No external actions or writes.</small></span></div></Panel>
            </> : <><Panel title="Selected read-only sources" icon="circle-check"><p>{selected.length ? selected.join(" · ") : "No optional source selected."}</p><p>These choices are presentation state only. No account authentication, connector runtime, or durable preference was changed.</p></Panel><Panel title="Backend setup posture" icon="shield-check"><p>{setup.repoSafeScope}</p><p><strong>{setup.steps.length}</strong> setup steps · <strong>{readiness.ready_source_count}/{readiness.source_count}</strong> sources ready</p><div className="ns-info-callout"><Icon name="lock" size={18} /><span><strong>Finish remains unavailable</strong><small>{setup.nextSteps[0] ?? readiness.next_safe_action}</small></span></div></Panel></>}
          </div>
        </main>
        <footer><Button disabled={stage === "sources"} icon="arrow-left" onClick={() => setStage("sources")}>Back</Button><p>Selections are local and unsaved.<br />No setup mutation contract is connected.</p>{stage === "sources" ? <><Button onClick={() => { setSelected([]); setStage("review"); }}>Skip sources for now</Button><Button onClick={() => setStage("review")} tone="primary">Continue to review</Button></> : <Button disabled title="No durable setup-finish contract is connected" tone="primary">Finish setup unavailable</Button>}</footer>
      </div>
    </div>
  );
}
