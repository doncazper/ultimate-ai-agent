# Authority Lane 08: Memory Write / Context Injection

Goal: Keep memory useful while separating reviewed memory writes from context
injection authority.

Allowed next promotion: reviewed memory write hardening or context-pack
preview/materialization only. Runtime context injection remains later.

Scope:

- Memory writes require reviewed candidate, exact decision, receipt, evidence,
  and correction/supersession posture.
- Context work may create reviewable context-pack refs only.
- No hidden prompt mutation.

Still blocked:

- Automatic memory writes.
- Memory-as-truth.
- Hidden context injection.
- Connector/browser/web-derived context injection.
- Provider/model context injection without explicit later lane.

Promotion condition:

Reviewed memory write or context-pack preview has source refs, redaction,
approval/decision refs, evidence, rollback/safe-disable, and no hidden prompt
inclusion.

Tests/verifiers:

- memory decision tests.
- context no-injection tests.
- citation/source tests.
- no raw memory/prompt tests.
- product-language checks.

If blocked:

Generate an unblock prompt for the missing review, citation, context-pack,
redaction, or no-injection verifier.
