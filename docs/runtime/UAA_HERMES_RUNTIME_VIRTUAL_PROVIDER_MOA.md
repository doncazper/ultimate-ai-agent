# UAA Hermes Runtime Virtual Provider MoA

Status: Hermes Runtime Adoption Phase 20 repo-safe read model

## Full-Strength Version

UAA can define virtual multi-agent provider presets such as Codex implementer,
Claude reviewer, Hermes researcher, local verifier, security reviewer, and UAA
supervisor while keeping UAA in control of route decisions, approval mode,
cost posture, output envelopes, comparison proof, and safe-disable posture.

## Repo-Safe Version

Phase 20 adds Python Core virtual-provider Mixture-of-Agents posture:

- `GET /api/runtime/virtual-provider-moa`
- `scripts/dev/uaa_runtime.py inspect-virtual-provider-moa`
- `RuntimeVirtualProviderMoaReadModel`
- preset refs for implement/review, research/verify, and security-review board
  shapes
- per-agent slot refs with role, configured/runtime/provider refs, capability
  evidence refs, routing-policy refs, output-envelope refs, and comparison
  proof refs
- route-decision trace refs, cost-estimate refs, approval-mode refs,
  safe-disable refs, proof refs, verifier refs, blocked authority refs, and
  next-safe-action refs

This is readiness and metadata posture only. It does not perform live model
fan-out, call provider SDKs, dispatch external runtimes, use hidden advisor
prompts, treat agent output as authority, write connectors, run shell or
browser work, or claim production authority.

## Blocked / Needs Authority

- live multi-agent model fan-out
- provider SDK calls
- external runtime dispatch
- hidden advisor prompts or hidden context injection
- agent output as production truth, approval, or execution authority
- connector, shell, browser, Git, or file mutation from virtual provider slots
- production authority

## Exact Promotion Path

Future promotion requires route decision traces, bounded cost estimates,
explicit approval mode, per-agent output envelopes, comparison proof, safe-
disable posture, idempotency, redaction, CLI/API/Core parity, route
classification updates, and focused verifier coverage. Each provider/runtime
slot must remain independently policy-bound, receipt-backed, and unable to
grant authority to another slot.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_hermes_runtime_virtual_provider_moa.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_20.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
```
