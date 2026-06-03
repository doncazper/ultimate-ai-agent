# Approval Expiry, Revocation, and Replay

Status: active
Current through: v0.32.0
Purpose: Define M28 approval grant lifetime and replay protection.

Approval Authority v2 denies grants that are expired, revoked, replayed,
superseded, blocked, inactive, or otherwise invalid. Replay protection uses a
nonce boundary so a used replay nonce cannot authorize another policy decision.

Denied grant states include:

- expired grant or expired scope.
- revoked grant.
- replayed grant nonce.
- inactive, superseded, blocked, or invalid grant status.
- wildcard scope.
- actor/action/resource/scope mismatch.

These protections are policy checks only. They do not create production approval
authority, action execution, tool execution, memory writes, file mutation,
network calls, model/provider calls, shell execution, browser/mobile/remote/
plugin execution, backend execution routes, dependencies, or M29 work.

M29 remains planned/provisional.
