# Managed Portable Mission Evidence Signing

Status: implemented in the Python core for exact dispatcher-governed signing
and key lifecycle operations; macOS is the only supported signing platform.

UAA preserves `uaa-portable-mission-evidence-bundle.v1` as the unsigned,
content-free local SHA-256 chain format. A signed export is a separate outer
`uaa-portable-mission-evidence-signed-artifact.v1` wrapper. Existing unsigned
exports and offline verification remain compatible.

The inner unsigned v1 field
`signing_status=blocked_signing_lifecycle_not_implemented` is a frozen
compatibility value describing that unsigned artifact itself. It is not the
current managed-signing lifecycle posture. The separate outer signed wrapper
and `managed_signing` read model carry current signing truth.

## Trust model

The signed wrapper provides an Ed25519 signature over a domain-separated,
canonical attestation bound to the exact unsigned bundle ref and digest, key
ref/version/generation, request ref, receipt ref, and public-key fingerprint.
Offline verification requires a caller-supplied public-key bundle plus a
separately pinned bundle ref and key fingerprint. An artifact does not trust a
public key merely because the key arrived beside it.

The v1 verifier accepts only a key marked `active` in the supplied pinned
bundle. A current bundle that marks the key retired, revoked, or lost fails
closed. To verify evidence after rotation without a public lifecycle
transparency service, the operator must retain and independently pin the
contemporaneous active-key bundle used at signing time.

This proves cryptographic authenticity relative to that pinned key snapshot.
It does not prove signer identity, non-repudiation, current revocation status,
an external timestamp, public notarization, or source-ledger availability.
Evidence never grants execution authority.

## Managed key boundary

The purpose-specific Swift helper uses CryptoKit Ed25519 and stores the raw
32-byte seed only in a non-synchronizing, device-only macOS Keychain generic
password accessible only while the device is unlocked. The helper never returns the seed. Python
receives public keys and signatures only.

macOS Security.framework does not offer Secure Enclave-backed Ed25519 keys.
UAA therefore does not claim Secure Enclave storage or hardware
non-exportability. The helper is explicitly built and installed with:

```bash
make portable-evidence-keychain-helper
```

The helper source and installer are source-checkout tooling and are not shipped
inside the Python wheel. A usable local signing backend therefore requires a
trusted source checkout, a locally built pinned helper, and an unlocked login
Keychain. Helper readiness alone does not prove that a particular key is
accessible; exact key access and fingerprint are probed again inside the
adapter's locked start boundary after dispatcher authority succeeds.

Runtime requests never build or download it. The Python adapter requires a
regular single-link executable owned by the current user, non-writable by group
or others, with an exact installed SHA-256 fingerprint and expected protocol.
At request time Python copies bytes from the already-open, inode- and
hash-verified installed helper into a private mode-0700 temporary directory,
re-verifies the copied hash, executes that isolated copy with a fixed argv,
scrubbed environment, bounded input, one source-bounded protocol response,
post-execution output-size rejection, fixed working directory, and timeout, then
removes it. It never builds, downloads, invokes `/usr/bin/security`,
uses a shell, or trusts a PATH-selected helper.

Both the Python backend and Swift helper reject signing payloads that lack the
exact portable-mission-evidence Ed25519 domain prefix. The direct helper is a
local cryptographic primitive, not an approval or authority surface.

## Authority and lifecycle

Six exact adapters exist in the `evidence_signing` authority domain:

- bundle sign (`execute`);
- key create (`mutate`);
- key rotate (`mutate`);
- key revoke and Keychain deletion (`mutate`);
- key mark-lost (`mutate`);
- key-material cleanup for an exact interrupted rotation, revocation, or loss
  settlement (`mutate`).

Every UAA product signing or lifecycle operation flows through
`AuthorityDispatcher`. Immediately
before start it rechecks the exact adapter/tool/capability binding, current
PolicyEngine decision, exact `LocalApprovalAuthority` validation, active
resource-exact `AuthorityLease`, budget, kill switch, backend readiness,
safe-disable posture, key lifecycle, idempotency, and replay state. An approval
ref alone authorizes nothing. Durable start wins over ambiguous failure;
started-without-terminal replay becomes recovery-required and never reinvokes
the Keychain helper.

Rotation, revocation, and mark-lost append their public transition before
deleting the retired or terminal Keychain item. A deletion failure leaves an
explicit `active_rotation_delete_pending`, `revoked_deletion_pending`, or
`lost_deletion_pending` state that
blocks signing and all unrelated lifecycle changes. Only the exact cleanup
adapter, with a new exact approval and resource-bound lease, may retry the
idempotent delete and append settlement evidence. This also recovers a crash
after Keychain deletion but before its public settlement append.
Mark-lost and revoke deliberately allow an already-absent exact Keychain item;
their idempotent delete then settles the terminal public posture. A locked or
otherwise failing Keychain remains deletion-pending and cannot be mistaken for
settlement.

The public lifecycle ledger is bounded, append-only, hash-chained, fsynced,
single-writer, and hardened against symlink, FIFO, hard-link, mode, size, and
transition substitution. It stores public keys, fingerprints, safe refs,
timestamps, and lifecycle receipts only—never seeds, prompts, results, paths,
logs, environment values, or provider payloads.

## Operator surfaces

- `inspect-authority-mission-completions` shows read-only lifecycle posture.
- `export-portable-evidence-public-key-bundle` exports safe public trust data.
- `verify-authority-mission-evidence` accepts unsigned v1 or a signed artifact;
  signed verification requires explicit pinned trust arguments.
- `GET /api/runtime/authority-missions/completions` exposes the same safe
  lifecycle posture and cannot sign, create, rotate, revoke, approve, or lease.

No mutating CLI, API, or Control Center shortcut is exposed. Integrators must
use the same Python dispatcher contracts; operator shells cannot mint authority.
