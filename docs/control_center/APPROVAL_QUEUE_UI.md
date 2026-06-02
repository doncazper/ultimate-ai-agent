# Approval Queue UI

Status: Active for v0.19.0 / M15 Approval Queue + Receipt/Event Viewer UI.

The Approval Queue UI is a read-only and preview-only CCC Web surface under `apps/control-center`. It helps a user inspect approval request summaries and selected approval details without becoming approval authority.

The UI may show:

- approval refs.
- status.
- risk level.
- data classification.
- actor summary.
- requested action summary.
- subject/resource summary.
- reason codes.
- created and expiry times when safe.
- required next action.
- related receipt and event refs.
- safe messages.
- visibly mock and non-authoritative fallback state.

The UI must not:

- execute approvals.
- grant approvals.
- reject approvals as an authoritative backend action.
- send, write, publish, run, deploy, enable, install, or mutate anything.
- treat arbitrary approval refs as authority.
- bypass Approval Authority, Consent Ledger, Tool Broker, Event Ledger, Secret Broker, Redaction, or Foundation Gate.
- display raw secrets, raw prompt bodies, raw file bodies, raw memory contents, provider payloads, or raw credentials.
- use local storage, session storage, cookies, browser credential APIs, mobile sensor APIs, native build workflows, plugin enablement, Chrome authenticated profile control, or Computer Use automation.

Approval Authority remains in the Python Agent Core. The Control Center displays inspection summaries only.

M15 uses selected item detail panels instead of dynamic approval detail routes because the current route framework is a simple path switch. This patch adds no backend approval queue route and no OpenAPI path.
