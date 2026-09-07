# Q32 CRM Functional Adoption

Status: implemented candidate for founder-private dogfood. Queue V2 terminal
status still requires protected merge, exact-head and post-merge verification,
and the Queue V2 completion receipt. This is not a public beta, supported
distribution, production-security, or external-CRM claim.

## Outcome

The normal Control Center CRM surface now supports a complete local workflow
with operator-entered private records rather than treating fixtures as product
truth. A founder can create and inspect people, organizations, properties,
relationships, opportunities, activities, and follow-ups; link records; search
and filter; edit; archive or restore; undo; preview a bounded contact CSV
import; and move the workspace between private computers through an encrypted
portable backup.

The Python core owns the durable state and every lifecycle rule. React keeps
only transient presentation state such as the selected record, filters, form
draft, and currently reviewed confirmation. The older CRM M2 diagnostic
cockpit remains available in a collapsed compatibility panel; it is not the
primary Q32 workflow.

## Foundation and persistence boundary

Q32 is the product-adoption successor to the accepted ECO-005 first-class CRM
foundation. The runtime view publishes and verifies
`uaa-eco-005-crm-private-portfolio.v1` as its foundation contract while adding
the bounded path, key, lifecycle, import, backup, recovery, API, CLI, and UI
work that ECO-005 explicitly deferred. It does not silently ingest or relabel
the M0-M2 fixture and JSONL compatibility stores. There is no automatic legacy
migration in this slice.

Private record material is serialized into one versioned CRM state and
encrypted with AES-256-GCM before the atomic local write. The random local key,
encrypted state, and content-free audit log use owner-only filesystem modes.
The key is created without replacing an existing key inode. Invalid keys,
unsafe files, corrupt ciphertext, stale revisions, mismatched previews,
approval substitution, replay substitution, unknown links, and invalid
prospective state all fail closed.

This is a founder-private local key boundary, not a production key-management
claim. The key currently lives beside the encrypted state under an owner-only
local state directory. A machine-account compromise can therefore reach both;
full-disk encryption and normal device security remain necessary. Production
keychain integration, multi-user isolation, hosted sync, and supported binary
distribution remain out of scope.

## Exact local-write flow

Every state-changing operation uses the same bounded sequence:

1. Read the current encrypted state and bind the expected revision.
2. Build a deterministic preview and approval ref over the exact payload.
3. Require a new idempotency ref and explicit operator confirmation.
4. Capture and durably authenticate an exact five-minute
   `LocalApprovalAuthority` grant before the commit request is accepted.
5. Revalidate that pre-existing grant, then issue and evaluate one exact
   Contacts/write `AuthorityLease` constrained to
   the contract, route, action, preview, approval, revision, payload, and
   idempotency refs with an operation budget of one.
6. Validate the complete prospective state, durably stage a content-free audit
   event, atomically replace the encrypted state, then publish and clear the
   staged audit event. Restart recovery publishes only a staged event whose
   receipt is present in the authoritative encrypted state.
7. Return safe approval, lease, decision, rollback, and receipt refs. No raw
   private values are copied to the audit log or receipt.

The lease is revoked if the durable write fails after issuance. Replaying the
same request and idempotency ref returns the existing receipt; changing the
payload under that ref is rejected.

## Import, backup, and recovery

- Contact CSV input is capped at 500 rows and two megabytes. The preview shows
  operator-visible labels and the exact duplicate count; duplicates are
  skipped, never silently merged or overwritten.
- Aggregate encrypted state and portable backup ciphertext are capped at 32
  MiB. A prospective write that would make the state unbackable is rejected
  before replacing the durable file.
- Portable backups use a new random salt and nonce plus scrypt-derived
  AES-256-GCM encryption. The passphrase and local state key are not stored in
  the backup, receipt, or audit log.
- Restore first verifies the ciphertext fingerprint, passphrase, authenticated
  decryption, and full state schema. Commit then requires a fresh exact preview,
  approval, lease, idempotency ref, and operator confirmation.
- A corrupt or unreadable active state disables ordinary edits and keeps the
  verified encrypted-restore path available as the next safe action.
- An approved recovery quarantines a malformed regular local key before
  creating the replacement key; unsafe key file types remain rejected. An
  unreadable pre-restore state is never advertised as an undo target.
- Portable backup is deliberate file handoff, not background synchronization.
  Concurrent edits on multiple computers are not merged; the operator chooses
  which verified backup to restore.

## Operator and inspection surfaces

Control Center routes:

- `GET /control-center/crm/adoption`
- `POST /control-center/crm/adoption/query`
- `POST /control-center/crm/adoption/preview`
- `POST /control-center/crm/adoption/approval`
- `POST /control-center/crm/adoption/commit`
- `POST /control-center/crm/adoption/backup`
- `POST /control-center/crm/adoption/restore-preview`
- `POST /control-center/crm/adoption/restore`

The CLI keeps private values out of terminal output by default:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_crm.py inspect-adoption
```

`--show-private` is an explicit local disclosure switch. Encrypted backup
verification reads its passphrase only from
`UAA_CRM_BACKUP_PASSPHRASE`; the passphrase is not accepted as a command-line
argument.

Private search terms are sent only in the authenticated loopback POST body;
they are not placed in access-log-visible request URLs. The ordinary North Star
`/workspace/crm` navigation mounts this adopted workspace as its primary local
editing entry point.

## Authority and product limits

This slice grants no connector runtime, account sync, external CRM writes,
email or message sends, calendar writes, provider or model calls, browser
automation, background worker, remote execution, public distribution, or
production authority. The API remains authenticated loopback-only. Private
values are returned only to that local authenticated operator surface and are
omitted from durable evidence.

The current portability contract is designed for private UAA instances on the
founder's computers. The implementation is macOS-first under the current
Control Center baseline; it does not claim a separately qualified Windows
host package. Browser clients on another computer are not granted remote
access by Q32.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B \
  scripts/verify_queue_v2_q32_crm_functional_adoption.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest \
  tests/test_crm_adoption.py \
  tests/test_queue_v2_q32_crm_functional_adoption.py
cd apps/control-center && npm test -- --run \
  src/components/CrmAdoptionWorkspace.test.tsx
```

The verifier uses disposable synthetic private values, deletes them with its
temporary directory, and emits only bounded booleans, counts, schema refs, and
authority posture. It proves all seven record kinds, restart and search,
update/archive/undo, duplicate-aware import, encrypted backup handoff, wrong
passphrase rejection, corruption recovery, filesystem modes, exact approval
and lease evidence, CLI safe defaults, and the absence of external writes,
model calls, fixture-primary truth, and public or production claims.
