# M139 Receipt Plan

M139 receipts are safe-summary-only and safe-ref-only. They may store abuse
signal refs, loop signal refs, pattern policy refs, threshold policy refs,
intervention plan refs, escalation plan refs, human checkpoint refs, audit
refs, replay refs, revocation refs, and kill-switch refs.

Receipts must store no raw abuse log, no raw loop trace, no raw prompt, no raw
provider payload, no cookies, no credentials, no secrets, no detector output,
no intervention output, and no recovery output. They must record no detector
runtime, no loop intervention, and no recovery execution.
