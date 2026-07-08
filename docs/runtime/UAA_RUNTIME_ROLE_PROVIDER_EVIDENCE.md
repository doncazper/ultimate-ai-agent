# UAA Runtime Role Provider Evidence

Status: implemented as advisory Python Agent Core read-model evidence for UAA
Runtime Parity Phase 06.

This phase borrows external comparison runtime's useful pattern of role-based provider/model
selection evidence, but does not copy external reference code and does not adopt
external comparison runtime authority assumptions.

## Full-Strength Intent

UAA should eventually explain, per agent role, which local or remote model is
best suited for the work, why it was selected, what fallback exists, what the
cost and latency posture is, and what evidence supports the choice.

Full-strength role routing remains future gated because it would need exact
provider/model invocation authority, cost receipts, credential resolution,
provider allowlists, model-router traces, safe-disable posture, rollback or
recovery behavior, and Proof Detail evidence.

## Repo-Safe Implementation

`role_based_model_provider_evidence.v1` is a backend-owned read model inside the
existing model/provider control plane:

- `src/ultimate_ai_agent/core/providers/role_evidence.py`
- `GET /control-center/providers/runtime-control-plane`
- `scripts/dev/uaa_runtime.py inspect-role-provider-evidence`

The read model covers:

- answerer
- planner
- reviewer
- synthesizer
- coder
- extractor
- safety reviewer

For each role, UAA surfaces:

- role ref
- local and remote candidate provider/model refs
- advisory capability score
- authority-adjusted score
- cost and latency visibility labels
- policy decision ref
- fallback ref
- disabled or blocked reason ref
- redacted evidence ref
- selected advisory candidate

The current safe selection posture is local-first advisory evidence only.
remote provider candidates remain blocked because credentials, cost decisions,
provider SDK/network authority, and model invocation authority are not granted by
this phase. The phase exposes no model invocation.

## Authority Boundary

This phase is advisory evidence only. It adds no provider SDK call, no model
invocation, no provider network call, no fallback execution, no raw prompt or
raw response persistence, no provider payload persistence, no background
autonomy, and no production authority.

Control Center cannot mint authority from this evidence. It may display the
backend-owned read model and initiate only later exact-approved lanes when those
lanes separately prove approval binding, idempotency, receipts, redaction,
safe-disable posture, and CLI/API/Core parity.

## Blocked / Needs Authority

Still blocked:

- remote provider/model calls
- provider SDK calls
- live provider metadata discovery
- credential material display or storage
- provider-output-as-truth
- automatic cost refresh
- fallback execution
- background model routing
- production authority

## Verification

Focused coverage:

- `tests/test_role_provider_evidence.py`
- `tests/test_model_provider_control_plane.py`
- `scripts/verify_uaa_runtime_role_provider_evidence.py`

Required hygiene also includes model-runtime no-real-call checks, runtime
capability matrix checks, product truth, documentation integrity, operational
maturity, and `git diff --check`.
