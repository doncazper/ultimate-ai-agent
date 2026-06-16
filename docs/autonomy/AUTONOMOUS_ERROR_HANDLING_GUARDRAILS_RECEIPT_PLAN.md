# M138 Receipt Plan

M138 receipts are safe-summary-only and safe-ref-only. They may store error
signal refs, guardrail policy refs, retry policy refs, fallback policy refs,
escalation policy refs, recovery plan refs, rollback plan refs, resume plan
refs, human checkpoint refs, audit refs, replay refs, revocation refs, and
kill-switch refs.

Receipts must store no raw error log, no raw stack trace, no raw prompt, no raw
provider payload, no cookies, no credentials, no secrets, no retry output, no
rollback output, no resume output, and no recovery output. They must record no
error handling runtime, no retry execution, no rollback execution, no resume
execution, and no recovery execution.
