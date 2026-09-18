# FIN-003 Explicit Finance Configuration Through Normal Startup

Status: the separately admitted `dev-task:finance-fin003-normal-startup` child
merged in PR #485 at `66bd2f48e1ac220589430423e7bf6c0622406999`, with scoped
post-merge startup checks and owned cleanup recorded. FIN-003 and Q26 remain
incomplete. The [managed setup continuation](UAA_FINANCE_FIN003_MANAGED_SETUP.md)
adds separately confirmed profile enrollment and extends startup capture.

## Scope

The developer launcher and installed macOS runtime must preserve the existing
four Finance configuration values only for the Python backend. Core remains
responsible for validating the private synthetic repository, pinned native
helper, and safe-disable state. Missing or malformed configuration remains a
visible unavailable state. Empty values must retain their meaning, particularly
the fail-closed empty safe-disable setting.

A running backend may be reused only when its owned launch metadata binds the
same Finance configuration as the requested launch. Changed or unproven
configuration requires an explicit owned stop and restart. A successful health
response alone cannot establish that binding. This metadata is a reuse guard,
not an authorization token or proof against a compromised local account.

The self-contained installer bootstrap includes the exact standard-library
startup dependency closure and its package initializers. It does not include the Finance
implementation or require third-party packages to import the installer runtime.
The distribution policy pins these delegated source dependencies separately;
they receive no distribution adapter scan exemptions.

This child does not provision the native helper, initialize books or keys,
select real data, grant approvals, change API contracts, or qualify the complete
Finance product. Ordinary first-use provisioning and remaining Finance
acceptance stay under Q26. The existing synthetic in-app contract remains
authoritative for all Finance operations.

## Operator flow

Configure the three explicit repository/helper values documented in the
[in-app workflow](UAA_FINANCE_FIN003_SYNTHETIC_IN_APP_WORKFLOW.md) and, if needed,
`UAA_FINANCE_SAFE_DISABLE`. Launch with `scripts/dev/uaa start` in a clean
developer checkout or `uaa launch` for an installed app. Configuration is
forwarded only to the backend; Vite and OpenWebUI do not receive it.

When a running backend reports changed or unverified Finance configuration,
stop it through its owning launcher and start it again with the intended values.
For developer instances, preserve the original endpoint settings when stopping;
use `scripts/dev/uaa stop` followed by `scripts/dev/uaa start`. For an installed
app, use `uaa stop` followed by `uaa launch`. Refusal preserves the running
process and its ownership metadata. For installed apps, if the recorded process
is still alive but its runtime identity cannot be verified, launch and stop
preserve that ownership record and report the refusal; only a proven-dead process
may be treated as stale. The developer launcher's general stop behavior is unchanged.
A changed environment does not retroactively
disable or reconfigure an already running backend. Legacy instances without the
configuration binding also require this one-time stop/restart.

Opening Finance after startup still requires separate review and confirmation
for sample-book creation and every subsequent mutation. Restarting does not
initialize a book or replay an interrupted save.

## Pre-implementation invariant matrix

| Class | Applicability and evidence |
|---|---|
| Authority and provenance | Applicable: exact four-name backend allowlist, values captured from trusted process configuration, unchanged Core policy/approval/native digest checks; launcher and workspace tests. No wildcard or backend-selector forwarding. |
| Atomicity and recovery | Applicable: configuration identity records the actual environment supplied to the spawned child; refusal does not overwrite ownership metadata or perform recovery. Existing owned stop remains available. |
| Concurrency and generations | Applicable: capture one environment per spawn and bind its metadata to that same capture; running instances with missing or different identity cannot be reused as newly configured instances. Existing ownership checks remain in place; this child does not add serialization of concurrent launches. |
| Tampering and substitution | Applicable: canonical domain-separated digest distinguishes absence from empty values and every configuration key; malformed/missing identity refuses reuse. No runtime identity is inferred from port liveness. |
| Capacity and retention | Applicable: fixed four-key input, fixed-length content-free digest, existing bounded metadata lifecycle. No new journal, raw values, paths, or environment dump. |
| Failure truth | Applicable: readable restart-required refusal, no automatic browser open, restart, stop, or mutation on mismatch; preserve invalid/empty values for Core fail-closed classification. |
| Cross-surface parity | Applicable: developer and packaged backend use the same configuration capture contract; frontend and OpenWebUI receive none of it. CLI and API continue using the existing Finance workspace contract. |

## Qualification

Required evidence includes exact allowlist and empty-value tests, fresh spawn
metadata, matching reuse, missing/changed identity refusal, preserved stopping,
Core configuration/safe-disable tests, static distribution guardrails,
isolated copied-bootstrap execution, delegated dependency tamper rejection,
documentation integrity, final broad qualification, independent exact-head
review, security review, hosted checks, merge proof, and owned cleanup.
The scoped merge and local post-merge checks are recorded above; the managed
setup continuation has its own candidate and qualification gates.

Related contract:
[`FIN-003 synthetic in-app workflow`](UAA_FINANCE_FIN003_SYNTHETIC_IN_APP_WORKFLOW.md).
