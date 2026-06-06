# Plugin Permission Model

M78 requires every plugin manifest to include declared permissions before it can
be considered review-ready. Declared permissions include a permission ref,
permission kind, risk level, safe purpose, and Tool Broker permission mapping.

Permission risk is deterministic and review-only. Low and medium permissions
remain disabled after review. High-risk capabilities require human approval for
high-risk capabilities and exact binding to the manifest, plugin, version, and
actor. Forbidden permission classes are denied.

Declared permissions do not grant install, enablement, execution, runtime
imports, network access, model/provider calls, browser automation, shell
execution, mobile device access, remote execution, credentials or cookies, raw
prompt exposure, raw provider payload exposure, backend routes, Control Center
controls, dependencies, or production authority.

M79 remains future.
