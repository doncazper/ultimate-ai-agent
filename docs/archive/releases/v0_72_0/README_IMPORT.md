# README Import - v0.72.0

v0.72.0 implements M68 Autonomy Risk Classifier.

Import summary: contract-only, review-only, deterministic autonomy risk
classification over exact scoped approval bundles and Revocation + Kill Switch
records. Derived risk is the highest of declared risk, bundle risk, and explicit
risk signals. Risk downgrade is denied. Approval refs are identifiers only.

No policy activation, session start, autonomous action, background worker,
execution, tool execution, shell execution, network tool, browser automation,
plugin execution, mobile sensor access, remote execution, memory write, context
injection, model/provider authority, backend route, Control Center control,
dependency, M69 work, or production authority is added.

