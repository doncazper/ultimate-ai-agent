# Queue Checkpoint Tag Plan

Status: active supplemental execution instruction

This plan supplements the 11 parked queue prompts without changing their
order, scope, source text, or recorded hashes. It explicitly authorizes
creating and pushing the new annotated checkpoint tags listed below when, and
only when, each exact checkpoint boundary has been completed and accepted.
It records the operator's queue-specific instruction; the document does not
independently grant runtime authority or broaden any queue item.

This authorization does not permit moving, deleting, replacing, reusing, or
force-pushing any existing tag. It does not authorize a GitHub Release,
package publication, deployment, public distribution, or a change to the
active `v0.104.0` / `0.104.0` product and package baseline.

## Required Tag Gate

Before creating each tag:

1. Complete the named checkpoint scope without silently broadening it.
2. Merge every required scoped PR.
3. Synchronize a clean worktree to the exact current `origin/main`.
4. Confirm all required exact-SHA CI, review, security, redaction, product
   truth, documentation, and post-merge checks are green.
5. Confirm no actionable review thread remains unresolved.
6. Record the exact main SHA, implemented/inactive/blocked truth, verification
   evidence, known limitations, and external-facility posture in the annotated
   tag message.
7. Create the tag only on that verified main commit and push only that new tag.
8. Verify that the remote tag resolves to the intended main SHA.
9. Install from the exact tag into a separate checkpoint-specific environment
   or application location without replacing another retained checkpoint.
10. Run proportionate CLI, API, Control Center launch, and principal product
    smoke tests against that installed checkpoint and record the tag, SHA,
    build identity, install command, results, and limitations.

If a tag already exists at the intended SHA, verify and reuse it without
mutation. If it exists at a different SHA, stop that tag action and report the
conflict; never retarget it. Do not tag planning-only output, a gap report,
failed acceptance, partially merged work, or an unproved external capability.

## Required Checkpoint Sequence

All checkpoints below are required, including those previously described as
optional:

1. After MSG-MX-012 acceptance:
   `checkpoint-msg-mx-012-acceptance`
2. After QUEUE 01 completes with truthful inactive posture:
   `checkpoint-governed-browser-inactive`
3. After QUEUE 02 adversarial hardening:
   `checkpoint-governed-browser-hardened`
4. During QUEUE 03, after Phase 03 local setup and packaging:
   `checkpoint-parity-local-install`
5. After QUEUE 03 Phase 10 acceptance:
   `checkpoint-parity-gap-closure`
6. After QUEUE 04:
   `checkpoint-delegated-document-mission`
7. After QUEUE 05:
   `checkpoint-capability-evaluation-lab`
8. After QUEUE 06:
   `checkpoint-work-board-macos`
9. After QUEUE 07:
   `checkpoint-news-signals-macos`
10. After QUEUE 08:
    `checkpoint-autocorrect-controls`
11. After the governed social-publishing program:
    `checkpoint-governed-social-publishing`
12. During the governed self-improvement program, after Phase 03:
    `checkpoint-self-improvement-review-loop`
13. During the governed self-improvement program, after Phase 08:
    `checkpoint-self-improvement-draft-pr-loop`
14. After governed self-improvement Phase 10 acceptance:
    `checkpoint-self-improvement-acceptance`
15. After the final Goat comparison, accepted repairs, rerun, and clean final
    main verification:
    `checkpoint-uaa-queue-final-acceptance`

The governed-browser inactive tag must say that real external targets remain
inactive. The capability-evaluation tag must preserve
`external_facility_required` when no accepted live facility exists. The social
publishing tag is conditional on its activation gate and accepted implemented
lane evidence; a Phase 0 gap report alone must not receive that implementation
tag.

## Queue Count Truth

The archived manifest contains 11 parked prompts after Messenger. Messenger
plus those 11 prompts yields 12 broad program boundaries. Do not synthesize an
additional parked prompt unless the operator supplies it explicitly.
