# Tool-Aware Cognition TAW-01 Capability Evidence

Status: implemented for founder-private dogfood; independent promotion remains
blocked.

Acceptance-state role: `non-owner`. This slice records bounded implementation
evidence only. Mutable founder-private acceptance state is owned by the
content-addressed TAW-08 report and its two bounded active-truth reconciliations;
independent promotion is a separate gate.

Contract: `contract-ref:taw01:capability-awareness-envelope:v1`.

## Outcome

TAW-01 adds one deterministic Python Core contract that projects registered
`CapabilityManifest` records and exact operation schemas into typed,
content-free capability-awareness envelopes. The projection does not search a
request, affect chat routing, hydrate a model prompt, call a model or provider,
or execute a capability.

Each envelope binds:

- exact capability and operation identities and versions;
- a bounded operator summary and sorted deterministic aliases;
- effect, risk, authority, and approval classifications;
- required and optional input-field refs plus canonical input/output schema
  fingerprints, without persisting the schemas in the envelope;
- precondition, incompatibility, and dependency refs;
- health, availability epoch, policy snapshot, and authority-lane posture;
- safe-disable and rollback posture;
- expected receipt and terminal-proof contracts;
- positive, negative, ambiguity, and adversarial evaluation refs; and
- provenance, review, catalog-epoch, expiry, envelope fingerprint, and catalog
  fingerprint evidence.

The contract hard-codes raw operator/model content persistence, model calls,
provider calls, execution enablement, and authority grants to `false`.
`graduated` is an inspectable authority-lane classification only; it cannot
authorize or execute an operation.

## Fail-Closed Validation

Construction and validation reject:

- unregistered capabilities or mismatched capability versions;
- operation input/output schemas that differ from the registered manifest;
- operation risk or side-effect classes broader than the manifest;
- malformed object schemas, unsafe field names, undefined required fields,
  noncanonical JSON, unsafe summaries, raw local paths, or obvious secrets;
- duplicate operation schemas, duplicate bindings, duplicate catalog entries,
  unsorted aliases/refs, or incomplete one-to-one operation bindings;
- contradictory read/mutation authority-lane or rollback postures;
- mixed policy snapshots inside one catalog;
- envelope/catalog binding or fingerprint drift; and
- expired or substituted catalog, availability, or policy epochs.

The accepted stale boundary is inclusive at the recorded expiry second and
fails on the next second. Refresh remains model-free and provider-free.

## Verification

Run:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_tool_aware_cognition_taw01.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_aware_cognition_taw01.py
```

The focused tests cover deterministic fingerprints, content-free output,
required/optional field projection, no-authority literals, exact expiry,
substituted epochs, tampering, extra fields, duplicate and missing bindings,
version and policy drift, mutating approval/rollback posture, malformed schema,
unsafe content, canonical ordering, and the repository verifier.

## Remaining Boundary

This slice provides evidence construction, not familiarity assessment. TAW-02 remains
responsible for the nine canonical familiarity states, precedence, stable
reason codes, ambiguity, substitution, and fail-closed decision behavior.
TAW-03 remains responsible for compact discovery and bounded manifest
hydration. TAW-04 remains responsible for chat integration and shadow-mode
behavior. Independent custody, blinded scoring, supported-matrix evidence, and
TAW-08 promotion remain required before independent, public, multi-user, or
production quality claims.
