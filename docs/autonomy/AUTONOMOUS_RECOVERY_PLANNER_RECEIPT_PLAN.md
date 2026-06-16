# Autonomous Recovery Planner Receipt Plan

M135 receipts are no-effect receipt records. They store safe summaries and safe
refs only.

The receipt plan binds recovery plan ref, scope ref, M134 human checkpoint
scheduling decision ref, M133 supervisor decision ref, M132 trusted workflow
decision ref, failure signal ref, recovery trigger ref, rollback plan ref,
resume plan ref, checkpoint ref, human checkpoint ref, audit ref, replay ref,
revocation ref, and kill-switch ref.

The receipt plan stores no raw prompt, no raw provider payload, no secret, no
recovery execution, no retry execution, no resume execution, no rollback
execution, no supervisor runtime, no checkpoint scheduler, no prompt, no
notification delivery, and no execution result.
