# Route Inventory

Current active baseline: **v0.104.0**

Current OpenAPI path count: `252`.

The API route inventory is generated from FastAPI route metadata and exposed by
`/api/manifest`. The manifest route count is the authoritative current count.
Historical release notes may preserve older route counts for audit history.

Each route declares:

- `path`
- `method`
- `operation_id`
- `tags`
- `summary`
- `validation_only`
- `side_effect_class`
- `route_classification`
- `auth_posture`
- `approval_posture`
- `idempotency_required`
- `idempotency_posture`
- `idempotency_policy_ref`
- `requires_auth_future`
- `blocked_from_production`

UAA-P1-080 classification adds a public/protected route inventory view using:

- `public_metadata`
- `local_readonly`
- `local_sensitive`
- `mutating_requires_authority`

This vocabulary is implemented in `/api/manifest` and the frozen route
inventory fixture. Current route metadata also exposes side-effect classes,
auth posture, approval posture, idempotency posture, rate-limit posture, and
blocked-from-production posture.

Current route classification summary:

| Classification | Count |
|---|---:|
| `public_metadata` | 3 |
| `local_readonly` | 28 |
| `local_sensitive` | 171 |
| `mutating_requires_authority` | 50 |

Allowed current side-effect classes are:

- `none`
- `validation_only`
- `local_dev_workspace_only`
- `governed_network_read_only`

Production runtime side effects remain blocked unless an exact scoped milestone
grants reviewed authority and updates OpenAPI, route side-effect
classification, Foundation Gate checks, tests, docs, and rollback guidance.

UAA-P1-081 implements centralized security-header posture for handled FastAPI
responses: `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options`,
`Content-Security-Policy`, `Permissions-Policy`, and HTTPS-only
`Strict-Transport-Security`.

UAA-P1-082 implements explicit loopback CORS allowlist posture for local Control
Center dev/preview origins only: `http://localhost:5173`,
`http://127.0.0.1:5173`, `http://[::1]:5173`,
`http://localhost:4173`, `http://127.0.0.1:4173`, and
`http://[::1]:4173`. Wildcard CORS and CORS credentials remain denied, and CORS
does not grant auth or route authority.

UAA-P1-083 implements local protected-route bearer gate posture for non-public
route classifications. `GET /health`, `GET /version`, `GET /api/manifest`, and
`GET /openapi.json` remain public metadata; `local_readonly`,
`local_sensitive`, and `mutating_requires_authority` routes fail closed unless
the configured local bearer is sent or the explicit local-dev bypass is set.
This is not enterprise auth, OAuth, a password flow, production authority, or a
public beta claim.

UAA-P1-084 implements mutating-route idempotency enforcement audit posture.
Routes classified as `mutating_requires_authority` now require
`X-UAA-Idempotency-Key` or `X-UAA-Idempotency-Ref` before the mutating handler
can run. `/api/manifest` and the frozen route inventory expose
`idempotency_required`, `idempotency_posture`, and `idempotency_policy_ref`.
The Today-to-Action envelope promotion route additionally requires active
`workspace/draft` AuthorityLease scope and records authority decision refs
before local review-only Action envelope state is written.
This is not durable dedupe storage, exactly-once execution, replay execution,
mutation authority, production authority, or a public beta claim.

UAA-P1-085 implements targeted local fixed-window rate-limit posture for
model/chat, task decomposition, action preview/proposal, turn-router preview,
Action Inbox decisions,
Today-to-Action envelope promotion, Chat durable receipts/handoffs, Memory
Review decision receipts, Memory context-pack internal Action proposal receipts,
Memory feedback receipts, the exact-approved provider credential validation
capability, the scoped provider capability route, governed runtime pilot
mutation routes, and local model validation route groups.
The extension disabled-install record and rollback routes are targeted as one
exact local metadata receipt group; rollback deletes only the local disabled
record and writes a redacted delete receipt.
`/api/manifest` and the frozen route inventory expose
`rate_limit_targeted`, `rate_limit_posture`, `rate_limit_policy_ref`, and
`rate_limit_group`. This is not auth, distributed quota, billing, production
authority, or a public beta claim.

Governed Runtime Pilot Phase 07 keeps `/api/runtime/*` governed by contract and
storage metadata while exposing configured local loopback model calls, one
allowlisted read-only command status capability, and Action Inbox approved
focused pytest, repo verifier, frontend check, and repo-doctor command execution
through `RuntimeGateway` only when the required AuthorityLease scope validates,
with CLI/Control Center/evidence timeline parity for status, capabilities,
invocation, receipt,
safe-disable, approval decision inspection, command root pinning, configured
endpoint matching, receipt-detail execution truth, and approval preflight.
`GET /api/runtime/governed-product-pilot-profile` exposes the Governed Product
Pilot authority profile as a protected read-only Python Core read model for
AuthorityLease-gated capability posture, portable evidence envelopes, durable
orchestration posture, and blocked authority refs.
`GET /api/runtime/authority-state#authority_lane_catalog` exposes Authority
Lane Catalog V1 within the existing authority-state read model. It normalizes
the first exact governed lanes across verifier commands, code proposal/apply
readiness, WebAccessGateway evidence preview, Memory Review decisions,
provider readiness, and extension catalog review with safe refs, approval
scope, idempotency, receipt, rollback/safe-disable, and active policy decision
posture. It is inspection-only and creates no new execution route.
`GET /api/runtime/authority-domain-readiness` exposes a focused read-only
AuthorityLease domain readiness model derived from the same authority-state
decision catalog, active leases, and mode catalog. It gives one row per target
domain with active lease refs, decision outcomes, issue-ready modes, blocked
reason refs, and unsupported adapter refs; it performs no mutation, execution,
adapter call, or authority grant.
`GET /api/runtime/staged-orchestration` exposes a protected read-only Python
Core staged orchestration plan/checkpoint/dependency read model and grants no
scheduling, dispatch, background autonomy, model call, browser action,
connector write, shell/subprocess authority, or production authority.
`GET /api/runtime/prepared-turn` exposes a protected read-only Python Core
prepared-turn read model over turn contract, route binding, readiness, durable
run, and evidence refs without persisting raw prompt text or granting runtime
authority.
`GET /api/runtime/parity-loop` exposes a protected read-only Python Core final
runtime parity-loop read model over prepared turn, route decision, durable run,
staged orchestration, provider evidence, Action Inbox approval, receipt, signed
evidence, and blocked-state refs without executing work or granting runtime
authority.
`GET /api/runtime/delegation-adapter` exposes a protected read-only Python Core
Hermes Runtime Adoption Phase 01 delegation adapter readiness model. It shows
runtime identity refs, endpoint posture, authority mode, capability refs,
health refs, proof refs, blocked reasons, next safe actions, CLI parity, and
Control Center binding while keeping live run submission, runtime model calls,
provider SDK calls, tool execution, shell/subprocess execution, browser
automation, connector writes, background autonomy, production authority, and
raw prompt/response/provider payload/log/local-path persistence blocked.
`GET /api/runtime/interface-mode` exposes a protected Python Core
`runtime_interface_mode.v1` read model for optional Hermes interface mode. It
defaults to `disabled`, leaving UAA UAA-native with no Hermes CLI discovery,
readiness probe, context projection, or chat execution unless
`UAA_HERMES_INTERFACE_MODE_ENABLED=1` is explicitly set. It also reports opt-in
`shell_guarded`, `operator_override`, and `pure_hermes_pass_through` posture,
exact argv shapes, blocked unsafe flags, and candidate-only Memory update
policy.
`GET /api/runtime/hermes/context-pack` exposes a protected Python Core
`hermes_context_pack.v1` read model. While disabled, it reports
`projection_enabled=false` and zero projected sections. When explicitly enabled,
it contains curated summaries from Memory, CRM, Chat, Cowork/Plans, Today,
Action Inbox, Evidence, Proof, and Sources with provenance refs, why-shown refs,
evidence/proof refs, and explicit false flags for raw record, transcript, path,
log, credential, and unbounded private content exposure.
`POST /api/runtime/hermes/chat` exposes the exact guarded Hermes CLI chat lane
for `hermes chat --query ... --quiet --source uaa-control-center`. It is
classified `mutating_requires_authority`, requires active `workspace/execute`
AuthorityLease scope before Hermes CLI discovery or subprocess execution,
requires idempotency, returns a redacted receipt with authority decision refs,
hashes query content, summarizes output, and blocks yolo, oneshot, arbitrary
args/toolsets, shell strings, raw persistence, direct Memory writes, browser
automation, connector writes, and production authority.
`POST /api/runtime/local-model/call` is a mutating-requires-authority governed
runtime lane for configured loopback local-model calls only. It requires active
`provider_model_calls/execute` AuthorityLease scope under Full machine access
before transport execution, records metadata-only/redacted receipts, treats
model output as untrusted proposal text, and denies remote provider SDK calls,
tools/functions, streaming, connector writes, browser automation, billing, and
production authority.
Runtime command execution routes refresh active AuthorityLease scope before
process start. If a previously approved Action Inbox command no longer has an
active `workspace/execute` lease, execution records a blocked receipt instead
of relying on stale approval or policy refs.
Runtime invocation lifecycle routes are authority-mapped for cockpit
inspection: invocation creation is workspace draft/record-only, approval
binding and approved execution are workspace execute with exact approval and
lease gates, and safe-disable is a local safety control that only reduces
runtime authority.
`GET /api/runtime/capability-discovery` exposes a protected read-only Python
Core Hermes Runtime Adoption Phase 02 capability discovery posture for models,
runs, events, approvals, sessions, skills, toolsets, jobs, and blocked actions.
It is a static snapshot with safe refs and a snapshot hash ref only; runtime
support metadata cannot grant UAA permission, and stale or unreachable runtime
state degrades to blocked. The same route now carries Phase 09 runtime toolset
capability posture for runtime support versus UAA allowance states while
keeping runtime tool invocation, Hermes toolset enablement, toolset config
mutation, raw tool payload persistence, and production authority disabled.
`GET /api/runtime/tool-registry` exposes a protected read-only Python Core
Hermes Runtime Adoption Phase 10 tool registry availability posture for
UAA-native preview tools and delegated Hermes/Codex/Claude/MCP/future runtime
tool references. It records availability, configured status, authority class,
side-effect class, risk, blocker refs, proof refs, next safe actions,
AuthorityState mapping/decision refs, and unsupported adapter refs while
keeping tool invocation, remote discovery, live web fetch, provider/model call,
plugin import, connector write activation, raw tool payload persistence, and
production authority disabled.
`GET /api/runtime/session-search` exposes a protected read-only Python Core
Hermes Runtime Adoption Phase 12 session/run search posture. It returns safe
refs, bounded summaries, proof refs, attachable context refs, and memory
separation posture only, now bound to AuthorityState as
`lane-ref:runtime-session-search-read-model` under Read-only `workspace/read`
with route/CLI/mapping/catalog/decision/reason refs and unsupported adapter
refs. Raw transcript persistence, raw prompt/response exposure, semantic
provider calls, embedding/vector indexing, hidden context injection, memory
writes, action execution, live fetch, connector writes, background indexing,
and production authority remain blocked.
`GET /api/runtime/session-lineage` exposes a protected read-only Python Core
Hermes Runtime Adoption Phase 19 session lineage and fork posture bound to
`lane-ref:runtime-session-lineage-read-model` through AuthorityState. It
returns safe parent/child, user request, task, run, proof, branch, reason,
redacted fork-envelope, retrieval-log, compare-view, verifier, AuthorityState
mapping/decision refs, unsupported adapter refs, and blocked authority refs
only. Raw transcript cloning, raw prompt/response persistence, hidden context
injection, runtime dispatch, provider/model calls, connector writes,
shell/subprocess execution, browser automation, and production authority remain
blocked.
`GET /api/runtime/virtual-provider-moa` exposes a protected read-only Python
Core Hermes Runtime Adoption Phase 20 virtual provider Mixture-of-Agents
posture bound to `lane-ref:runtime-virtual-provider-moa-read-model` through
AuthorityState. It returns preset, agent-slot, route-decision trace,
cost-estimate, approval-mode, output-envelope, comparison-proof, safe-disable,
verifier, AuthorityState mapping/decision refs, unsupported adapter refs, and
blocked authority refs only. Live model fan-out, provider SDK calls, external
runtime dispatch, hidden advisor prompts, model-output authority, connector
writes, shell/subprocess execution, browser automation, and production
authority remain blocked.
`GET /api/runtime/usage-cost-analytics` exposes a protected read-only Python
Core Hermes Runtime Adoption Phase 22 usage and cost analytics posture bound to
`lane-ref:runtime-usage-cost-analytics-read-model` through AuthorityState. It
returns redacted accounting record refs, runtime/provider/model refs,
task-value refs, receipt refs, estimate refs, bounded usage estimates, latency
estimates, cost minor units, AuthorityState mapping/decision refs, unsupported
adapter refs, proof refs, verifier refs, and blocked authority refs only.
Billing actions, provider calls, provider SDK calls, live pricing fetches,
operator export, raw prompt/response/provider material persistence,
model-output authority, and production authority remain blocked.
`GET /api/runtime/prompt-stability-tiers` exposes a protected read-only Python
Core Hermes Runtime Adoption Phase 23 prompt stability tier posture bound to
`lane-ref:runtime-prompt-stability-tiers-read-model` through AuthorityState. It
returns prompt tier refs, manifest refs, redacted hash refs, cache policy refs,
safe source refs, AuthorityState mapping/decision refs, unsupported adapter
refs, proof refs, verifier refs, next-safe-action refs, and blocked authority
refs only. Raw prompt/response persistence, hidden prompt/context injection,
model calls, provider SDK calls, cache writes, model-output authority, and
production authority remain blocked.
`GET /api/runtime/context-budget-pressure` exposes a protected read-only Python
Core Hermes Runtime Adoption Phase 24 context budget pressure posture bound to
`lane-ref:runtime-context-budget-pressure-read-model` through AuthorityState.
It returns context budget segment refs, pressure levels, warning refs,
review-only trimming and summary proposal refs, source refs, retrieval log
refs, AuthorityState mapping/decision refs, unsupported adapter refs, proof
refs, verifier refs, next-safe-action refs, and blocked authority refs only.
Hidden compression, automatic context mutation, model summarization calls,
context injection, provider SDK calls, cache writes, raw context/prompt/
response/provider material persistence, and production authority remain
blocked.
`GET /api/runtime/hardline-command-blocklist` exposes a protected read-only
Python Core Hermes Runtime Adoption Phase 25 hardline command blocklist
posture bound to `lane-ref:runtime-hardline-command-blocklist-read-model`
through AuthorityState for inspection only. It returns command-shape
classification refs, denied category refs, allowed shape counts, hardline rule
refs, AuthorityState mapping/decision refs, unsupported adapter refs, proof
refs, verifier refs, next-safe-action refs, and blocked authority refs only.
Command execution, raw command strings, raw command text/output persistence,
hardline floor override, and production authority remain blocked.
`GET /api/runtime/managed-scope-policy` exposes a protected read-only Python
Core Hermes Runtime Adoption Phase 27 managed scope policy posture. It returns
pinned local policy source refs, source kinds, precedence, checksum refs, drift
warning refs, rollback refs, admin/operator proof refs, verifier refs,
next-safe-action refs, blocked authority refs, AuthorityState route/CLI/mapping/
catalog/decision/reason refs, unsupported adapter refs, and decision-bound
snapshot hashes for `lane-ref:runtime-managed-scope-policy-read-model`. System
config writes, privileged writes, MDM delivery, managed secrets, unsigned
runtime config overrides, raw config/local path/account/credential material
persistence, production enforcement, and production authority remain blocked.
`GET /api/runtime/doctor-diagnostics` exposes a protected read-only Python Core
Hermes Runtime Adoption Phase 28 runtime doctor diagnostics posture. It returns
diagnostic refs, setup/runtime/provider/tool/protected-material/service/
authority status refs, CLI refs, proof refs, next-safe-action refs, blocked
authority refs, AuthorityState route/CLI/mapping/catalog/decision/reason refs,
unsupported adapter refs, and decision-bound snapshot hashes for
`lane-ref:runtime-doctor-diagnostics-read-model`. Installs, service starts,
credential writes, runtime config mutation, raw log/local path persistence,
provider payload persistence, Control Center authority minting, and production
authority remain blocked.
`GET /api/runtime/session-continuity` exposes a protected read-only Python Core
Hermes Runtime Adoption Phase 29 AuthorityState-bound multi-surface session
continuity posture. It returns session refs, source labels, staleness refs,
conflict refs, proof refs, verifier refs, blocked authority refs,
AuthorityState route/CLI/mapping/catalog/decision/reason refs, unsupported
adapter refs, and a decision-bound snapshot hash for
`lane-ref:runtime-session-continuity-read-model`. External messaging gateways,
account sync, connector writes, remote sessions, raw transcript/provider payload
persistence, Control Center authority minting, and production authority remain
blocked.
`GET /api/runtime/mcp-catalog-filtering` exposes a protected read-only Python
Core Hermes Runtime Adoption Phase 30 AuthorityState-bound MCP catalog filtering
posture. It returns metadata catalog refs, tool filter contracts, blocked
activation states, proof refs, verifier refs, blocked authority refs,
AuthorityState route/CLI/mapping/catalog/decision/reason refs, unsupported
adapter refs, and a decision-bound snapshot hash for
`lane-ref:runtime-mcp-catalog-filtering-read-model`. MCP install, subprocess
runtime, OAuth login, tool invocation, connector writes, raw manifest
persistence, and Control Center authority minting remain blocked.
`GET /api/runtime/background-jobs` exposes a protected read-only Python Core
Hermes Runtime Adoption Phase 31 background job posture. It returns durable job
proposal refs, schedule policies, approval scope refs, idempotency refs,
safe-disable refs, receipt plans, failure handling refs, proof refs, verifier
refs, AuthorityState route/CLI/mapping/catalog/decision/reason refs,
unsupported adapter refs, and blocked authority refs only. The
`lane-ref:background-autonomy-scoped` decision is denied because worker and
supervisor adapters are unsupported. Schedulers, workers, run-now, pause/resume
mutation, autonomous retries, external delivery, provider calls, shell
execution, and connector writes remain blocked.
`GET /api/runtime/subagent-isolation` exposes a protected read-only Python Core
Hermes Runtime Adoption Phase 32 subagent isolation posture. It returns role
refs, scope envelopes, context/tool/memory grant refs, budget refs,
kill-switch refs, review artifacts, proof refs, verifier refs, AuthorityState
route/CLI/mapping/catalog/decision/reason refs, unsupported adapter refs, and
blocked authority refs only. The
`lane-ref:runtime-subagent-isolation-live-dispatch` decision is denied because
live dispatch/tool-sharing/memory-transfer adapters are unsupported. Live
dispatch, background fan-out, cross-agent memory transfer, tool sharing,
autonomous delegation, raw transcript persistence, and raw agent-output
persistence remain blocked.
`GET /api/runtime/worktree-per-agent` exposes a protected read-only Python Core
Hermes Runtime Adoption Phase 33 worktree-per-agent posture. It returns lane
refs, workspace scope refs, branch proposal refs, worktree refs, checkpoint
plans, Git receipt plans, rollback plans, proof refs, verifier refs,
AuthorityState route/CLI/mapping/decision refs for the implementer/reviewer/
verifier lanes, and blocked authority refs only. The three read/prepare lane
decisions are allowed by the active read-only lease, but Git worktree
create/delete, branch mutation, file writes, commits, pushes, raw path
persistence, shell execution, and provider calls remain blocked.
`GET /api/runtime/lsp-diagnostics` exposes a protected read-only Python Core
Hermes Runtime Adoption Phase 34 semantic diagnostics proof posture. It returns
diagnostic refs, safe source scope refs, evidence refs, receipt-plan refs,
proof refs, verifier refs, promotion refs, redaction refs, AuthorityState
route/CLI/mapping/catalog/decision/reason refs, unsupported adapter refs, and
blocked authority refs only. The
`lane-ref:runtime-lsp-diagnostics-evidence` decision is denied because
language-server launch/file-read/diagnostic-extraction adapters are
unsupported. Language-server launch, dependency install, shell execution, file
reads/writes, provider calls, raw path persistence, and raw
diagnostic payload persistence remain blocked.
`GET /api/runtime/preview-rail` exposes a protected read-only Python Core
Hermes Runtime Adoption Phase 35 right preview rail posture. It returns safe
source refs, source-classification refs, bounded preview refs, redaction policy
refs, attach-plan refs, receipt-plan refs, proof refs, verifier refs,
promotion refs, AuthorityState route/CLI/mapping/catalog/decision/reason refs,
unsupported adapter refs, and blocked authority refs only. The
`lane-ref:runtime-preview-rail-safe-ref-read-model` decision is allowed for
safe-ref `workspace/read` inspection only. Browser automation, screenshot
capture, raw sensitive file display, direct runtime payload rendering, file
reads/writes, shell execution, provider calls, Control Center authority
minting, raw path persistence, raw file-content persistence, and raw runtime
payload persistence remain blocked.
`GET /api/runtime/slash-command-registry` exposes a protected read-only Python
Core Hermes Runtime Adoption Phase 36 slash command registry posture. It
returns command refs, trigger labels, command status, authority class,
side-effect class, docs refs, approval policy refs, idempotency policy refs,
receipt-plan refs, proof refs, verifier refs, promotion refs, and blocked
authority refs only. Chat slash-command execution, runtime invocation, state
mutation, shell execution, provider calls, browser automation, connector
writes, Control Center authority minting, raw prompt persistence, and raw
response persistence remain blocked.
`GET /api/runtime/interrupt-redirect` exposes a protected read-only Python
Core Hermes Runtime Adoption Phase 37 interrupt/redirect run-control posture.
It returns pause, stop, redirect, revise, and recovery proposal refs, approval
scope refs, idempotency refs, receipt-plan refs, recovery-state refs, proof
refs, verifier refs, promotion refs, and blocked authority refs only. Live
stop POST, process kill, runtime mutation, background autonomy, shell
execution, provider calls, browser automation, connector writes, Control
Center authority minting, raw runtime payload persistence, and raw log
persistence remain blocked.
`GET /api/runtime/logging-profile` exposes a protected read-only Python Core
Hermes Runtime Adoption Phase 38 logging profile posture. It returns quiet,
redacted troubleshooting, and forensic safe-ref profile refs, flag scope refs,
TTL policy refs, retention policy refs, redaction policy/verifier refs, proof
refs, verifier refs, promotion refs, and blocked authority refs only. Verbose
toggling, raw log persistence, raw prompt/response/provider payload/path
persistence, credential persistence, remote telemetry export, and background
log streaming remain blocked.
`GET /api/runtime/result-classification` exposes a protected read-only Python
Core Hermes Runtime Adoption Phase 39 result taxonomy posture. It returns
evidence, mutation, warning, blocked, proposal, diagnostic, and untrusted-data
class refs, provenance policy refs, redaction policy refs, receipt requirement
refs, proof binding refs, verifier refs, promotion refs, and blocked authority
refs only. Treating tool output as truth, treating output as action authority,
mutation without receipt, unverified evidence promotion, raw output
persistence, and provider payload persistence remain blocked.
`GET /api/runtime/voice-media-posture` exposes a protected read-only Python
Core Hermes Runtime Adoption Phase 41 voice/media posture. It returns voice
input, speech-to-text, text-to-speech, image input, image generation, media
upload, and external media delivery lane refs, consent refs,
device-permission refs, redaction refs, receipt-plan refs, proof refs,
verifier refs, authority refs, and blocked authority refs only. Microphone
access, camera access, file/media upload, transcription, media generation,
provider calls, external delivery, media material persistence, and Control
Center authority minting remain blocked.
`GET /api/runtime/messaging-gateway-posture` exposes a protected read-only
Python Core Hermes Runtime Adoption Phase 42 messaging gateway posture. It
returns email, Slack, Telegram, SMS, Discord, and generic webhook readiness
labels, connector label refs, inbound refs, outbound write label refs, OAuth
refs, webhook refs, account-sync refs, redaction refs, proof refs, authority
refs, unsupported adapter refs, and blocked authority refs only. Connector
runtime, connector reads, sends, OAuth, webhook exposure, account sync,
external writes, raw message persistence, and Control Center authority minting
remain blocked.
`GET /api/runtime/remote-execution-posture` exposes a protected read-only
Python Core Hermes Runtime Adoption Phase 43 remote execution posture. It
returns local workspace, local container, secure host, cloud sandbox,
serverless worker, and remote GPU backend labels, workspace boundary refs,
credential policy refs, network policy refs, receipt refs, budget refs,
rollback refs, kill-switch refs, proof refs, authority refs, unsupported
adapter refs, and blocked authority refs only. Remote execution, host access,
cloud sandboxes, remote command sessions, file sync, protected material access,
remote process control, credential material persistence, and Control Center
authority minting remain blocked.
`GET /api/runtime/plugin-metadata-posture` exposes a protected read-only
Python Core Hermes Runtime Adoption Phase 44 plugin metadata posture. It
returns adapter, hook, tool, memory provider, context engine, UI extension, and
skill bundle metadata contract labels, reviewed manifest refs, static scan refs,
sandbox refs, activation grant refs, rollback refs, safe-disable refs, receipt
refs, proof refs, authority refs, unsupported adapter refs, and blocked
authority refs only. Runtime imports, hooks, package installation, marketplace
content execution, plugin code execution, connector writes, provider calls, raw
manifest persistence, and Control Center authority minting remain blocked.
`GET /api/runtime/skill-marketplace-posture` exposes a protected read-only
Python Core Hermes Runtime Adoption Phase 45 skill marketplace posture. It
returns discovery signal, quarantine, review, adaptation proposal, UAA-owned
adaptation, activation grant, and execution-block labels, AuthorityState mapping
refs, decision refs, reason refs, unsupported adapter refs, receipt refs, proof
refs, and blocked authority refs only. External code execution, direct
marketplace installation, runtime import, automatic skill writes, provider
calls, browser automation, connector writes, raw marketplace payload
persistence, and Control Center authority minting remain blocked.
`GET /api/runtime/context-references` exposes a protected read-only Python Core
Hermes Runtime Adoption Phase 16 context-reference posture bound to
`lane-ref:runtime-context-references-read-model` through AuthorityState. It
returns safe-ref grammar, preview refs, budget estimates, why-included refs,
AuthorityState mapping/decision refs, unsupported adapter refs, and blocked
URL/live-fetch posture for file, folder, diff, URL evidence, run, proof, task,
memory, CRM object, and issue refs. Live URL fetch, raw path persistence, raw
file-content persistence, protected config reads, automatic context injection,
provider/model calls, connector writes, shell/subprocess execution, browser
automation, and production authority remain blocked.
`GET /api/runtime/checkpoint-rollback` exposes a protected read-only Python Core
Hermes Runtime Adoption Phase 18 checkpoint/rollback posture bound to
`lane-ref:runtime-checkpoint-rollback-read-model` through AuthorityState. It
returns safe checkpoint, receipt, rollback-plan, AuthorityState
mapping/decision refs, unsupported adapter refs, proof, verifier, and blocked
authority refs only; rollback execution, broad filesystem snapshots, Git
mutation, raw path/content persistence, and production authority remain
blocked.
`GET /api/runtime/run-events` exposes a protected read-only Python Core Hermes
Runtime Adoption Phase 03 run/event posture for external runtime lifecycle
state, UAA durable run state mapping, event-ref grammar, proof binding, blocked
stop posture, approval-wait proposals, and the AuthorityState mapping/catalog/
decision/reason/unsupported-adapter refs for
`lane-ref:runtime-run-events-read-model`. It does not create delegated runs,
stop delegated runs, resolve runtime approvals, or stream live events.
`GET /api/runtime/approval-bridge` exposes a protected read-only Python Core
Hermes Runtime Adoption Phase 04 approval bridge posture for approval
envelopes, Action Inbox projection refs, proof refs, denial/timeout/scope-
mismatch previews, default-deny timeout posture, and the AuthorityState
mapping/catalog/decision/reason/unsupported-adapter refs for
`lane-ref:runtime-approval-bridge-read-model`. It does not send approval,
denial, timeout, or scope-mismatch resolutions to Hermes or any delegated
runtime.
`GET /api/runtime/streaming-progress` exposes a protected read-only Python Core
Hermes Runtime Adoption Phase 05 streaming-progress posture for ordered,
redacted event previews, stale/disconnected stream state, event hash refs,
proof refs, and the AuthorityState mapping/catalog/decision/reason/unsupported-
adapter refs for `lane-ref:runtime-streaming-progress-read-model`. It does not
open SSE/WebSocket subscriptions, reconnect to Hermes, ingest live runtime
events, or persist raw runtime/tool/generated/log/prompt/response payloads.
`GET /api/runtime/profiles` exposes a protected read-only Python Core Hermes
Runtime Adoption Phase 06 profile isolation posture for UAA-owned profile refs
that stay separate from delegated runtime profile refs, safe display labels,
role, configured status, authority posture, workspace and memory scope refs,
toolset posture, profile health, blocked reasons, proof refs, AuthorityState
route/CLI/mapping/catalog/decision/reason refs, unsupported adapter refs, and a
decision-bound snapshot hash for
`lane-ref:runtime-profile-isolation-read-model`. It does not create profiles,
delete profiles, write runtime config, copy sensitive material, change runtime
defaults, live-activate delegated profiles, execute tools, call providers, write
memory, allow cross-profile authority bleed, expose raw delegated profile names,
or expose workspace paths.
Capability, invocation, policy, approval-ref, receipt, and safe-disable records
store safe refs and redacted metadata only; model output is untrusted proposal
text, and command output is redacted and bounded. Remote provider/model calls,
arbitrary shell/subprocess execution outside implemented AuthorityLease-gated
command capabilities, arbitrary focused tests, repo verifier/frontend check, or
repo-doctor execution outside implemented AuthorityLease-gated capabilities,
arbitrary adapter execution, browser automation, connector writes, plugin
runtime import, remote execution, raw
prompt/response/command output/local path/env persistence, production authority,
and public release claims remain blocked.

UAA-P1-086 implements route inventory enforcement checks across OpenAPI,
`/api/manifest`, the frozen fixture, and the Control Center route-status
manifest. These checks add no new runtime authority.

FCC-V1-001 updates the frozen route inventory fixture to
`uaa-api-route-inventory.v4` and makes `auth_posture` plus `approval_posture`
manifest-visible for every route. Mutating routes must expose local bearer
auth posture, approval-before-mutation posture, idempotency posture, and
rate-limit posture before real Founder Loop mutation routes can land.
Duplicate replay behavior remains a route-owner contract; FCC-V1-002 implements
it for Action Inbox decision routes, FCC-ACTION-001a implements it for the
exact local task commit lane, FCC-V1-004 implements it for Chat receipt/handoff
routes, and FCC-V1-005 implements it for Memory Review decision receipt routes.
Governed Cognitive Memory Spine Phase 6.1 implements it for the active
`memory/draft` AuthorityLease-gated internal Action proposal hook only.

## Current route groups

### System and API metadata

- `GET /health`
- `GET /version`
- `GET /api/manifest`

These routes expose status and route metadata only.

### Governed web evidence

- `GET /web-evidence/status`
- `POST /web-evidence/request`

UAA-P1-063 exposes operator-visible governed web evidence status and a bounded
request envelope for allowlisted HTTPS GET evidence. The request path returns
receipt refs and bounded redacted previews only. It does not add unrestricted
browsing, browser automation, request bodies, caller-supplied headers, session
state, credential material, redirects, downloads, raw page/body storage, raw
header storage, provider calls, context injection, memory writes,
shell/subprocess behavior, plugin execution, hidden network access, or
production authority. OpenWebUI remains a shell; UAA owns the guardrail.

### Observability

- `GET /observability/session-events`
- `POST /observability/client-errors`

These routes expose bounded redacted summaries only. They do not expose raw log
records, request bodies, response bodies, prompts, provider payloads, terminal
output, credential material, external telemetry, production authority,
background monitoring, or process control.

### Extension catalog

- `GET /extensions/catalog`
- `POST /extensions/disabled-install-records`

`GET /extensions/catalog` returns read-only inspectable extension catalog
metadata with safe refs, visibility status, trust posture, callable posture,
blocked reasons, review evidence refs, safe adoption posture, and
install-disabled posture. `POST /extensions/disabled-install-records` records
only an exact disabled extension install metadata receipt after active
`workspace/write` AuthorityLease scope, exact `LocalApprovalAuthority`
validation, idempotency, redacted receipt refs, and the local disabled-record
store validate. These routes do not persist package installs, import, enable,
activate, revoke, execute, fetch, or mutate extensions.

### Control Center capability surface

- `GET /control-center/capabilities/availability`
- `GET /control-center/capabilities/surface`

`GET /control-center/capabilities/availability` returns the backend-owned
capability availability truth model with separate declaration, observed
runtime readiness, request-scoped authority posture, and execution-receipt
contract refs. Unknown and stale observations fail closed. Runtime-ready means
eligible for an immediate exact request decision, not globally authorized or
callable. The route uses injected deterministic observations only and performs
no live health probe, provider call, network access, mutation, or execution.

The capability-surface route returns a bounded read-only capability coverage
read model derived from the human capability manifest, generated source-truth
overlay, and live API manifest metadata. It exposes safe capability rows,
source-truth posture, route refs, CLI refs, missing reasons, and blocked
authority refs only. It does not
return raw manifest dumps or grant action execution, approval authority,
provider/model calls, connector writes, browser automation, shell/subprocess
execution, memory writes, context injection, public release, or production
authority.

### Mattermost agent rooms

- `GET /integrations/mattermost/status`
- `GET /integrations/mattermost/roles/catalog`
- `POST /integrations/mattermost/roles/suggest`
- `POST /integrations/mattermost/roles/bind`
- `POST /integrations/mattermost/roles/unbind`
- `POST /integrations/mattermost/events/message`
- `GET /integrations/mattermost/audit`
- `GET /integrations/mattermost/receipts`

These routes are disabled-by-default local bridge surfaces for UAA-managed
Mattermost agent room roles. They expose safe refs, bounded previews, receipt
refs, audit summaries, and reply-command proposals only. They do not persist raw
transcripts, manage credentials or cookies, treat model output as authority, or
perform unapproved connector writes.

### Control Center setup assistant

- `GET /control-center/setup-assistant/summary`

This route returns the existing deterministic macOS Setup Assistant dry-run
plan and approval-envelope metadata for read-only inspection. Dry-run
approval-envelope hardening validates proposed setup action metadata only. It
does not capture approval grants, create receipts or audit records, run
installer actions, execute shell commands, download models, install/load/start
LaunchAgents, install/load/start background services, handle credentials, claim
signed installer readiness, claim public distribution, claim production
readiness, or execute rollback.

### Control Center Coding Cockpit

- `GET /control-center/coding/session`
- `GET /control-center/coding/context`
- `GET /control-center/coding/patch-proposal`
- `GET /control-center/coding/patch-apply-readiness`
- `GET /control-center/coding/test-command-readiness`
- `GET /control-center/coding/git-review`
- `GET /control-center/coding/live-preview`
- `GET /control-center/coding/multi-agent-review`

These routes return the repo-safe Coding Cockpit shell seed and read-only
context-pack preview as backend-owned read models for `/coding`. They expose
safe workspace, context, task, diff, terminal preview, Git preview, test output,
live preview, proof, context comparison, patch proposal, blocked apply
readiness, approval-required RuntimeGateway validation command readiness,
budget, redaction, authority posture, blocked Git review, blocked live-preview,
agent slot, plan, review,
diff-comparison, disagreement, handoff, blocker, and promotion refs only. They
do not write files, apply patches, read or persist raw file content, run
shell/subprocess commands, execute commands, mutate Git state, start or inspect
dev servers, persist raw URLs, capture screenshots, read console output, call
providers or models, call provider SDKs, dispatch local agents, inject context,
persist raw prompts or responses, automate browsers, write connectors, launch
background agents, persist raw paths or raw content, or grant production
authority.

### Control Center Founder Loop summaries

- `GET /control-center/today/summary`
- `GET /control-center/actions/inbox`
- `POST /control-center/actions/{action_id}/approve`
- `POST /control-center/actions/{action_id}/edit`
- `POST /control-center/actions/{action_id}/reject`
- `POST /control-center/actions/{action_id}/defer`
- `POST /control-center/actions/{action_id}/local-task/commit`
- `GET /control-center/actions/{action_id}/receipt`
- `GET /control-center/memory/review`
- `GET /control-center/memory/contradictions`
- `POST /control-center/memory/feedback`
- `GET /control-center/memory/observation-candidates`
- `GET /control-center/memory/probe`
- `GET /control-center/memory/l1-index`
- `GET /control-center/memory/l2-index`
- `GET /control-center/memory/l3-index`
- `GET /control-center/memory/retrieval-diagnostics`
- `GET /control-center/memory/citation-integrity`
- `GET /control-center/memory/quality-issues`
- `GET /control-center/memory/maintenance-runs`
- `GET /control-center/memory/context-manifest`
- `GET /control-center/memory/context-packs`
- `GET /control-center/memory/context-packs/{context_pack_ref}/preview`
- `GET /control-center/memory/review/{candidate_ref}/receipt`
- `POST /control-center/memory/review/{candidate_ref}/accept`
- `POST /control-center/memory/review/{candidate_ref}/correct`
- `POST /control-center/memory/review/{candidate_ref}/reject`
- `GET /control-center/morning-briefing/summary`
- `GET /control-center/proof/index`
- `GET /control-center/proof/{proof_ref}`
- `GET /control-center/start-here/summary`
- `GET /control-center/storage/status`
- `POST /control-center/web-evidence/attach`
- `GET /control-center/work-board`
- `POST /control-center/work-board/reorder`
- `POST /control-center/work-board/cards`
- `POST /control-center/work-board/tasks`

These routes expose storage-backed Founder Loop v1 summaries for Today, Action
Inbox, Memory Review, Morning Briefing, local storage status, Action Inbox
decision receipts, Memory Review decision receipts, universal proof
index/detail records, read-only L1 hot local
memory index previews, L2 ref projections, L3 representation proposals, and
Phase 5 context-pack proposal envelopes, plus a backend-owned Start Here local
loop summary, FCC-MEM-022 feedback receipts, observation-candidate previews,
probe index summaries, contradiction previews, and one allowlisted
WebAccessGateway web evidence preview receipt path. The Work Board route
exposes backend-owned Kanban safe refs, local preview posture, blocked
mutation refs, proof refs, exact approved reorder/local-card-create/local-task
receipt refs, and CLI inspection refs only; drag/drop remains presentation
preview until persisted through an exact approval-bound Work Board route.
Action decision routes record backend-owned
approve/edit/reject/defer state, validate exact approval scope for approve where
required, handle idempotency replay/conflict locally, and return safe receipt
refs. Memory Review accept/correct/reject routes are backend-owned,
idempotency-required receipt routes; accept/correct create reviewed recall-only
records, and reject preserves blocked review state. The L1 route derives safe
recall previews from reviewed recall-only records only; the L2, L3, and
context-pack routes derive deterministic safe-ref inspection/proposal items
from reviewed source lanes only. They do not execute the
underlying action, run, send, install, enable, dispatch, call providers, perform
connector writes, read email/calendar data, automatically write memory, inject
context, run shell/subprocess work, deliver notifications, use embeddings or
vector DBs, run semantic search/background indexing, inject context packs, or expose raw prompts, raw
responses, raw paths, raw logs, usernames, hostnames, environment dumps,
credential material, or provider payloads.

### Local model and runtime readiness

- local `/v1` model shell routes remain disabled by default and bearer-gated
- model-runtime validation and simulation routes remain validation/fallback only
- runtime readiness and smoke-report routes remain status/validation only

UAA-P1-083 adds the general local protected-route bearer gate around the
current non-public route classifications. Protected routes fail closed by
default; local `/v1` and task-decomposition routes can still keep their
narrower disabled-by-default bearer gates; P1-083 does not grant execution,
provider, connector, or production authority.

### Task, file, tool, provider, memory, truth, approval, consent, cost, gate, and remote-worker groups

These groups keep their existing validation, preview, evaluate, dry-run,
summary, readiness, and local-dev scoped boundaries. Mutating local-dev paths
remain approval-bound and blocked from production authority.

Provider credential validation is represented by
`POST /control-center/providers/credentials/validate` as an exact-approved,
idempotency-required, redacted-receipt lane for one provider credential check.
It has no built-in live validation transport by default and is not model
invocation, provider SDK authority, provider payload persistence, fallback
routing, billing authority, autonomous/background calls, or production
authority.

Provider router dry-run is represented by
`POST /control-center/providers/router/dry-run` as a proposal-only local
posture lane. It can return exact-approval candidate provider refs, blocked provider refs,
missing credential refs, cost-risky refs, validation-required refs,
no-authority refs, and recommended exact approval scope refs. It performs no
provider invocation, fallback execution, network calls, provider SDK calls,
credential validation, model calls, billing authority, autonomous/background
calls, or raw provider payload persistence.

## Verification

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_boundary_enforcement.py
.venv/bin/python scripts/verify_uaa_p1_086_api_boundary_enforcement_tests.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_governed_web_evidence.py
```
