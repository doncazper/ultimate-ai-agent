# TAW-03 Progressive Capability Retrieval

Status: bounded founder-private-dogfood implementation evidence. This contract
does not change chat routing, assemble a prompt, invoke a model/provider,
construct a proposal, request approval, execute a capability, or grant
authority.

## Purpose

TAW-03 adds a deterministic local retrieval boundary over the merged TAW-01
capability-awareness catalog and preserves the TAW-02 familiarity dimensions.
It provides:

- a cached Tier 1 compact index of reviewed canonical metadata;
- a relevance-ranked shortlist that keeps blocked and unavailable registered
  matches visible for familiarity classification;
- deterministic effect and input-schema compatibility decisions before any
  later proposal;
- a bounded Tier 2 renderer for selected typed operation manifests; and
- exact catalog, schema-set, policy, availability, environment, provenance,
  review, tokenizer-accounting, and evaluator bindings.

The cache and both result types use canonical SHA-256 fingerprints. Pydantic
instances are round-tripped through validation at every public boundary so a
copied instance cannot bypass fingerprint or cross-source checks.

## Tier 1 Compact Discovery

`build_progressive_capability_cache` requires one exact reviewed operation
schema for every TAW-01 envelope. Cache construction is model-free,
provider-free, network-free, and executable-code-free. It fails rather than
truncates when the caller's tightened entry or byte budget cannot contain the
catalog. Entries bind the exact TAW-01 catalog and operation-schema set plus the
observed environment fingerprint. Iterable inputs are consumed through a
hard-bounded collector, so the entry ceiling applies before full
materialization rather than after it.

`discover_capabilities` performs bounded deterministic lexical ranking over
the reviewed compact metadata. The normalized operator request is transient.
Neither it nor a reversible encoding is stored in the shortlist, receipt, log,
or output. The output contains safe candidate refs, scores, compatibility
decisions, fixed budgets, and fingerprints only.

Unavailable, policy-blocked, and authority-blocked matches remain in the
shortlist. They cannot become proposal-eligible. Effect and schema
incompatibilities are likewise explicit block reasons. TAW-03 has no execution
path, so every candidate's execution eligibility is a literal false value.

Hard ceilings are 512 cache entries, 128 KiB of canonical compact entries, a
4 KiB transient request, and 32 shortlist entries. Callers may tighten but not
raise these ceilings. A request or latency budget failure returns an explicit
`over_budget` result with no candidates.

## Tier 2 Manifest Hydration

Hydration accepts only shortlist candidates bound to the same cache, catalog,
environment, envelope, and operation-schema fingerprints. Every manifest is
rendered as untrusted data regardless of source. The renderer emits an explicit
instruction/data boundary and a canonical quoted JSON object. It includes only
approved identifiers, reviewed summaries and aliases, effect/risk classes,
schema fingerprints, and schema-limited input field names, required flags, and
primitive types. Free-form schema descriptions and other arbitrary schema
keywords are not rendered. Markup and reserved envelope-marker text are escaped
so catalog strings cannot create a second raw instruction/data delimiter.

Source kind, provenance ref, review ref, and review state are bound per
operation. Unreviewed imported or A2A-derived text is excluded. Missing token
accounting, source substitution, and entry/byte/token exhaustion are recorded
as explicit exclusions rather than guessed around.

The non-overridable hydration ceilings are:

- 8 manifests;
- 32 KiB rendered bytes; and
- `min(4096, floor(model_context_tokens * 0.05), remaining exact context)`
  accounted tokens.

Accounting binds the backend, tokenizer artifact and fingerprint, prompt
format, estimator, full context limit, non-hydration prompt tokens, reserved
output tokens, and a conservative or exact count for every candidate. Missing
or exhausted context accounting fails closed for hydration.

## Authority Boundary And Next Slice

TAW-03 does not integrate the shortlist or rendered material with the Turn
Contract Router or any model-visible prompt. Its cache, shortlist, and hydration
result all carry literal false values for model/provider/network calls,
executable-code loading, prompt assembly, proposal construction, approval
requests, execution, and authority grants.

TAW-04 remains responsible for evidence-only shadow integration, clarification
behavior, the ordinary-chat zero-extra-model-call rule, adversarial testing of
every model-visible field, and the explicit safe-disable path. TAW-04 must not
interpret TAW-03 relevance or hydration as execution authority.

## Verification

Run:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_tool_aware_cognition_taw03.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_tool_aware_cognition_taw03.py
```

The focused tests cover deterministic cache construction; copied-instance,
schema, catalog, source, and environment substitution; stale and over-budget
evidence; blocked-match retention; effect/schema filters; transient request
handling; unreviewed imported-text exclusion; escaped data rendering; exact
context ceilings; and non-authority literals.
