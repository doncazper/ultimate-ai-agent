# UAA Hermes Runtime Session Continuity

Phase 29 adds a backend-owned, AuthorityState-bound read model for
multi-surface runtime session continuity. It is a UAA-native operator-control
posture, not a messaging gateway, account sync system, connector write lane, or
remote session runtime.

## Full-Strength

UAA sessions can be visible across desktop, CLI, future mobile, delegated
runtimes, Coding Cockpit, Evidence, Proof, and other operator surfaces. The
operator can see which surfaces refer to the same session, which are stale, where
conflicts exist, and which channel last reported a receipt.

## Repo-Safe

The current implementation exposes safe session continuity refs only:

- `GET /api/runtime/session-continuity`
- `uaa runtime inspect-session-continuity`
- AuthorityState route/CLI/mapping/catalog/decision/reason refs for
  `lane-ref:runtime-session-continuity-read-model`
- unsupported adapter refs for external gateway, account sync, connector write,
  remote session, turn-material persistence, provider-material persistence, and
  authority minting
- source labels for Control Center desktop, CLI, delegated runtime, Coding
  Cockpit, and future mobile posture
- current, stale, conflict-review, and blocked states
- redacted evidence, proof, receipt, staleness, and conflict refs
- Control Center presentation in the Runtime panel

No raw transcripts, prompts, responses, provider payloads, account material, or
local paths are persisted. The Control Center can inspect the decision refs but
cannot mint or widen authority.

## Blocked / Needs Authority

The following remain blocked:

- external messaging gateway
- account sync
- connector writes
- remote sessions
- raw transcript, prompt, response, or provider payload persistence
- Control Center authority minting

## Exact Promotion Path

Promotion requires an exact lane with:

- channel identity
- authorization binding
- redaction boundary
- delivery receipt
- revoke posture
- audit record
- CLI/API/Core parity
- focused verifier coverage

Planning artifacts and stale session refs do not grant authority.

## Verification

Run:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_hermes_runtime_session_continuity.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_29.py
```
