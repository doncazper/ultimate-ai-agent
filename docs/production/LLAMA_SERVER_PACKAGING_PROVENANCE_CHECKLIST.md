# llama-server Packaging Provenance Checklist

Status: active UAA-P0-015 llama-server packaging/provenance checklist
Scope: local loopback readiness for the M166/M167 local model lane
Authority source: M166 exact-scope local llama.cpp/OpenWebUI shell gate

This checklist is the repo-owned packaging and provenance review artifact for
local `llama-server` operation. It is guidance for release-readiness evidence,
not an installer, downloader, updater, launcher, binary trust service, or public
distribution package.

M166 remains the exact-scope authority gate. This document adds no production
authority, no runtime model/provider authority, no unrestricted
shell/subprocess execution, no broad network authority, no connector writes, no
plugin runtime import, no mobile control, and no autonomous background
execution. Any later runtime behavior must still be scoped by a milestone,
approved, audited, rollback-aware, verifier-covered, and bound to safe refs.

## Evidence Rules

Packaging evidence must use safe refs and redacted summaries only. Durable
evidence, release docs, reports, tests, and logs must not contain raw prompts,
raw responses, raw provider payloads, raw local paths, raw logs, usernames,
hostnames, serials, environment dumps, credential material, or secret-like
values.

The checklist does not install, launch, download, sign, publish, or trust a
binary. It records whether a reviewer has enough safe evidence to treat local
`llama-server` prerequisites as passed, blocked, pending, or not-scoped.

## Checklist

| Review area | Required operator evidence | Safe evidence shape | Pass condition | Blocked or unknown handling |
|---|---|---|---|---|
| `llama-server` discovery | A reviewer can identify the candidate binary through an approved local discovery flow. | `discovery-ref:llama-server:*` plus redacted binary label, version summary, architecture class, and safe location class. | Candidate matches an approved discovery ref and no raw path evidence is required. | Block if discovery relies on a filename alone, a raw path, unreviewed shell output, or an unapproved process scan. |
| Allowed locations | Candidate location is one of the reviewed local classes allowed by the M166/M167 runbook. | `location-class-ref:llama-server:*` such as managed local tool cache, reviewed developer build output, or approved local package manager cache. | Location class is reviewed, local, loopback-oriented, and rollback-aware. | Block if the location is unknown, remote-mounted, world-writable without review, hidden behind an unreviewed symlink, or requires durable raw path evidence. |
| Provenance review | Source, build, package, or acquisition story is reviewed before runtime evidence is accepted. | `provenance-ref:llama-server:*` with source kind, reviewer ref, version summary, build/acquisition summary, and risk notes. | Provenance is known, reviewer-bound, and compatible with local loopback-only use. | Unknown provenance is blocked or not production-ready. Do not infer trust from popularity, local presence, or successful startup. |
| Checksum/signature verification | Integrity evidence is reviewed for the exact candidate. | `integrity-ref:llama-server:*` with checksum status, signature status when available, reviewer ref, and verification result ref. | Checksum matches the reviewed expected value, or signature verification passes where signatures are available. | Block if checksum/signature evidence is missing, mismatched, stale, unreviewed, or tied to a different candidate. |
| Offline operation | Approved local operation can proceed without new network access after required artifacts are present. | `offline-ref:llama-server:*` with prerequisite summary, denied-network expectation, and reviewer ref. | Runtime checklist can be satisfied from already-approved local artifacts and loopback-only configuration. | Block if startup requires unreviewed downloads, telemetry, remote calls, auth prompts, or broad network authority. |
| Rollback | Reverting to a known-good local state is planned before live evidence is accepted. | `rollback-ref:llama-server:*` with previous-known-good ref, stop/restore summary, cache policy ref, and reviewer ref. | Rollback is documented, local, idempotent, and does not require raw logs or raw paths in evidence. | Block if rollback is manual guesswork, destructive without review, or cannot restore the prior approved candidate. |
| Cache cleanup | Cleanup removes stale or failed local artifacts without deleting approved evidence refs. | `cleanup-ref:llama-server:*` with cache class, retention summary, rollback impact, and reviewer ref. | Cleanup plan preserves audit, receipt, provenance, integrity, and rollback refs while clearing stale local artifacts. | Block if cleanup would erase evidence needed for review, remove rollback state, expose raw paths, or require broad filesystem authority. |
| Blocked/unknown provenance handling | Review state is explicit when packaging evidence is insufficient. | `blocker-ref:llama-server:*` with blocker reason, owner, next review step, and safe target state. | Unknown or unverified candidates remain blocked, pending, or not-scoped until evidence is reviewed. | Do not mark unverified binaries production-ready. Fail closed with safe, operator-actionable guidance. |

## Status Values

| Status | Meaning |
|---|---|
| passed | Reviewed safe refs show the packaging prerequisite is satisfied for the exact local loopback scope. |
| blocked | The prerequisite is scoped but cannot be accepted until the named blocker is resolved. |
| pending | The prerequisite is expected but reviewed evidence has not been attached. |
| not-scoped | The behavior is outside M166/M167 and needs a later accepted scoped milestone. |

## Operator Rules

- Discovery must be exact and reviewable; do not trust a candidate only because
  it is named `llama-server`, appears in a process list, or starts locally.
- Allowed locations are safe location classes, not durable raw path evidence.
- Provenance review happens before checksum/signature results are accepted as
  release evidence.
- Unverified binaries are blocked or not production-ready.
- Offline mode is required after approved artifacts are present; new network
  access is not part of this checklist.
- Rollback must be defined before M167 live evidence can be accepted.
- Cache cleanup must preserve audit, receipt, provenance, integrity, and
  rollback refs.
- Packaging failures fail closed with safe, operator-actionable guidance.

## Non-Goals

UAA-P0-015 does not claim or add:

- public distribution
- signed installer readiness
- broad binary trust
- unreviewed binary trust
- broad network authority
- unrestricted shell/subprocess execution
- shell authority beyond scoped llama.cpp operation
- connector writes
- plugin runtime import
- mobile control
- autonomous background execution
- provider/model output as authority
- production runtime behavior outside the M166/M167 local loopback lane

## Rollback

If this checklist is rolled back, remove links to this document from the active
docs index, canonical map, M167 production-hardening docs, evidence matrix,
local smoke harness, product truth packet, and current Kanban board. Until a
replacement checklist is accepted, M167 packaging evidence must remain blocked
or pending for production-readiness review.
