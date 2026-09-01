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
decision. Founder-private acceptance requires verified, digest-bound
measurement receipts whose candidate revision and manifest match the exact
candidate. Each receipt carries bounded numeric observations, an exact
observation count, threshold identities, comparison operators and values, and
a verifier identity. Ratio observations and thresholds are constrained to the
closed interval from zero through one. The verifier recomputes the threshold decision; an
arbitrary digest or caller-authored `passed` label is insufficient:

- stale-cache recovery evidence;
- routing-confidence-bound evidence;
- response-level scoring evidence;
- at least one exact live model/hardware run receipt;
- the end-to-end chat, discovery, proposal, approval-required, unavailable,
  unsupported, interrupted, and recovery journey receipt;
- the founder decision ref with an explicit `accepted` outcome and a verified
  Ed25519 signature over the exact candidate, measurement-receipt census,
  exact-head Foundation receipt, and decision ref; and
- a passing redacted Foundation Gate `report-only` receipt for the exact
  candidate head.

The accepted profile remains English-first, Qwen 3.8 27B with a 128K local
context identity, configured ChatGPT/Codex API profile identities, and per-run
observed Mac/Windows hardware. A run receipt must bind the exact model artifact
or configured model ID and the observed host. This repository slice performs no
such run and does not grant permission to call those models or providers.
Local model evidence uses a SHA-256 artifact-digest identity; API evidence uses
the exact configured OpenAI model ID rather than a generic profile placeholder.

The founder-decision verification key is an acceptance authority, not ordinary
caller input. This slice intentionally leaves that repository trust root
unconfigured, so a caller cannot invent a decision and advance acceptance.
Founder-private acceptance stays blocked until a later exact candidate binds
the founder's public verification key; no private signing key is stored here.

When the evidence is absent, `evaluate_taw08_acceptance` returns
`blocked_missing_founder_evidence` with an exact missing-evidence census. Once
the complete founder bundle is bound, the report can advance only to
`founder_private_accepted_postmerge_pending`. A passing redacted post-merge
Foundation Gate receipt advances it only to
`founder_private_accepted_final_publication_pending`. A content-addressed final
publication receipt must verify the actual canonical artifact bytes at
`docs/evals/tool_aware_cognition_taw08_final_acceptance_report_v1.json` and bind
their exact publication revision before the durable report advances to
`founder_private_accepted_promotion_blocked`.

## Candidate Lock And Evidence-Only Delta

The existing TAW-00 `CandidateLock` remains the candidate-manifest authority.
It binds an exact Git revision, sorted content-addressed acceptance-affecting
entries, and the only paths permitted to change after the lock. TAW-08 requires
a candidate-verification receipt produced only after the locked path census,
content digests, source projection, transitive dependency closure, and resolved
evaluator environment all verify. `pyproject.toml` and `uv.lock` are mandatory
lock entries, and their verified digests form the evaluator-environment digest.
The repository verifier derives the complete source universe with
`git ls-tree` at the locked revision before resolving imports, and reads every
locked artifact directly with `git show <revision>:<path>`. Candidate source
paths and content digests must match the projection roots and closure entries
exactly. An incomplete one-file lock, caller-supplied content map or source
universe, or source projection rebound to different bytes cannot satisfy the
acceptance boundary.

The lock also binds the canonical Foundation Gate runner directly and derives a
complete content-addressed census of every Python source file in the gate
package from the named Git revision. The verifier compares that census with the
revision tree, so adding, removing, or changing evaluator, report, criteria, or
support code invalidates stale acceptance evidence even when the runner path
itself does not change. This explicit package census remains fail-closed where
the gate intentionally uses dynamic module loading; it does not guess at a
false static import graph.

`EvidenceOnlyDeltaManifest` permits only three artifact kinds:

- `acceptance_report`;
- `immutable_evidence_refs`; and
- `claim_reconciliation`.

Its verifier proves candidate ancestry and recomputes both the endpoint diff and
the complete per-commit changed-path history, including merge-parent and
later-reverted paths. It also recomputes content digests,
requires every changed path to be predeclared by the candidate lock, recursively
rejects forbidden durable fields and high-signal secret-like values, validates
the bounded artifact against the frozen schema for its declared kind, and
rejects overlap with acceptance-affecting candidate entries. A redacted
acceptance artifact must be present at the one canonical acceptance-report path
and be the exact projection of a fully validated `TAW08AcceptanceReport`;
schema-valid placeholder values, an omitted acceptance report, or a report for
another candidate are rejected. A successful verification produces a
digest-bound receipt that must match the candidate,
delta manifest, delta revision, independently derived revision-delta path
census, and exact artifact count. The repository workflow must derive that
census from the named candidate and delta revisions before calling the core
verifier; a caller-authored subset is not complete revision evidence.
Executable code, routes, prompts, policy data, configuration, dependencies,
evaluators, thresholds, corpora, labels, raw content, and holdout material
cannot be represented as evidence-only. Both the board and release-truth
reconciliations are mandatory and must publish `implemented` before the delta
can verify. Each may update only the entire canonical TAW-07/TAW-08 status
narrative and single machine-owned JSON block
between the named TAW-08 markers in each active Markdown truth document. The
verifier binds the narrative to the structured status, reads the candidate
revision, and rejects any prefix, suffix, duplicate-marker, schema, or secret
drift outside that bounded block. Separate structured JSON sidecars remain
available for durable reconciliation evidence. Any other change requires a new
candidate lock and acceptance cycle.

Foundation receipts are produced only by the canonical repository gate runner
from an immutable, digest-bound, typed, validated, internally consistent,
passing Foundation Gate report with real criterion results and the same clean
exact Git revision derived before and after the full-repository gate invocation
in `report-only` mode. The general report builder cannot attach evaluation
provenance, and the public arbitrary receipt binder is not available. They
are SHA-bound, revision-bound, and redacted. The exact-head receipt must match
the candidate revision. The
post-merge receipt is a distinct stage, must bind the verified evidence-only
delta revision, and cannot substitute for the exact-head gate. A post-merge
receipt without the verified delta receipt produces a failed report.

Every measurement kind has a frozen case/stratum census and a minimum
denominator of 24 per stratum; an aggregate observation cannot substitute for
the complete powered census. Ratio observations bind their integer success
numerator to the denominator. The ordinary-chat stratum also binds one measured
model-call count per observation and rejects any count other than exactly one.
Live measurements additionally bind the English
language profile plus exact model, artifact/configuration, 128K context,
backend, and observed-hardware refs. Each live result includes a numeric,
count-consistent same-host baseline for the same metric and cannot regress from
that baseline. The per-host identity is an opaque SHA-256 observation ref;
hostnames, serials, and other raw machine identifiers are not valid evidence.
The final publication receipt binds the
candidate, verified delta, post-merge receipt, terminal founder-private status,
semantic digest of the final report. Its verifier parses and compares the
canonical durable artifact bytes, then binds their content digest, canonical
path, and exact publication revision so an in-memory `published` assertion
cannot advance acceptance while durable truth stays post-merge-pending. The
repository wrapper accepts no caller-supplied bytes; it reads the canonical
artifact with `git show <publication-revision>:<canonical-path>` before invoking
the core verifier. It also proves that the publication revision descends from
the verified evidence-delta revision and that the complete endpoint and
per-commit changed-path history between them contains only the canonical final
publication artifact. An intervening, reverted, merged, or unrelated path
change invalidates the receipt.

The evaluator-environment receipt binds each reachable installed distribution
to exactly one wheel hash selected by `uv.lock`, compares the installed payload
with that wheel's bounded uv-cache archive and authenticated `RECORD` census,
and binds a SHA-256 content census for the entire reachable dependency closure.
Foundation receipts embed that same verified evaluator-environment receipt and
also compare the bytes of every executing repository evaluator source with the
exact Git revision being evaluated, including when the evaluated checkout
differs from the launcher checkout.

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

The locked verifier downloads only the compatible wheel URLs named by
`uv.lock`, verifies the complete wheel bytes against each locked size and
SHA-256 digest, and installs them into a temporary no-pip venv. The receipt
child starts with `python -S`; a standard-library preflight rejects importable
or startup files not owned by an installed distribution `RECORD` before adding
that venv's site-packages. The child then binds installed distribution content
back to each authenticated wheel and deletes the temporary environment when
verification ends.
