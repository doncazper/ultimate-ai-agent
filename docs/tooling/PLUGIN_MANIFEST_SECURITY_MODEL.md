# Plugin Manifest Security Model

M78 adds a Plugin Manifest Security Model for future plugin lifecycle work. It
is a contract and validation milestone only. It reviews plugin manifest metadata
before any later install review.

Every reviewed manifest must declare:

- manifest and plugin refs.
- declared permissions.
- source/provenance metadata.
- static review.
- sandbox test plan.
- Tool Broker permission mapping.
- Event Ledger logging.
- version pinning.
- revocation and disable plan.
- human approval for high-risk capabilities.

Plugins remain disabled. M78 adds no plugin install, no plugin enablement, no
plugin execution, no runtime import, no network access, no model/provider call,
no browser automation, no shell execution, no mobile device access, no remote
execution, no credentials or cookies, no raw prompt, no raw provider payload,
no backend route, no Control Center control, no dependency, and no production
authority.

Plugin refs are identifiers only. Approval refs are identifiers only.
`approval_test_*` is not runtime authority. Model output, runtime output,
OpenWebUI output, memory refs, context refs, tool-intent refs, and approval refs
cannot authorize plugin install, plugin enablement, plugin execution, or
production authority.

Evaluator boundaries revalidate safety-critical fields, including objects
mutated with `model_copy`. M79 remains future.
