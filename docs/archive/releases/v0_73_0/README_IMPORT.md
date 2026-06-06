# README Import - v0.73.0

v0.73.0 implements M69 Low-Risk Autonomous Dry Run.

Import summary: contract-only, review-only, dry-run-only, deterministic
low-risk autonomous dry-run records over exact M68 Autonomy Risk Classifier
decisions. The low risk ceiling is enforced, higher-risk classifier decisions
and higher-risk dry-run steps are denied, and approval refs are identifiers
only.

No policy activation, session start, autonomous action, background worker,
execution, tool execution, shell execution, network tool, browser automation,
plugin execution, mobile sensor access, remote execution, memory write, context
injection, model/provider authority, backend route, Control Center control,
dependency, M70 work, or production authority is added.
