# Manual Smoke Reports

Status: Active M11 validation contract, surfaced in CCC Web by v0.22.0 / M18.

Manual smoke reports are safe summaries of a manual local loopback smoke attempt. They are not raw transcripts, not prompt logs, not model evidence, and not production readiness proof.

Accepted reports must use safe fields only:

- stable report and request IDs.
- loopback-only endpoint summary with no credentials and no secret query values.
- fixed prompt hash.
- response origin from `local_loopback_smoke`, `fake_transport`, `fake_manual_loopback_smoke`, or `simulated_fallback`.
- short response preview capped at 512 characters.
- response hash or marker metadata.
- `model_output_authoritative=false`.

Rejected report content includes:

- raw prompt fields or prompt text.
- secret-like values.
- endpoint URLs with credentials or secret query parameters.
- remote endpoint summaries.
- full response bodies.
- cloud/provider execution claims.
- remote execution claims.
- live mesh/tailnet claims.
- mobile sensor claims.
- plugin/native build enablement claims.
- authoritative model-output claims.
- production runtime, production readiness, production evidence, real runtime origin, or real model output claims.

Validation responses must be safe reason codes and messages only. They must not echo secrets, prompts, or raw response bodies.

`fake_manual_loopback_smoke` is an allowed fake/test origin used by tests, gates, and validation examples. It is not a live runtime origin, not production evidence, and not proof that a real model/provider/runtime was called.

## v0.22.0 M18 Web Surface

v0.22.0 adds a validation-only CCC Web manual smoke report surface at `/runtime/manual-smoke`.

The surface may display safe report refs, request refs, endpoint summaries, model ID summaries, fixed prompt hashes, response origin labels, reason codes, redaction status, and model-output-authority flags. It must show no raw smoke report, no raw prompts, no raw response bodies, no raw transcripts, no credentials, no endpoint secrets, and no provider payloads.

The surface adds no backend route. OpenAPI path count remains `74`. It performs no manual smoke execution, no runtime execution, and no model/provider calls.

M23 adds a separate manual fixed-prompt local model call CLI path. M23 results
are still non-authoritative, receipt-backed, redacted summaries only, and not
production readiness evidence.
