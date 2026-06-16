# M133 To M134 Boundary

M133 implements Long-Running Task Supervisor as a review-only contract. It may
record safe supervisor refs, heartbeat plan refs, checkpoint plan refs, context
budget refs, pause condition refs, resume condition refs, stop condition refs,
audit refs, replay refs, revocation refs, kill-switch refs, and no-effect
receipt refs.

M134 remains future as Human Checkpoint Scheduling. M133 does not add human
checkpoint scheduling, runtime prompts, scheduler loops, background workers,
notification delivery, approval capture, or task execution.
