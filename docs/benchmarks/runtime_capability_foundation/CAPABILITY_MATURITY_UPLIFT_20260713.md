# Capability maturity uplift

Status: implemented evidence gate; targets require a passing bounded evaluation.

This slice turns the 16-component comparison into an executable acceptance
contract. A score stays at its baseline until real repository scenarios prove
the expected safe outcome, evidence completeness, absence of unsupported
claims or policy violations, and replay or recovery correctness where
applicable. A score is operator information only; it grants no runtime
authority.

| Component | Baseline | Target | Runtime proof |
|---|---:|---:|---|
| Reasoning and task understanding | 8 | 9 | ambiguity and immutable revision scenarios |
| Planning and orchestration | 10 | 10 | DAG replay, cancellation, and settlement recovery |
| Learning and adaptation | 8 | 9 | idempotent governed feedback replay |
| Memory and context management | 9 | 10 | correction precedence and content-free receipts |
| Communication and interaction quality | 8 | 9 | readable handoff and blocked-state truth |
| Action and tool calling | 9 | 10 | exact dispatcher idempotency |
| Autonomy and authority management | 10 | 10 | approval expiry and request-scoped denial |
| Code and implementation assistance | 8 | 9 | exact approved patch with redacted receipt |
| Research, web, and external information | 10 | 10 | SearXNG/Firecrawl preservation and injection isolation |
| Model and provider management | 8 | 9 | proposal-only routing explanation and cost-risk visibility |
| Evidence, audit, and observability | 9 | 10 | tamper detection and surface parity |
| Safety, security, and failure handling | 10 | 10 | durable tamper denial |
| UX as an AI cockpit | 8 | 9 | backend-owned maturity and founder-loop rendering |
| CLI and API parity | 9 | 10 | identical safe capability-surface projection |
| Extensibility and ecosystem | 9 | 10 | exact extension adapter dispatch and replay |
| Productized agent loop | 8 | 9 | founder loop through terminal receipt and memory candidate |

The evidence gate contains 23 bounded scenarios. It executes offline on macOS
with network denied, a scrubbed environment, bounded output and time, isolated
pytest base directories, and process-group cleanup. One scenario remains a
truthful blocked sandbox posture; the separately proven exact patch workflow is
the implemented code-assistance proof.

Operator surfaces:

- `GET /control-center/capabilities/surface` exposes the backend-owned baseline,
  target, verification posture, evidence refs, and blockers.
- `python scripts/dev/uaa_runtime.py capability-maturity` renders the safe plan.
- `python scripts/run_agent_capability_evaluation.py --maturity-json` runs the
  bounded evaluation and emits its content-free evidence-gated result.
- `python scripts/verify_capability_maturity_uplift.py` is the finite acceptance
  command.

The default API, CLI, and Control Center view intentionally shows
`evaluation_required`; it does not run a test suite on request and does not
claim a target from static configuration. Only the explicit evaluator can
produce `targets_proven`.
