# Claim Conflict And Staleness

Status: Active for v0.29.2 / M25.

M25 evidence chains carry conflict, stale, revoked, deleted, and superseded
markers. These markers cause safe denial for verified status unless a later
reviewed milestone defines a separate human-reviewed resolution path.

Conflict, staleness, revocation, deletion, and supersession are surfaced as
reason codes and warnings. They do not authorize truth, memory writes, action
approval, source mutation, or Event Ledger mutation.
