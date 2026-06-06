# Ultimate AI Agent Version

Current active baseline: **v0.72.0**

v0.72.0 implements M68 Autonomy Risk Classifier. It adds contract-only,
review-only, deterministic classifier contracts that derive the highest risk
from caller-declared risk, scoped approval bundle risk, and explicit risk
signals. It binds classifier decisions to exact scoped approval bundle refs,
Revocation + Kill Switch refs, source scope refs, actor refs, resource refs,
capability refs, allowlist refs, audit refs, replay refs, and approval refs as
identifiers only. It denies risk downgrades, revalidates scoped approval bundles
and Revocation + Kill Switch records at evaluator boundaries, and adds tests,
documentation-integrity checks, static verification, and Foundation Gate
coverage.

It adds no policy activation, session start, autonomous actions, background
worker, execution, tool execution, shell execution, network tools, browser
automation, plugin execution, mobile sensor access, remote execution, memory
writes, context injection, model/provider authority, backend routes, Control
Center controls, dependencies, M69 work, or production authority.
