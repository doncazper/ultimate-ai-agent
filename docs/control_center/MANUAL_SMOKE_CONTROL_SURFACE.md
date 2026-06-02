# Manual Smoke Control Surface

Status: Active for v0.22.0 / M18.

M18 adds a CCC Web manual smoke report surface at `/runtime/manual-smoke`.

This page is validation-only and summary-only. It may display safe manual smoke report validation metadata tied to the existing `POST /runtime/smoke-reports/validate` backend route. It does not perform the manual smoke attempt.

The page may show:

- report refs.
- request refs.
- endpoint summary labels.
- model ID summary labels.
- fixed prompt hash values.
- response origin labels such as `fake_manual_loopback_smoke`.
- safe reason codes.
- redaction status.
- whether a response preview is shown.
- whether model output is authoritative.

Safety boundary:

- No backend route is added.
- OpenAPI path count remains `74`.
- no manual smoke execution.
- no runtime execution.
- no model/provider calls.
- no raw smoke report.
- no raw prompts.
- no raw response bodies.
- no raw transcripts.
- no secrets or credentials.
- no response body display.
- no endpoint credentials or secret query display.

Manual smoke execution remains CLI-only, fixed-prompt-only, approval-gated, and non-authoritative. The Web Control Center can display validation metadata only.
