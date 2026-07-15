import { Fragment, useState } from "react";
import type { ControlCenterData } from "../api/types";
import { Badge, Button, Icon, Panel } from "./primitives";
import { WORKSPACE_PREFIX } from "./model";

const sourceDrafts = [
  { name: "Email", kinds: ["email", "inbox"], reads: "Requested future scope: bounded message metadata and separately accepted content fields.", blocked: "Authentication, account reads, sends, deletes, moves, labels, and attachment writes." },
  { name: "Calendar", kinds: ["calendar"], reads: "Requested future scope: bounded event metadata from a separately connected read model.", blocked: "Authentication and creating, editing, or deleting events." },
  { name: "Local files", kinds: ["local_files", "repo"], reads: "Requested future scope: explicitly selected safe refs and bounded read-only metadata.", blocked: "File content access or mutation without a separately governed exact lane." },
  { name: "Weather", kinds: ["weather"], reads: "Requested future scope: bounded forecast evidence through an approved read-only adapter.", blocked: "Location disclosure, direct network calls, and external writes." },
  { name: "News sources", kinds: ["news", "web"], reads: "Requested future scope: cited search and extraction evidence through WebAccessGateway.", blocked: "Browser actions, downloads, uploads, authentication, and external writes." },
];

export function OnboardingSurface({ data }: { data: ControlCenterData }) {
  const [selected, setSelected] = useState<string[]>([]);
  const [stage, setStage] = useState<"sources" | "review">("sources");
  const setup = data.macosSetupAssistant;
  const readiness = data.founderSourceReadiness.source_readiness_posture;
  const sourceItems = data.founderSourceReadiness.source_readiness_items;
  return (
    <div className="ns-onboarding-app">
      <aside className="ns-onboarding-rail">
        <div className="ns-window-controls"><span /><span /><span /></div>
        <a className="ns-brand" href={`${WORKSPACE_PREFIX}/today`}><Icon name="shield-check" size={34} /><span><strong>Control Center</strong><small>Founder Command Center</small></span></a>
        <div className="ns-onboarding-steps">{["Local runtime", "Your workspace", "Read-only sources", "Review & finish"].map((item, index) => <div className={index === (stage === "sources" ? 2 : 3) ? "active" : index < (stage === "sources" ? 2 : 3) ? "complete" : ""} key={item}><span>{index + 1}</span><strong>{item}</strong><small>{index < 2 ? "Backend status loaded" : index === (stage === "sources" ? 2 : 3) ? "In progress" : "Not started"}</small></div>)}</div>
        <hr /><h3><Icon name="shield-check" size={18} /> Current posture</h3>{[["house", "Local setup draft", "Selections remain unsaved presentation state"], ["shield", "External writes", setup.blockedAuthoritySummary], ["shield-alert", "Exact evaluation", "Policy and exact approval apply where required"], ["receipt-text", "Mutation receipts", "Implemented mutations require backend receipts"]].map(([icon, title, copy]) => <div className="ns-onboarding-posture" key={title}><Icon name={icon as Parameters<typeof Icon>[0]["name"]} size={19} /><span><strong>{title}</strong><small>{copy}</small></span></div>)}
      </aside>
      <div className="ns-onboarding-workspace">
        <header className="ns-onboarding-topbar"><span><Icon name="shield-check" size={19} tone={setup.controlCenterPreviewReady ? "success" : "warning"} /> Local setup · {setup.status.replaceAll("_", " ")}</span><span><Icon name="shield" size={19} /> {setup.blockedAuthoritySummary}</span><span><Icon name="user" size={19} /> Operator · You</span></header>
        <main>
          <header><h1>{stage === "sources" ? "Set up your Control Center" : "Review your local setup"}</h1><p>A private, local workspace you can expand deliberately.</p><small>Step {stage === "sources" ? 3 : 4} of 4 · selections are local and unsaved</small></header>
          <div className="ns-onboarding-content">
            {stage === "sources" ? <>
            <Panel title="Select source setup drafts"><p>No source data is read from these controls. Each badge reports the current backend readiness for a matching source kind, or an explicit unknown state.</p><div className="ns-source-list">{sourceDrafts.map(({ name, kinds, reads, blocked }, index) => { const source = sourceItems.find((item) => kinds.some((kind) => item.source_kind.toLowerCase().includes(kind))); const posture = source?.status.replaceAll("_", " ") ?? "not reported"; return <label key={name}><Icon name={["mail", "calendar", "file-text", "cloud-sun", "newspaper"][index] as Parameters<typeof Icon>[0]["name"]} size={22} /><input checked={selected.includes(name)} onChange={(event) => setSelected((current) => event.target.checked ? [...current, name] : current.filter((item) => item !== name))} type="checkbox" /><span><strong>{name} <Badge tone={source?.status === "ready" ? "green" : source ? "orange" : "neutral"}>{posture}</Badge></strong><small>Local unsaved setup draft</small><p><b>Requested future read scope:</b> {reads}</p><p><b>What remains blocked:</b> {blocked}</p></span><button disabled title="Use the checkbox to include or exclude this local draft choice" type="button">Setup later</button></label>; })}</div></Panel>
            <Panel title="Current safety posture"><p>These statements describe this screen and the exact backend posture it displays; they are not global guarantees.</p>{[["shield-check", "Local draft only", "Selections in this view are reversible and are not saved."], ["shield-alert", "Request-scoped authority", "Policy, approval, lease, budget, target, and readiness are evaluated by Python Core where required."], ["link", "Safe refs", "Operator surfaces prefer bounded safe refs and redacted summaries."], ["receipt-text", "Mutation receipts", "Implemented mutations require content-free backend receipts."], ["globe-2", "External writes blocked here", "This screen has no connector or external-write handler."], ["server", "Off-device behavior", "No source authentication or sync is initiated by this setup draft."]].map(([icon, title, copy]) => <div className="ns-safety-row" key={title}><Icon name={icon as Parameters<typeof Icon>[0]["name"]} size={22} /><span><strong>{title}</strong><small>{copy}</small></span></div>)}<hr /><strong>How implemented governed work flows</strong><div className="ns-flow-steps">{[["file-text", "Inspect source"], ["sparkles", "UAA proposal"], ["shield-alert", "Policy / approval"], ["receipt-text", "Receipt"]].map(([icon, title], index) => <Fragment key={title}><div><Icon name={icon as Parameters<typeof Icon>[0]["name"]} size={27} /><strong>{title}</strong></div>{index < 3 ? <Icon name="arrow-right" size={20} /> : null}</Fragment>)}</div><div className="ns-info-callout"><Icon name="globe-2" size={18} /><span><strong>No connector call from this screen</strong><small>No account authentication, source read, external action, or write is initiated.</small></span></div></Panel>
            </> : <><Panel title="Selected read-only sources" icon="circle-check"><p>{selected.length ? selected.join(" · ") : "No optional source selected."}</p><p>These choices are presentation state only. No account authentication, connector runtime, or durable preference was changed.</p></Panel><Panel title="Backend setup posture" icon="shield-check"><p>{setup.repoSafeScope}</p><p><strong>{setup.steps.length}</strong> setup steps · <strong>{readiness.ready_source_count}/{readiness.source_count}</strong> sources ready</p><div className="ns-info-callout"><Icon name="lock" size={18} /><span><strong>Finish remains unavailable</strong><small>{setup.nextSteps[0] ?? readiness.next_safe_action}</small></span></div></Panel></>}
          </div>
        </main>
        <footer><Button disabled={stage === "sources"} icon="arrow-left" onClick={() => setStage("sources")}>Back</Button><p>Selections are local and unsaved.<br />No setup mutation contract is connected.</p>{stage === "sources" ? <><Button onClick={() => { setSelected([]); setStage("review"); }}>Skip sources for now</Button><Button onClick={() => setStage("review")} tone="primary">Continue to review</Button></> : <Button disabled title="No durable setup-finish contract is connected" tone="primary">Finish setup unavailable</Button>}</footer>
      </div>
    </div>
  );
}
