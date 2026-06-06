# M79 Plugin Install Review Receipt Plan

The M79 receipt plan stores safe refs only: install review request ref, manifest
security decision ref, manifest ref, plugin ref, version, source package ref,
static review ref, sandbox test plan ref, Tool Broker mapping ref, Event Ledger
plan ref, version pin ref, and revocation plan ref.

The receipt plan stores no raw manifest content, no raw package content, no raw
prompt, no raw provider payload, no credentials or cookies, and no secret-like
metadata. It records no side effects and no plugin install, no plugin
enablement, no plugin execution, and no runtime import.

Receipt plans are review evidence only. They do not grant backend route,
Control Center control, dependency, production authority, or M80 work. M80
remains future.
