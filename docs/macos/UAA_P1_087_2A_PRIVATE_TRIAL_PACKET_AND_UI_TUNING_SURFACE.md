# UAA-P1-087.2a Private Trial Packet And UI Tuning Surface

Status: implemented as an incremental local/private trial packet and read-only
Control Center tuning surface.

UAA-P1-087.2a prepares the full UAA-P1-087.2 in-person/private UI functional
tuning milestone without claiming that accepted in-person founder findings are
complete. It uses the proven `uaa trial-boot` contract from UAA-P1-087.1 to
define the safe evidence packet, checklist, friction refs, UI/copy task refs,
and core-loop gap refs that the full UAA-P1-087.2 trial must review.

The packet is intentionally safe-ref-only and does not claim public beta, public
distribution, production readiness, connector writes, memory writes, action
execution, provider/model authority, Code apply, or OpenWebUI product-state
ownership.

## Packet

The canonical packet is:

```text
docs/macos/private_operator_trial_packet_v1.json
```

It records:

- local boot checklist state;
- Today, Actions, Memory, Evidence, Chat/Plans handoff, blocked-state language,
  and CRM-lite follow-up findings;
- manual smoke evidence refs;
- friction refs;
- UI/copy task refs;
- core loop gap refs;
- blocked authority refs.

The Control Center exposes the packet at `/private-trial` as a read-only
operator surface. This route adds no backend endpoint, OpenAPI operation,
middleware, auth, CORS, security header, rate limit, connector behavior,
runtime model call, browser automation, shell authority, native app behavior, or
action execution.

## Current Findings

Current safe packet findings:

- Local Boot: pass for repo-local dual-surface boot readiness; Control Center is
  first-party and OpenWebUI remains secondary or blocked.
- Today: partial; the product spine is visible, but repeated operator review
  still needs scan-friction tuning.
- Actions: partial; reviewable envelopes and memory-derived proposals are
  visible while state changes remain blocked.
- Memory: partial; provenance, quality, intake, review, and loop refs are
  visible without memory writes.
- Evidence: partial; history grammar is readable but should stay compact.
- Chat/Plans Handoff: blocked until durable receipts and handoff refs exist.
- Blocked State Language: partial; copy should bias toward next safe action.
- CRM-Lite Follow-Ups: blocked until local business state and memory/action
  receipts are scoped.

## Full UAA-P1-087.2 Gate

UAA-P1-087.2 should remain planned until a local/private operator trial reviews
this packet and accepts or revises the findings. The full milestone should then
record accepted UI/copy tuning changes, manual smoke evidence refs, and
remaining blocker refs before moving to UAA-P1-087.3.

## Verification

Run:

```bash
.venv/bin/python scripts/verify_uaa_p1_087_2a_private_trial_packet.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_uaa_p1_087_2a_private_trial_packet.py
cd apps/control-center && npm test -- --run src/App.test.tsx
```

UAA-P1-087.3 must remain source-only planning/scaffold work until full
UAA-P1-087.2 local/private UI functional tuning evidence is accepted.
