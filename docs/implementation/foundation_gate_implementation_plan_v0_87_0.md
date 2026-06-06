# Foundation Gate Implementation Plan v0.87.0

v0.87.0 implements M83 Shell Dry-Run Classifier with classifier-only,
review-only, deterministic, local-only contracts over M82 command proposals.

Foundation Gate coverage:

- M83 classifier contract exists.
- M83 static safety scan denies dry-run execution, shell execution, command
  execution, subprocess execution, process spawn, routes, dependencies, and
  production authority.
- M83 OpenAPI path count remains unchanged.
- M83 roadmap currentness marks M83 implemented and keeps M84-M100 planned.

Skill Package Security Rule remains active. All skills are untrusted packages by default and require a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities before any future runtime use. M83 does not enable skill package execution, plugin execution, or package installation.

M83 adds no dry-run execution, shell string, command execution, subprocess
execution, shell execution, process spawn, filesystem mutation, network access,
tool execution, browser automation, plugin execution, remote execution, model
call, memory write, context injection, background worker, backend route,
Control Center control, dependency, M84 work, or production authority.
