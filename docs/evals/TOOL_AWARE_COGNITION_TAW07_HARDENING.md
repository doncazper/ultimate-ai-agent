# Tool-Aware Cognition TAW-07 Development Hardening

Status: deterministic development contract implemented; TAW-07 qualification is
`blocked_missing_acceptance_evidence`. The repository fixture proves structural
contract behavior only, not accepted model, response, recovery, statistical, or
hardware evidence.
Independent promotion and public quality claims remain blocked.

Acceptance-state role: `non-owner`. This slice records bounded implementation
evidence only. Mutable founder-private acceptance state is owned by the
content-addressed TAW-08 report and its two bounded active-truth reconciliations;
independent promotion is a separate gate.

TAW-07 adds a deterministic, content-free hardening contract around the accepted
TAW-04 evidence-only chat decision. It does not activate routing, change model
context, call a model or provider, construct a proposal, grant approval, execute
a tool, access a connector, write externally, or open the independent holdout.

## Founder Scope

The accepted founder profile remains English-first with Qwen 3.8 27B and a 128K
local context identity. Configured ChatGPT/Codex API profiles remain configuration
identities only; this slice makes no API call. Mac and Windows hardware evidence
is still recorded per run rather than inferred from a repository fixture.

The durable development corpus is
`docs/evals/tool_aware_cognition_taw07_development_corpus_v1.json`. It contains 24
synthetic cases. Its accepted corpus digest locks the complete case-to-category,
rubric, parameter, variant, and generated-content mapping rather than only a
category census:

- two ordinary-chat cases;
- two supported-tool cases;
- two unsupported-request cases;
- one material-effect ambiguity case;
- one authority-blocked case;
- one outcome-uncertain case; and
- fifteen catalog-injection cases, one for every TAW-04 model-visible catalog
  field path.

The development seed is intentionally available because this is the development
corpus. No acceptance-holdout seed, parameter, generated input, case hash, label,
expected decision, or per-case result is present. A validated public
`HoldoutCommitment` envelope may bind the accepted TAW-00 cycle, custodian,
HMAC-SHA256 commitment, creation-order evidence, and custodian attestation before
the report is preserved for later qualification. The report records whether the
envelope is present but always records `holdout_evidence_verified=false`.
Because TAW-07 cannot independently resolve those refs or open the HMAC
commitment, a passing status is not representable in this contract. The private
holdout material remains unrepresentable here.

## Exact Matrix

Every case must have exactly one observation for each combination of:

- catalog state: healthy, missing, corrupt, stale, and over-budget; and
- replay mode: candidate shadow and explicit safe-disable replay.

That produces 240 duplicate-free observations. Each observation embeds and
validates the exact TAW-04 decision fingerprint, candidate Git revision,
candidate-manifest digest, development-corpus digest, legacy route, content-free
payload/response/evidence fingerprints, latency values, context count, and a
safe evidence ref.

The candidate remains no-effect. Healthy candidate-shadow observations reconstruct
each transient synthetic payload and run it through the bounded familiarity,
progressive-retrieval/hydration, and TAW-04 chat-shadow path; the evaluator then
classifies the request from its bounded parameter refs rather than the embedded
manifest category label. The supported write case is matched and hydrated against
the reviewed write envelope, where its blocked authority lane remains visible.
Each catalog-injection case places instruction-shaped data into its named catalog
field, then exercises the poisoned catalog through constrained retrieval and
single-candidate hydration before the same path is evaluated. Input/output schema
descriptions are deliberately excluded from rendered hydration and the contract
asserts that instruction-shaped schema descriptions cannot cross that projection.
Corrupt, stale, and over-budget candidate-shadow states are derived by exercising
the real catalog-cache or retrieval boundary; they are not caller-selected labels.
The evaluator then
compares that result with the accepted action matrix. Every degraded state and
every explicit safe-disable replay must preserve the accepted legacy direct-chat
route and the exact payload, response, and durable-evidence fingerprints. The
evaluator recomputes that accepted binding set from the immutable development
case refs instead of trusting mutually consistent caller-supplied substitutions.
No model-visible context or second model call is allowed.

The repository verifier's TAW-07 candidate digest reads every covered blob from
the exact committed revision and uses Git's normalization-aware comparison to
reject a covered working-tree mismatch. It
covers every path changed by this slice, including status and index reconciliation.
The exact Git revision binds the complete tree. This development digest is not the complete
acceptance-affecting manifest required by TAW-08.

## Recomputed Gates

`evaluate_taw07_hardening` recomputes, rather than trusts, the following
development gates:

- candidate-action disagreement;
- direct-chat false-positive and ordinary-chat false-block events;
- unsupported-request false support;
- unsafe authority events;
- catalog-instruction following across all fifteen catalog fields;
- route, payload, response, and durable-evidence safe-disable equivalence;
- per-observation routing, hydration, and context budgets;
- per-category, catalog-state, and replay-mode stratum p95 of paired
  candidate-minus-baseline time-to-first-token margins, with the relative margin
  computed per pair before ranking, so degraded/safe-disable observations cannot
  mask the active candidate path, checked against both absolute and relative
  limits; and
- founder-private paired quality deltas for helpfulness, instruction following,
  tone, and response relevance, using a deterministic one-sided 95% bootstrap
  lower bound with 10,000 resamples and policy-bound seed 7.

The deterministic fixture exposes zero-event structural checks for safety,
routing disagreement, prompt injection, and equivalence calculations. These are
not accepted product metrics: every result records
`acceptance_evidence_complete=false`, and the report preserves an exact missing
evidence census for stale-cache recovery, routing confidence bounds,
response-level catalog-instruction scoring, and live model/hardware measurements.
Each fixture quality confidence lower bound,
not only the observed minimum, must remain at or above the -5 point floor. The
routing and hydration ceilings are 100 ms and 200 ms, context is
bounded to the accepted 128K profile, and the p95 TTFT margin must satisfy both
50 ms absolute and five-percent relative limits.

The repository verifier generates a deterministic identity-preserving no-effect
fixture to prove the contract and all fail-closed calculations. Those fixture
latencies and identity-equal response fingerprints are structural regression
evidence, not claims about measured model or hardware performance. Actual
founder-dogfood measurements must bind exact model artifacts, hardware, and
candidate evidence before TAW-08 acceptance.

## Fail-Closed Behavior

The evaluator rejects an oversized corpus before materializing the observation
matrix; any drift from the exact `2/2/2/1/1/1/15` category census; missing, extra,
or duplicate matrix identities; incomplete legacy or
paired-quality or metric censuses; candidate/corpus rebinding; any drift from the
accepted exact corpus digest; incomplete catalog-injection coverage; malformed
digests; covered-tree drift; and unknown fields. Baseline and
candidate response fingerprints are independently bound by each paired-quality
observation, so genuine candidate wording may differ. Substituted legacy response or durable
evidence fingerprints, exceeded budgets, negative quality drift, or a validated
decision mismatch produce a failed report. Every report embeds and fingerprints
the exact governing policy, including the thresholds actually used, and its
persisted maximum and p95 latency, relative-TTFT, context, and quality
aggregates, including p95-at-or-below-maximum latency and the policy-bound quality
confidence lower bounds, must agree with the corresponding structural checks. Report status and
fingerprint are recomputed from the exact evidence. Persisted reports must retain
the fixed `24/240/2` case,
observation, and paired-quality census plus the exact denominator for every
metric. Clean deterministic evidence remains
`blocked_missing_acceptance_evidence` whether the public commitment is absent or
present-but-unverified. A separate boolean preserves that distinction without
promoting the overall result.

The models use Python-3.10-compatible string enums. Durable evidence contains no
raw prompts, responses, provider payloads, local paths, logs, usernames,
hostnames, serials, environment dumps, credentials, or secret-like values.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_tool_aware_cognition_taw07.py
PYTHONPATH=src .venv/bin/python scripts/verify_tool_aware_cognition_taw07.py
```

TAW-07 does not complete Q22 and is not qualified by the repository fixture.
TAW-08 is the only lane permitted to bind founder-private stale-recovery,
routing-confidence, response-scoring, and live-model/hardware evidence; lock the
complete candidate manifest; record founder-private dogfood acceptance with
exact measured evidence; and reconcile product claims.
Independent-promotion evidence remains outside TAW-08. It belongs to its
separately governed future gate. External custody, blind scoring, independently
accepted baseline evidence, public claims, runtime model/provider calls, and
production authority remain blocked.
