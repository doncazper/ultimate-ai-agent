# FIN-003 Managed Synthetic Finance Setup

Status: implemented candidate for the separately admitted
`dev-task:finance-fin003-managed-setup`; review, hosted qualification and merge
remain pending. FIN-003 and Q26 remain incomplete.

## Operator contract

The Python Core can enroll one immutable native-helper profile for the current
account. The repository and installed CLIs share inspection, preparation,
refresh and separate confirmation. Preparation and inspection are read-only.
Confirmation checks current policy, an exact local approval and an active
Finance setup lease before writing the private profile and helper. Enrollment
does not execute the helper, create a Finance book, create its encryption key,
or access Keychain. Approval signing material may be created and is reported
separately in the result.

The managed location comes from the operating system account directory, not
`HOME`, an installation-root override or a bundle-supplied path. An installed
source is captured only from the current verified app and its fixed helper,
with signature and file-identity checks surrounding the capture. A developer
source is a fixed artifact built from the two known Swift sources. Neither
source grants publisher identity or real-data authority. The build uses local
Swift tooling; setup does not compile, download, fetch or choose arbitrary
executables.

## Commands

For an installed app containing the helper, use:

```bash
uaa finance-setup inspect
uaa finance-setup prepare --operation enroll \
  --request-ref request-ref:finance:setup:first \
  --idempotency-ref idempotency-ref:finance:setup:first
```

For a developer checkout, build the fixed artifact first, then use the same
Core through the repository CLI:

```bash
PYTHONPATH=src .venv/bin/python scripts/macos/build_finance_helper.py --architecture arm64
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_finance.py setup-inspect
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_finance.py setup-prepare \
  --helper-source developer-artifact --operation enroll \
  --request-ref request-ref:finance:setup:first \
  --idempotency-ref idempotency-ref:finance:setup:first
```

Select the architecture of the target machine. Preparation prints a bounded,
content-free JSON envelope for CLI transport. Retain it as an owner-only regular
file with mode `0600`, inspect its exact operation and profile refs, then run
`uaa finance-setup run --bundle PATH --confirmed`. The developer equivalent is
`setup-run --helper-source developer-artifact --bundle PATH --confirmed` with
the same Python invocation above. `refresh --bundle PATH` (or `setup-refresh`)
re-presents the same intent and does not confirm it.

After enrollment, explicitly stop and restart the backend through its owning
launcher. Developer instances use `scripts/dev/uaa stop` then
`scripts/dev/uaa start`, preserving their original endpoint settings; installed
instances use `uaa stop` then `uaa launch`. A running backend keeps its captured
configuration. Enrollment therefore cannot silently reconfigure a process or
make an unconfigured instance reusable. In the Finance workspace, sample-book
creation and every later mutation still need their own preview and confirmation.

Any of the three explicit Finance repository/helper settings selects explicit
configuration and requires all three to be valid; a partial or invalid override
never falls back to the managed profile. `UAA_FINANCE_SAFE_DISABLE` remains
independent, including its fail-closed empty value. Launchers generate the
startup mode from one discovery, bind the actual child environment into reuse
metadata, and send it only to the backend. The backend consumes that snapshot
without rediscovering a newly enrolled profile. Unmarked direct CLI operations
discover current configuration normally.

## Recovery and limits

Inspection distinguishes missing, unconfigured, present, incomplete and invalid
state. An interrupted enrollment retains its exact intent. Refresh and separately
confirm that same preparation to retry, or prepare `discard_incomplete` with new
request and idempotency refs and separately confirm its bounded cleanup. Discard
removes only artifacts whose recorded ownership still matches; unknown or
substituted files are preserved and rejected. An active profile cannot be
replaced or discarded through this lane.

An exact committed replay verifies the enrolled helper and returns its original
receipt without revisiting the original source or issuing new authority. An
abandoned replay needs valid retained history but does not require the discarded
helper. A historical result cannot authorize a new operation. Changed intent,
stale state, expired/revoked authority, unsafe filesystem state and insufficient
capacity fail closed.

| Invariant | Implementation boundary |
|---|---|
| Authority | Exact `finance/FIN-003/managed-setup` capability, policy, approval and active lease; current validation under the setup, authority and approval lock order. |
| Filesystem | Retained descriptors, owner/private permissions, no-follow checks, bounded reads, ACL checks and repeated name-to-inode validation; one verified setup lock. |
| Atomicity | Durable pending intent precedes staged helper promotion and the terminal profile/receipt; exact owned retry or separately confirmed cleanup. |
| Provenance | Final helper bytes, fixed build metadata or signed app boundary, inventory and version refs bind the profile; no source path becomes authority. |
| Capacity | State at most 128 KiB, 16 terminal receipts and one active or pending profile; reserve room for commit and maximum discard before admitting pending work. |
| Serialization | One closed profile codec; strict UTF-8, duplicate-key, finite-value, depth, reference and hash validation. Preparation files are bounded private regular files. |
| Parity | One Core service, installed CLI and repository CLI; no new API route or Control Center setup control. |
| Bootstrap | Exact standard-library dependency closure and independent source/AST pins; no Finance or third-party import graph for ordinary installer startup. |

This slice does not qualify signed installed runtime behavior, Windows,
cross-machine portability, real inputs, active profile rotation, automatic
restart, FIN-000 human acceptance or the complete Finance product. Local helper
build/signature checks and synthetic fixtures establish only their stated
boundaries. Full qualification additionally requires focused tests, adversarial
review, static guardrails, actual owned launcher/process checks, exact-head
hosted checks, merge proof and scoped cleanup.

Related: [normal startup](UAA_FINANCE_FIN003_NORMAL_STARTUP.md),
[synthetic in-app workflow](UAA_FINANCE_FIN003_SYNTHETIC_IN_APP_WORKFLOW.md).
