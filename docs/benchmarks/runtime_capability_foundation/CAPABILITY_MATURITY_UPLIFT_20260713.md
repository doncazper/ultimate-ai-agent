# Capability maturity evidence gate

Status: implemented evidence-readiness contract; no one-point score uplift is
accepted by this slice alone.

This slice turns the 16-component comparison into an executable acceptance
contract without allowing a passing test suite to grade itself. The bounded
evaluator can satisfy implementation, automated-test, runtime-scenario, and
failure/recovery gates. A score still stays at its baseline until a separate,
content-free, digest-bound independent acceptance decision verifies the
operator or external evidence named for that component.

The 23-scenario evaluator is useful evidence, but it is not the whole maturity
rubric. A scenario matching its expected status cannot by itself prove product
usability, provider integration, ecosystem maturity, or an exceptional 10/10.

| Component | Baseline | Candidate target | Evidence still required before acceptance |
|---|---:|---:|---|
| Reasoning and task understanding | 8 | 9 | operator ambiguity/contradiction trial with fact, assumption, unknown, and question separation |
| Planning and orchestration | 10 | 10 | release-candidate DAG crash, replay, cancellation, and settlement drills defend the ceiling only |
| Learning and adaptation | 8 | 9 | reviewed correction, supersession, rejection, and feedback-replay trial |
| Memory and context management | 9 | 10 | exclusion, deletion, staleness, and conflict leak test over a bounded context manifest |
| Communication and interaction quality | 8 | 9 | browser-verified readable success, ambiguity, blocked, and failure handoffs |
| Action and tool calling | 9 | 10 | independent concurrency, revocation, replay, and rollback-readiness drills |
| Autonomy and authority management | 10 | 10 | release-candidate approval, lease, budget, and kill-switch drills defend the ceiling only |
| Code and implementation assistance | 8 | 9 | operator-reviewed proposal, patch hash, validation, exact apply, rollback, and receipt trial |
| Research, web, and external information | 10 | 10 | citation, fallback, cost, injection, and no-mutation drills defend the ceiling only |
| Model and provider management | 8 | 9 | provider-intelligence integration plus a configured local-provider routing/cost/latency trial |
| Evidence, audit, and observability | 9 | 10 | independent tamper, truncation, reorder, replay, and cross-run receipt verification |
| Safety, security, and failure handling | 10 | 10 | release-candidate corruption, redaction, cancellation, and recovery drills defend the ceiling only |
| UX as an AI cockpit | 8 | 9 | desktop browser and operator usability acceptance across Today, Actions, Evidence, and Capabilities |
| CLI and API parity | 9 | 10 | exact-SHA parity drill over success, blocked, stale, and failure states |
| Extensibility and ecosystem | 9 | 10 | merged exact lane, second isolated adapter, compatibility, rollback, replay, and developer-tooling acceptance |
| Productized agent loop | 8 | 9 | desktop Today-to-approval-to-lease-to-execution-to-receipt-to-refreshed-Today trial |

The evaluator runs offline on macOS with network denied, a scrubbed
environment, bounded output and time, isolated pytest base directories, and
process-group cleanup. One scenario remains a truthful blocked sandbox posture;
the separately proven exact patch workflow is the implemented code-assistance
surface.

Operator surfaces:

- `GET /control-center/capabilities/surface` exposes baseline, candidate target,
  verified score, six independent evidence gates, blocker codes, and the next
  acceptance ref.
- `python scripts/dev/uaa_runtime.py capability-maturity` renders the same safe
  paths in human-readable form.
- `python scripts/run_agent_capability_evaluation.py --maturity-json` runs the
  bounded evaluator and can advance automated evidence readiness only.
- `python scripts/verify_capability_maturity_uplift.py` verifies that complete
  automated evidence does not silently advance any score.

The default API, CLI, and Control Center view intentionally shows
`evaluation_required`. After the evaluator passes, the posture becomes
`automated_evidence_ready`, while the verified weighted score remains the
baseline. Only an explicit decision bound to the exact evaluation digest and
the component-specific acceptance contract can change a score. Neither a score
nor an acceptance decision grants runtime authority.
