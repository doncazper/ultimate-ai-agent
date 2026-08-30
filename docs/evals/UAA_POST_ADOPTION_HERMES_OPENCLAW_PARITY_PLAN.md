# Post-Adoption Hermes/OpenClaw Feature Parity Plan

Status: planned Queue V2 Q37 evaluation. It begins only after Q36, the
cross-module founder adoption closure, is completed. It grants no runtime,
provider, browser, connector-write, shell, public-distribution, or production
authority.

## Outcome

Evaluate the adopted UAA product against current Hermes Agent and OpenClaw
revisions through equivalent real workflows and direct inspection of their
operator surfaces. The result must say what is stronger, weaker, intentionally
different, missing, or unknown, then route only material UAA gaps to explicit
owners.

This is not a documentation inventory, screenshot contest, or claim that a
visible control is functional. Code, tests, exact configuration, direct
execution, durable state, failure recovery, and observed interaction behavior
outrank roadmaps and feature lists.

## Exact Comparison Boundary

Before testing, record for UAA, Hermes Agent, and OpenClaw:

- exact source revision, release, and relevant configuration;
- host class and supported client posture without durable raw local paths,
  usernames, hostnames, credentials, prompts, or response content;
- enabled and disabled capabilities, provider/model posture, and any setup
  blocker that prevents an equivalent task;
- the equivalent workflow corpus and the evidence expected from each run.

Unknown or inaccessible behavior remains `unknown`; it must not be scored as
implemented or missing without evidence. A later upstream revision requires a
new revision-bound observation, not silent reuse of prior findings.

## Functional Feature Matrix

Exercise comparable end-to-end work rather than merely locating components:

1. setup, identity, configuration, and safe-disable behavior;
2. ordinary chat plus multi-turn context, interruption, steering, retry, and
   resumption;
3. planning, tasks, queues, background work, and progress visibility;
4. memory, search, artifacts, citations, and durable conversation state;
5. tools, actions, approvals, authority disclosure, receipts, and audit trails;
6. CRM, News, communications, and other adopted module workflows where a peer
   has a meaningful equivalent;
7. failures, uncertainty, cancellation, restart, recovery, and retry safety;
8. local/private operation, portability, and variable Mac/Windows client use.

Equivalent tasks should reach a useful outcome through each product's normal
surface. If UAA requires an operator-critical raw-JSON or CLI workaround while
a peer completes the normal flow, record that as a product gap even though CLI
inspection remains a required UAA parity and diagnostic path.

## Direct Chat And Visual Inspection

Directly use the chat and adjacent operator surfaces. Capture redacted visual
evidence where it helps explain behavior, but pair it with interaction evidence.
Inspect:

- conversation hierarchy, density, readable use of space, and navigation;
- composer behavior, context or attachment selection, keyboard flow, and
  send/cancel/retry affordances;
- streaming, progress, tool/action disclosure, interruption, steering, and
  resumption;
- citations, artifacts, approvals, errors, uncertainty, and recovery inside
  the conversation;
- movement between chat, plans, tasks, memory, evidence, modules, and settings;
- persistence across refresh, restart, thread switching, and client changes;
- accessibility, focus order, responsive layout, and steps or time to a useful
  outcome.

A polished static surface does not prove function. Conversely, a capable
backend with a confusing or incomplete normal surface does not satisfy product
parity.

## Evidence And Disposition

For every compared capability, record:

- observed state: `stronger`, `weaker`, `intentionally_different`, `missing`,
  `equivalent`, or `unknown`;
- exact evidence refs and the limitation of that evidence;
- founder impact and severity;
- disposition: `adapt`, `study_only`, `retain_uaa_design`, or `no_action`;
- an explicit owner and next safe action for every material UAA gap.

Implement transferable patterns through original UAA-native work that keeps
Python Core ownership, API/CLI parity, policy, approvals, redaction, and
evidence boundaries intact. Do not copy competitor code, branding, unsafe
defaults, or shell-owned product truth.

## Finite Exit Gate

Q37 completes when:

1. exact revisions and relevant configurations are recorded;
2. the bounded equivalent-workflow corpus has been exercised or marked with an
   evidence-backed blocker;
3. chat and adjacent visual surfaces have direct interaction evidence;
4. the functional matrix and ranked reciprocal-learning ledger are durable;
5. every material UAA gap has an explicit owner and measurable exit test;
6. noncritical behavior and presentation polish is separated from functional,
   recovery, trust, and data-safety gaps; and
7. the evaluation makes no public, production, broad-authority, or inflated
   parity claim.

Unusual edge cases without material founder impact do not extend the comparison
indefinitely. New implementation work discovered here must enter Queue V2 as a
separate reviewed task; Q37 itself remains a bounded verification item.
