# M37 to M38 Boundary

Status: active milestone boundary.

M37 implements Review Approval Capture, Review-Only Persistence. It captures
safe approval or denial records bound to exact redacted review packets.

M37 did not implement M38. M38 is now implemented/released by v0.42.0 as Safe
Context Proposal From Approved Review. M37 itself still adds no context
proposal, no context injection, no automatic context handoff, no memory write,
no export, no raw file read, no execution, and no production authority.

An M37 review approval record may be consumed by the M38 proposal contract only
when it exactly matches the approved redacted review packet. It cannot itself
become context, authorize context injection, authorize OpenWebUI handoff,
authorize memory writes, authorize export, authorize execution, or authorize
raw file access.
