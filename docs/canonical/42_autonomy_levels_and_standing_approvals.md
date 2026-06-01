# 42 — Autonomy Levels and Standing Approvals

Status: Foundation permissions spec, v0.5.3
Owner: Trust / Orchestrator

## Autonomy levels

| Level | Name | Meaning |
|---:|---|---|
| L0 | Answer only | No tools, no memory writes, no external actions. |
| L1 | Draft only | Can draft plans/artifacts; no persistent mutation. |
| L2 | Recommend | Can inspect permitted context and recommend actions. |
| L3 | Prepare and ask | Can prepare tool/file/external actions, but waits for approval. |
| L4 | Execute reversible trusted actions | Can execute low/medium-risk reversible actions under standing approval. |
| L5 | Trusted recurring workflow | Can run explicitly approved recurring workflows within strict scope/budget. |

## Risk mapping

```text
read-only low sensitivity: L2 allowed with consent
local reversible file write: L3 by default; L4 with standing approval
memory write: L3 by default; L4 for low-risk source-linked project memory
external send/publish/payment/delete/admin: always explicit approval
credential changes: explicit approval
TCB changes: blocked from autonomous self-improvement
```

## Standing approval rules

Standing approvals must be:

```text
specific
revocable
time-bounded or scope-bounded
auditable
budget-bounded when costs exist
never valid for high/critical actions
visible in User Control Center
```

## Anti-rubber-stamp rule

The agent should batch low-risk approvals, explain risk clearly, and avoid repeatedly asking for trivial confirmations that train the user to approve blindly.

## Future Mobile Autonomy Limits

Mobile device capabilities do not raise autonomy by themselves. A mobile device, paired app, OS permission, notification response, or arbitrary approval string cannot authorize hidden sensor capture or external actions.

High-risk mobile capture such as camera, microphone, or precise location requires explicit purpose and governed approval rules. Always-on microphone, background location history, contacts bulk export, hidden sensor access, and unapproved external send are critical or forbidden by default.

Mobile emergency stop and kill switch are future safety controls, not broad mobile authority.
