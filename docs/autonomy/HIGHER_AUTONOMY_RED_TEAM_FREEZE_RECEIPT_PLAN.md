# M140 Receipt Plan

M140 receipts are safe-summary-only and safe-ref-only. They may store accepted
M131-M139 checkpoint refs, red-team checklist refs, audit refs, replay refs,
revocation refs, kill-switch refs, and no-effect receipt refs.

Receipts must store no raw prompt, no raw provider payload, no cookies, no
credentials, no secrets, no red-team runtime output, no red-team harness
output, no adversarial test output, no autonomous execution output, and no
production authority output. They must record no red-team runtime, no harness
execution, no adversarial test execution, no autonomous execution, no browser
action, no connector action, no tool execution, no shell execution, no network
access, no plugin execution, no model call, no memory write, no context
injection, no backend route, no Control Center control, no dependency, no
alpha release, no beta release, and no production authority.
