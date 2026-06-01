# Manual Smoke Reports

Status: Active M11 validation contract, v0.15.1

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
