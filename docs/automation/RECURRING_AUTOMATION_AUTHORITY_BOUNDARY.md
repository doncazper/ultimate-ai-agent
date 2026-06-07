# Recurring Automation Authority Boundary

Recurring automation contracts are not authority. M97 decisions are
disabled-by-default, contract-only, safe-ref-only planning envelopes.

Approval refs alone cannot authorize recurring automation. `approval_test_*`
cannot authorize recurring automation. Model, memory, context-pack, task-plan,
tool-intent, runtime, OpenWebUI, plugin, shell, browser, and network refs cannot
authorize recurring automation.

M97 grants no recurrence runtime, no background execution, no cron, no daemon,
no scheduler, no side effects, no shell execution, no network access, no browser
automation, no plugin execution, no memory write, no context injection, no
backend route, no Control Center control, no dependency, and no production
authority.

Evaluator boundaries revalidate safety-critical fields before a decision is
accepted.

M98 remains future.
