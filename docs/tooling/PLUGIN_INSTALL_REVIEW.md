# M79 Plugin Install Review

M79 adds Plugin Install Review, Disabled by Default. It reviews a plugin
install candidate using safe refs only and requires an exact approval binding to
the reviewed install review request, manifest security decision, manifest ref,
plugin ref, version, and actor.

The install review must be layered on an M78 manifest security decision. It
requires source package ref, provenance ref, static review, sandbox test plan,
Tool Broker mapping, Event Ledger plan, version pin, revocation, and a receipt
plan. Evaluator boundaries revalidate the current object fields before building
the decision, including fields mutated with `model_copy`.

M79 keeps plugin install disabled by default. It adds no plugin install, no
plugin enablement, no plugin execution, no runtime import, no network access,
no model/provider call, no browser automation, no shell execution, no mobile
device access, no remote execution, no credentials or cookies, no raw manifest
content, no raw package content, no raw prompt, no raw provider payload, no
backend route, no Control Center control, no dependency, no production
authority, and no M80 work. M80 remains future.
