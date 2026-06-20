# Manual Smoke Control Surface

Status: Historical M18 manual smoke control surface safety note.

Current API path count lives in `docs/api/README.md`; the route-count statement
below reflects the M18 milestone, not current repository truth.

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
- M18 adds no backend API path.
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
