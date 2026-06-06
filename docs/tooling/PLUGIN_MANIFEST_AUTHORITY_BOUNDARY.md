# Plugin Manifest Authority Boundary

M78 does not make plugin manifests authority. A reviewed manifest is not a
permission grant, not an install approval, not enablement, not execution, and
not production authority.

Approval refs are identifiers only. `approval_test_*` is never runtime
authority. Human approval for high-risk capabilities must bind exactly to the
manifest ref, plugin ref, plugin version, and actor ref, and expired, revoked,
or replayed approvals are denied.

Model output, runtime output, OpenWebUI output, memory refs, context refs,
tool-intent refs, approval refs, source/provenance metadata, static review
refs, sandbox test plan refs, Tool Broker permission mapping refs, Event Ledger
logging refs, version pinning refs, and revocation refs cannot authorize plugin
install, plugin enablement, plugin execution, runtime imports, network access,
model/provider calls, browser automation, shell execution, mobile device
access, remote execution, credentials or cookies, raw prompt exposure, raw
provider payload exposure, backend routes, Control Center controls,
dependencies, or production authority.

Evaluator boundaries revalidate safety-critical fields. M79 remains future.
