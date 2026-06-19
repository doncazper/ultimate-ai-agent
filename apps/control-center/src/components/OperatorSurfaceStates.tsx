type OperatorSurface =
  | "Chat Shell"
  | "Plans"
  | "Models"
  | "Approvals"
  | "Files"
  | "Runtime"
  | "Evidence"
  | "Settings";

type SurfaceStateKind = "loading" | "error" | "empty" | "blocked" | "denied";

interface SurfaceStateCopy {
  title: string;
  message: string;
  nextAction: string;
}

interface SurfaceConfig {
  eyebrow: string;
  heading: string;
  status: string;
  summary: string;
  states: Record<SurfaceStateKind, SurfaceStateCopy>;
}

const SURFACE_CONFIGS: Record<OperatorSurface, SurfaceConfig> = {
  "Chat Shell": {
    eyebrow: "Operator surface",
    heading: "Chat Shell",
    status: "blocked",
    summary:
      "Dedicated Control Center chat is not enabled. OpenWebUI remains the local shell path, and UAA model output is never authority.",
    states: {
      loading: {
        title: "Loading chat readiness",
        message: "Checking local chat route summaries without opening a model session.",
        nextAction: "Wait for local readiness metadata or inspect Runtime.",
      },
      error: {
        title: "Chat readiness unavailable",
        message:
          "The chat summary could not be loaded safely. Prompt and response details stay hidden.",
        nextAction: "Check Runtime readiness and local gateway status before retrying.",
      },
      empty: {
        title: "No chat receipts",
        message: "No safe chat receipt summaries are available for this shell.",
        nextAction: "Use reviewed local smoke evidence before claiming chat readiness.",
      },
      blocked: {
        title: "Blocked: dedicated chat shell not implemented",
        message:
          "CCC does not provide a chat composer, streaming UI, tool-call UI, or model-output authority.",
        nextAction: "Use OpenWebUI as the scoped local shell and review UAA /v1 readiness evidence.",
      },
      denied: {
        title: "Denied: model output is not authority",
        message:
          "Chat output cannot approve work, execute tools, write memory, or bypass LocalApprovalAuthority.",
        nextAction: "Route any proposed action through policy preview and exact approval.",
      },
    },
  },
  Plans: {
    eyebrow: "Operator surface",
    heading: "Plans",
    status: "partial backend / blocked UI",
    summary:
      "Task decomposition routes exist, but a product Plans surface with durable run lifecycle visibility is not complete.",
    states: {
      loading: {
        title: "Loading plan status",
        message: "Checking safe plan summaries without starting or resuming a run.",
        nextAction: "Wait for durable run metadata or inspect Action Preview.",
      },
      error: {
        title: "Plan status unavailable",
        message: "Plan summaries could not be loaded safely. Sensitive task details stay hidden.",
        nextAction: "Check task decomposition status and retry with safe refs only.",
      },
      empty: {
        title: "No plans listed",
        message: "No durable run or task decomposition summaries are available for this surface.",
        nextAction: "Create plans only through reviewed task decomposition contracts.",
      },
      blocked: {
        title: "Blocked: product Plans loop incomplete",
        message:
          "The UI does not create plans, bind approvals, execute handlers, or claim replay readiness.",
        nextAction: "Use route status and durable-run evidence to scope the next Plans milestone.",
      },
      denied: {
        title: "Denied: no unapproved plan execution",
        message:
          "Plan execution requires exact approval and registered capability binding; this page cannot run handlers.",
        nextAction: "Capture exact approval through approved backend contracts before any mutation.",
      },
    },
  },
  Models: {
    eyebrow: "Operator surface",
    heading: "Models",
    status: "blocked",
    summary:
      "Model readiness is visible through runtime summaries only. GGUF selection and llama.cpp lifecycle controls are not exposed here.",
    states: {
      loading: {
        title: "Loading model readiness",
        message: "Checking safe model readiness summaries without loading or starting a model.",
        nextAction: "Wait for runtime readiness metadata.",
      },
      error: {
        title: "Model readiness unavailable",
        message:
          "Model status could not be loaded safely. Provider and local environment details stay hidden.",
        nextAction: "Inspect local model evidence refs and packaging provenance before retrying.",
      },
      empty: {
        title: "No approved model summaries",
        message: "No approved GGUF or model readiness summaries are available in Control Center.",
        nextAction: "Review M167 evidence and packaging provenance before selecting a model.",
      },
      blocked: {
        title: "Blocked: model selection not implemented",
        message:
          "The UI cannot approve GGUF files, start llama.cpp, change tuning, or claim local model readiness.",
        nextAction: "Use reviewed local model runbooks and evidence matrices outside this UI.",
      },
      denied: {
        title: "Denied: no provider or model authority",
        message:
          "Model/provider output cannot grant approvals, alter settings, write memory, or authorize execution.",
        nextAction: "Keep model use within exact local llama.cpp/OpenWebUI scope.",
      },
    },
  },
  Approvals: {
    eyebrow: "Operator surface",
    heading: "Approvals",
    status: "review-only",
    summary:
      "Approval summaries are inspectable, but Control Center is not the approval authority.",
    states: {
      loading: {
        title: "Loading approval summaries",
        message: "Checking approval metadata without granting or denying anything.",
        nextAction: "Wait for redacted approval summaries.",
      },
      error: {
        title: "Approval summaries unavailable",
        message: "Approval data could not be loaded safely. Approval refs remain identifiers only.",
        nextAction: "Use Python Agent Core authority for final decisions.",
      },
      empty: {
        title: "No approval summaries",
        message: "No approval queue summaries are available from the local source.",
        nextAction: "Review pending work in the approved authority lane.",
      },
      blocked: {
        title: "Blocked: live approval binding incomplete",
        message:
          "The current UI cannot bind live approval capture, expiry, revoke, and replay status end to end.",
        nextAction: "Use exact scoped backend approval contracts for durable approval evidence.",
      },
      denied: {
        title: "Denied: no UI approval grant",
        message: "This UI cannot grant, deny, execute, or bypass approvals.",
        nextAction: "Route final decisions through LocalApprovalAuthority.",
      },
    },
  },
  Files: {
    eyebrow: "Operator surface",
    heading: "Files",
    status: "partial / safe refs",
    summary:
      "File surfaces show safe refs and review packets. Broad browsing, sensitive file content, and unapproved mutation remain unavailable.",
    states: {
      loading: {
        title: "Loading file summaries",
        message: "Checking safe file refs without reading sensitive file content.",
        nextAction: "Wait for redacted file metadata.",
      },
      error: {
        title: "File summaries unavailable",
        message:
          "File metadata could not be loaded safely. Location details and sensitive file content stay hidden.",
        nextAction: "Retry with safe refs and review redaction status.",
      },
      empty: {
        title: "No file summaries",
        message: "No safe file refs or redacted review packets are available.",
        nextAction: "Validate safe refs before requesting file review.",
      },
      blocked: {
        title: "Blocked: broad file workbench incomplete",
        message:
          "The UI cannot browse arbitrary files, apply patches, or claim rollback evidence from local state alone.",
        nextAction: "Use exact file/path binding and rollback receipts before mutation.",
      },
      denied: {
        title: "Denied: no unapproved file mutation",
        message:
          "File writes require exact approval, idempotency, audit links, rollback refs, and verifier coverage.",
        nextAction: "Capture approval through the scoped file mutation lane.",
      },
    },
  },
  Runtime: {
    eyebrow: "Operator surface",
    heading: "Runtime",
    status: "status only",
    summary:
      "Runtime panels show local readiness and validation summaries only. Lifecycle operations are not exposed.",
    states: {
      loading: {
        title: "Loading runtime status",
        message: "Checking local readiness and manifest summaries without starting runtime work.",
        nextAction: "Wait for health, manifest, and readiness summaries.",
      },
      error: {
        title: "Runtime status unavailable",
        message: "Runtime status could not be loaded safely. Local environment details stay hidden.",
        nextAction: "Check the local backend and rerun frontend verification.",
      },
      empty: {
        title: "No runtime entries",
        message: "No runtime capability entries are available in the local summary.",
        nextAction: "Inspect the API manifest and runtime readiness report.",
      },
      blocked: {
        title: "Blocked: lifecycle controls not scoped",
        message:
          "Control Center cannot launch, stop, connect, or supervise llama.cpp from this surface.",
        nextAction: "Use reviewed local runtime settings and evidence before any lifecycle milestone.",
      },
      denied: {
        title: "Denied: no hidden runtime authority",
        message:
          "Speed or convenience cannot bypass PolicyEngine, LocalApprovalAuthority, or route side-effect checks.",
        nextAction: "Keep runtime actions disabled until an explicit scoped milestone approves them.",
      },
    },
  },
  Evidence: {
    eyebrow: "Operator surface",
    heading: "Evidence",
    status: "redacted summary-only",
    summary:
      "Evidence surfaces show safe refs, redacted summaries, receipts, events, and Foundation Gate summaries.",
    states: {
      loading: {
        title: "Loading evidence summaries",
        message: "Checking safe evidence refs without exposing sensitive source details.",
        nextAction: "Wait for redacted receipt, event, and audit summaries.",
      },
      error: {
        title: "Evidence summaries unavailable",
        message: "Evidence data could not be loaded safely. Sensitive source details stay hidden.",
        nextAction: "Use verifier output and redacted refs only.",
      },
      empty: {
        title: "No evidence summaries",
        message: "No redacted evidence, receipt, event, or audit summaries are available.",
        nextAction: "Run the required verifiers before making release claims.",
      },
      blocked: {
        title: "Blocked: release evidence index incomplete",
        message:
          "The UI does not yet provide a complete release evidence index, latency report, or rollback status.",
        nextAction: "Use docs and verifier outputs until durable evidence routes are scoped.",
      },
      denied: {
        title: "Denied: no sensitive evidence display",
        message: "Sensitive source material, credentials, and private content are never displayed.",
        nextAction: "Collect only safe refs and redacted summaries.",
      },
    },
  },
  Settings: {
    eyebrow: "Operator surface",
    heading: "Settings",
    status: "blocked",
    summary:
      "Settings are visible as disabled posture only. There is no settings mutation route or runtime authority toggle.",
    states: {
      loading: {
        title: "Loading settings posture",
        message: "Checking disabled-by-default settings metadata without applying changes.",
        nextAction: "Wait for status summaries.",
      },
      error: {
        title: "Settings posture unavailable",
        message: "Settings posture could not be loaded safely. Configuration details stay hidden.",
        nextAction: "Inspect documented defaults and route status before retrying.",
      },
      empty: {
        title: "No settings manifest",
        message: "No dedicated settings manifest is implemented for Control Center.",
        nextAction: "Use documented defaults and scoped milestone requirements.",
      },
      blocked: {
        title: "Blocked: settings routes not implemented",
        message:
          "There is no UI path to enable shell, browser, connector, plugin, mobile, model, memory, or runtime authority.",
        nextAction: "Define a scoped settings milestone before any setting can mutate state.",
      },
      denied: {
        title: "Denied: no authority toggle",
        message:
          "Control Center cannot create broad autonomy, public distribution, production runtime, or connector write authority.",
        nextAction: "Keep authority disabled until explicit approval, audit, rollback, and tests exist.",
      },
    },
  },
};

export function OperatorSurfaceStates({ surface }: { surface: OperatorSurface }) {
  const config = SURFACE_CONFIGS[surface];
  return (
    <section
      className="operator-surface-states"
      aria-labelledby={`${surfaceId(surface)}-states-heading`}
    >
      <div className="section-heading compact-heading">
        <div>
          <p className="eyebrow">{config.eyebrow}</p>
          <h3 id={`${surfaceId(surface)}-states-heading`}>{config.heading} states</h3>
        </div>
        <span className="status-pill compact">{config.status}</span>
      </div>
      <p className="section-copy">{config.summary}</p>
      <div className="surface-state-grid" aria-label={`${surface} accessible state coverage`}>
        {(["loading", "error", "empty", "blocked", "denied"] as const).map((kind) => (
          <SurfaceStateCard key={kind} kind={kind} copy={config.states[kind]} />
        ))}
      </div>
    </section>
  );
}

export function OperatorSurfacePlaceholderPanel({ surface }: { surface: OperatorSurface }) {
  const config = SURFACE_CONFIGS[surface];
  return (
    <section className="page-section" aria-labelledby={`${surfaceId(surface)}-heading`}>
      <div className="section-heading">
        <div>
          <p className="eyebrow">{config.eyebrow}</p>
          <h2 id={`${surfaceId(surface)}-heading`}>{config.heading}</h2>
        </div>
        <span className="status-pill compact">{config.status}</span>
      </div>
      <p className="section-copy">{config.summary}</p>
      <p className="safe-copy">
        This surface is operator-facing status only. It does not run actions, does not grant
        approvals, does not change settings, does not call models, does not expose sensitive source
        material, and does not create completion evidence.
      </p>
      <OperatorSurfaceStates surface={surface} />
    </section>
  );
}

function SurfaceStateCard({ kind, copy }: { kind: SurfaceStateKind; copy: SurfaceStateCopy }) {
  const role = kind === "error" ? "alert" : "status";
  return (
    <article className={`surface-state-card ${kind}`} role={role}>
      <span className="surface-state-kind">{kind}</span>
      <strong>{copy.title}</strong>
      <p>{copy.message}</p>
      <small>Next safe action: {copy.nextAction}</small>
    </article>
  );
}

function surfaceId(surface: OperatorSurface): string {
  return surface.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}
