# M113 Secrets Boundary Policy

M113 policy requires contract-only, review-only, safe refs, actor-bound,
baseline-bound, source-identity-model-bound, user-bound, workspace-bound,
credential-vault-contract-bound, audit, replay, secret boundary refs,
credential scope refs, a redaction policy ref, and a no-effect receipt plan.

The policy denies production authority, production runtime, auth runtime, login,
session cookie handling, credential handling, credential storage, credential
read, credential write, secret material access, secret export, vault runtime,
account connector, network access, model call, memory write, context injection,
execution, tool execution, shell execution, browser automation, plugin
execution, mobile sensor, background worker, remote execution, backend route,
Control Center control, dependency, and side effects.

Evaluator boundaries revalidate current object fields, including model_copy
mutations. A credential vault contract ref is an identifier only; it is not
runtime authority and it cannot authorize credential access.
