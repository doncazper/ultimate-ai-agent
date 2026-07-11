# Phase 01: Reasoning And Task Understanding

Goal: implement backend-owned, deterministic intent and plan-revision truth
without treating model output as authority.

## Required Work

1. Inspect existing intent, planner, task-decomposition, evidence, CLI, API,
   OpenAPI, route-classification, Control Center, and redaction contracts.
2. Add typed records for:
   - safe intent ref and fingerprint;
   - facts, assumptions, and unknowns;
   - ambiguity and contradiction posture;
   - questions requiring operator input;
   - confidence band;
   - source and evidence refs;
   - immutable decomposition; and
   - revision fingerprint, predecessor ref, and reason.
3. Provide a deterministic baseline that works without a model. Runtime-model
   assistance may run only through an existing exact approved provider lane.
   Raw prompts remain transient. Model output remains evidence, not authority.
4. Expose one backend-owned readable explanation through the smallest existing
   CLI/API/macOS Control Center surfaces. JSON is optional and redacted.
5. Bind revisions to the prior immutable plan. Reject changed membership,
   reordered steps, retargeting, or other mutation unless represented as a new
   explicit revision with its own fingerprint and reason.

## Required Proofs

- ambiguity and low-confidence question generation;
- contradictory inputs;
- prompt-injection-shaped text remains untrusted data;
- facts, assumptions, and unknowns remain distinct;
- unchanged deterministic replay;
- changed-plan rejection;
- source/evidence refs remain safe and redacted; and
- no raw prompt, answer, path, log, provider payload, or secret persistence.

## Authority Boundary

Intent, confidence, questions, decomposition, revisions, model output, and UI
state grant no approval, lease, tool, memory, web, shell, connector, provider,
or production authority. Unknown authority is denied.

## Verification

Run focused intent/planning tests plus affected API/CLI/UI tests, OpenAPI and
route classification when routes change, redaction/product-truth/docs checks,
Foundation Gate report-only with `--no-write-latest`, and `git diff --check`.

## Exit

Reasoning truth is typed, deterministic, operator-readable, evidence-bound,
and tested. Any unavailable model-assisted path is terminally classified; it
does not delay the phase or generate another prompt.
