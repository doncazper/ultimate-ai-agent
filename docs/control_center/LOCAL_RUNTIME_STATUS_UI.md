# Local Runtime Status UI

Status: Active for v0.22.0 / M18.

M18 adds a CCC Web read-only local runtime status page at `/runtime/local`.

The page may show:

- readiness report status from `GET /runtime/readiness`.
- capability matrix summaries from `GET /runtime/capability-matrix`.
- safe route refs.
- boolean readiness flags.
- blocked runtime categories.
- visibly mock fallback summaries.
- redacted summary-only status messages.

Safety boundary:

- No backend route is added.
- OpenAPI path count remains `74`.
- no runtime execution.
- no local runtime start, stop, connect, launch, or provider invocation.
- no model/provider calls.
- no remote execution or remote dispatch.
- no mobile sensor access.
- no plugin enablement.
- no native build workflow.
- no raw prompts, no raw secrets, no raw response bodies, no credentials, and no provider payloads.

The UI is non-authoritative. Python Agent Core, Runtime Readiness contracts, Approval Authority, Event Ledger, Secret Broker, Tool Broker, Redaction, and Foundation Gate remain the authority boundary.
