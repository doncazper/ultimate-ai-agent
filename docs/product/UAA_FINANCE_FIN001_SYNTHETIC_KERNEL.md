# FIN-001 Synthetic Protected-Book Kernel

Status: implemented source candidate for the exact synthetic-only slice. Merge
and Queue V2 completion evidence remain required. No real-data or supported
deployment claim is made.

## What Works

- Strict `Book`, `LegalEntity`, `FinancialAccount`, `JournalEntry`, `Posting`,
  and snapshot contracts reject unknown fields and unbalanced commodities.
- The canonical manifest contains one deterministic allowlisted fixture with
  opening-balance, transfer, split, adjustment, reversal, and suspense flows.
- The repository builds SQLite in memory and persists only AES-GCM ciphertext,
  safe-ref metadata, and content-free receipts. It includes schema version 1,
  integrity checks, optimistic revision checks, exact replay/conflict handling,
  encrypted backup/restore, generation-safe restore, and cryptographic delete.
- Local mutation requires current `PolicyEngine` allowance, an exact
  `LocalApprovalAuthority` grant, and an active exact session AuthorityLease.
  All three are revalidated at the final persistence boundary. Safe-disable,
  kill switch, missing/revoked approval, missing/coarse/expired lease, stale
  revision, key loss, and ciphertext drift fail closed.
- `scripts/dev/uaa_finance.py` supplies status, prepare, run, inspect, check,
  and redacted export parity. `run` requires explicit operator confirmation,
  records backend approval for the exact lease, and calls the same Python core.

## Protected Storage Boundary

The macOS backend reuses the repository's hash-pinned native protected-cache
helper. That helper stores a random 256-bit key in a non-synchronizing,
ThisDeviceOnly Keychain item and performs authenticated encryption without
returning key material. Finance uses distinct content-derived handles and
Finance-specific AAD, preventing substitution with the Matrix cache lane. The
helper executable is owner-only, fingerprint-pinned, copied to a private
temporary executable before invocation, bounded, and receives a sanitized
environment. The in-memory backend exists only for deterministic tests.

No plaintext SQLite file, key, financial value, raw local path, or record body
is written to metadata, receipts, CLI output, or logs. CLI path arguments are
converted to content-derived safe refs before authority binding.

## CLI Flow

Build and fingerprint the existing native helper according to
`tools/macos/matrix-protected-cache-helper/README.md`, then use its absolute
path and SHA-256 with the commands below. The prepared JSON is a safe-ref-only
review envelope and performs no mutation.

```bash
.venv/bin/python scripts/dev/uaa_finance.py prepare \
  --repository-dir "$UAA_FINANCE_REPOSITORY_DIR" \
  --helper-path "$UAA_FINANCE_HELPER_PATH" \
  --helper-sha256 <64-lowercase-hex> \
  --operation create --expected-revision 0 \
  --request-ref request-ref:finance:local-create \
  --idempotency-ref idempotency-ref:finance:local-create > prepared.json

.venv/bin/python scripts/dev/uaa_finance.py run \
  --repository-dir "$UAA_FINANCE_REPOSITORY_DIR" \
  --helper-path "$UAA_FINANCE_HELPER_PATH" \
  --helper-sha256 <64-lowercase-hex> \
  --bundle prepared.json --confirmed
```

Set the task-specific variables to owner-only local paths. They are runtime
inputs, not defaults or durable evidence. Do not commit prepared bundles or
local repository state.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_fin001_synthetic_kernel.py
.venv/bin/python scripts/verify_fin001_synthetic_kernel.py
.venv/bin/ruff check src/ultimate_ai_agent/core/finance scripts/dev/uaa_finance.py tests/test_fin001_synthetic_kernel.py
```

## Explicitly Still Blocked

Real financial data, arbitrary financial values, import/OCR, files or
statements, bank/account connectors, accountant access, tax/compliance advice
or filing, payments/transfers, provider/model/browser runtime, background sync,
API/UI mutation surfaces, public release, supported binary distribution, and
production authority remain later independently reviewed promotions.
