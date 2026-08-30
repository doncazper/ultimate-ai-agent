# Tool-Aware Cognition TAW-08 Acceptance Contract

Status: candidate-lock and founder-private acceptance contract implemented;
actual founder acceptance remains `blocked_missing_founder_evidence`.
Independent promotion, public quality claims, and Q22 completion remain blocked.

TAW-08 now has a deterministic contract for the last acceptance boundary. It
does not claim that the product has been measured or accepted. It makes the
remaining work finite and machine-checkable: lock the exact candidate, collect
the named founder-private receipts, record the founder's decision, merge only a
verified evidence-only delta, and bind exact-head and post-merge Foundation Gate
receipts.

This slice adds no model or provider call, no second ordinary-chat model call,
no route or Control Center surface, no proposal, approval grant, tool execution,
connector, external write, holdout access, public claim, or production
authority.

## Founder-Private Acceptance

The founder is the sole product evaluator for the current private-dogfood
stage. The contract does not require multiple human evaluators to record that
decision. Founder-private acceptance requires all of the following safe,
content-free refs bound to one exact candidate revision and manifest:

- stale-cache recovery evidence;
- routing-confidence-bound evidence;
- response-level scoring evidence;
- at least one exact live model/hardware run receipt;
- the end-to-end chat, discovery, proposal, approval-required, unavailable,
  unsupported, interrupted, and recovery journey receipt;
- the founder decision ref with an explicit `accepted` outcome; and
- a passing redacted Foundation Gate `report-only` receipt for the exact
  candidate head.

The accepted profile remains English-first, Qwen 3.8 27B with a 128K local
context identity, configured ChatGPT/Codex API profile identities, and per-run
observed Mac/Windows hardware. A run receipt must bind the exact model artifact
or configured model ID and the observed host. This repository slice performs no
such run and does not grant permission to call those models or providers.

When the evidence is absent, `evaluate_taw08_acceptance` returns
`blocked_missing_founder_evidence` with an exact missing-evidence census. Once
the complete founder bundle is bound, the report can advance only to
`founder_private_accepted_postmerge_pending`. A passing redacted post-merge
Foundation Gate receipt advances it to
`founder_private_accepted_promotion_blocked`.

## Candidate Lock And Evidence-Only Delta

The existing TAW-00 `CandidateLock` remains the candidate-manifest authority.
It binds an exact Git revision, sorted content-addressed acceptance-affecting
entries, and the only paths permitted to change after the lock. TAW-08 requires
a candidate-verification receipt produced only after the locked path census,
content digests, source projection, and transitive dependency closure all
verify. Candidate source paths and content digests must match the projection
roots and closure entries exactly. An incomplete one-file lock or a source
projection rebound to different bytes cannot satisfy the acceptance boundary.

`EvidenceOnlyDeltaManifest` permits only three artifact kinds:

- `acceptance_report`;
- `immutable_evidence_refs`; and
- `claim_reconciliation`.

Its verifier recomputes the exact changed-path census and content digests,
requires every changed path to be predeclared by the candidate lock, validates
the bounded JSON artifact against the frozen schema for its declared kind, and
rejects overlap with acceptance-affecting candidate entries. A successful
verification produces a digest-bound receipt that must match the candidate,
delta manifest, delta revision, independently derived revision-delta path
census, and exact artifact count. The repository workflow must derive that
census from the named candidate and delta revisions before calling the core
verifier; a caller-authored subset is not complete revision evidence.
Executable code, routes, prompts, policy data, configuration, dependencies,
evaluators, thresholds, corpora, labels, raw content, and holdout material
cannot be represented as evidence-only. Any such change requires a new
candidate lock and acceptance cycle.

Foundation receipts are SHA-bound, revision-bound, redacted `report-only`
records. The exact-head receipt must match the candidate revision. The
post-merge receipt is a distinct stage, must bind the verified evidence-only
delta revision, and cannot substitute for the exact-head gate. A post-merge
receipt without the verified delta receipt produces a failed report.

## Independent Promotion Remains Separate

Founder-private acceptance is intentionally not independent acceptance. Every
TAW-08 report keeps `independent_promotion_ready=false`,
`sealed_holdout_evidence_verified=false`, and
`public_quality_claims_allowed=false`. The fixed blockers remain:

- independent custodian identity/authority;
- independent evaluator identity/authority;
- an externally accepted baseline; and
- verified sealed-holdout evidence.

Those gates matter only for independent/public promotion. They do not require
the founder to recruit extra evaluators before privately using and tuning the
application. Missing independent evidence cannot be relabeled as founder
evidence, and founder acceptance cannot be relabeled as a public quality claim.

## Fail-Closed Behavior

All models are frozen and reject unknown fields. They use Python-3.10-compatible
string enums. Builder functions reject unknown fields before materializing
digest payloads. Revisions and digests must be exact; refs must be structured
safe refs; receipt censuses must be sorted and duplicate-free; status, missing
refs, binding failures, and report fingerprints are recomputed. Candidate or
evidence rebinding is preserved as a fingerprinted failed report instead of an
unhandled validation exception. Foundation-stage substitution, delta path,
schema, or content drift, and any explicit failure produce a failed report or
verifier failure.

Durable records contain no raw prompts, responses, provider payloads, local
paths, logs, usernames, hostnames, serials, environment dumps, credentials, or
secret-like values.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_tool_aware_cognition_taw08.py
PYTHONPATH=src .venv/bin/python scripts/verify_tool_aware_cognition_taw08.py
```

The repository verifier locks the committed TAW-08 contract slice and proves
that the no-evidence fixture remains blocked with every authority and public
claim false. It is structural regression evidence, not founder acceptance,
live performance evidence, a holdout result, or Q22 completion.
