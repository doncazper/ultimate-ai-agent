# Plugin Manifest Policy

M78 policy enables only the Plugin Manifest Security Model. The model checks
review readiness for disabled plugin manifests; it does not enable plugins.

The policy requires declared permissions, source/provenance metadata, static
review, sandbox test plan, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation support, and human approval for high-risk
capabilities.

The policy denies no plugin install, no plugin enablement, no plugin execution,
no runtime import, no network access, no model/provider call, no browser
automation, no shell execution, no mobile device access, no remote execution,
no credentials or cookies, no raw prompt, no raw provider payload, no backend
route, no Control Center control, no dependency, and no production authority.

Evaluator boundaries revalidate policy fields before a decision is built. M79
remains future.
