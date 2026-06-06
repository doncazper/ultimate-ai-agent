# Plugin Sandbox Test Plan

M78 requires a sandbox test plan ref as part of plugin manifest security review.
This is a plan contract only. M78 does not run plugins, import plugin code,
install packages, execute commands, connect to networks, call models, or start
browser/mobile/remote workflows.

The sandbox test plan must remain paired with declared permissions,
source/provenance metadata, static review, Tool Broker permission mapping, Event
Ledger logging, version pinning, revocation support, and human approval for
high-risk capabilities.

M78 keeps plugins remain disabled and adds no plugin install, no plugin
enablement, no plugin execution, no runtime import, no network access, no
model/provider call, no browser automation, no shell execution, no mobile
device access, no remote execution, no credentials or cookies, no raw prompt,
no raw provider payload, no backend route, no Control Center control, no
dependency, and no production authority.

Evaluator boundaries revalidate sandbox test plan refs. M79 remains future.
