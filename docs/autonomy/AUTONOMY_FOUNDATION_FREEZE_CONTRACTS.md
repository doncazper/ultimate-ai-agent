# Autonomy Foundation Freeze Contracts

M70 defines deterministic Autonomy Foundation Freeze records for review only.

## Policy Contract

The default policy is contract-only, review-only, freeze-only, autonomy
foundation only, and deterministic. It disables policy activation, session
start, low-risk dry-run execution, autonomous actions, background workers,
execution, tool execution, shell execution, network tool use, browser
automation, plugin execution, mobile sensor access, remote execution, memory
write, context injection, model/provider call, backend route enablement,
Control Center control enablement, dependency change, and production authority.

## Request Contract

An Autonomy Foundation Freeze request contains:

- `request_ref`
- `freeze_ref`
- `baseline_ref`
- `actor_ref`
- accepted milestone refs for M61-M69
- explicit checklist refs
- safe summary

The request is contract-only, review-only, freeze-only, autonomy foundation
only, and deterministic. It cannot request policy activation, session start,
low-risk dry-run execution, autonomous actions, background workers, execution,
tool execution, shell execution, network tool use, browser automation, plugin
execution, mobile sensor access, remote execution, memory write, context
injection, model/provider call, backend routes, Control Center controls,
dependency changes, or production authority.

## Report Contract

An Autonomy Foundation Freeze report contains:

- exact request and freeze refs
- baseline and actor refs
- accepted M61-M69 milestone refs
- checklist refs
- stable reason codes
- safe summary

The report is not policy activation, not session start, not low-risk dry-run
execution, not autonomous action authority, not background worker authority,
not execution authority, not context injection authority, not memory write
authority, not model/provider authority, not backend route authority, and not
production authority.

Evaluator boundaries revalidate the current object fields and do not trust
constructor-time validation alone. Model-copy mutated policy activation flags,
session start flags, low-risk dry-run execution flags, autonomous action
flags, background-worker flags, execution flags, tool/shell/network/browser/
plugin/mobile/remote flags, context-injection flags, memory-write flags,
model/provider call flags, backend-route flags, Control Center control flags,
dependency flags, production-authority flags, accepted milestone refs,
checklist refs, and secret-like metadata are denied.

M71 remains future.
