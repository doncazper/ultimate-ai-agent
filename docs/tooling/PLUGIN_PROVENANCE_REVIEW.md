# Plugin Provenance Review

M78 requires source/provenance metadata for every reviewed plugin manifest.
Source and provenance refs explain where a manifest came from; they are not
authority and cannot authorize plugin install, plugin enablement, plugin
execution, or production authority.

Static review is required before a manifest can be review-ready. Static review
must evaluate declared permissions, source/provenance metadata, Tool Broker
permission mapping, Event Ledger logging, version pinning, revocation support,
and human approval for high-risk capabilities.

No raw prompt, raw provider payload, credentials or cookies, backend route,
Control Center control, dependency, or production authority is added by M78.
Evaluator boundaries revalidate provenance fields. M79 remains future.
