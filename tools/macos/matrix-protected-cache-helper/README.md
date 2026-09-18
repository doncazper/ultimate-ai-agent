# UAA Matrix Protected Cache Helper

This macOS-only helper owns random AES-256-GCM cache keys in the device-local
Keychain and performs bounded encrypt/decrypt operations without returning key
material. Python Core invokes a hash-bound installed copy only after exact
request-scoped authority evaluation. Plaintext is transient process memory; the
helper creates no files, logs, database, WAL, journal, temporary query material,
or backup.

It does not grant connector reads, writes, message sends, room mutation,
browser, Memory, or production authority. Cache key lifecycle mutations remain
separate exact approval- and AuthorityLease-governed lanes.

Build locally with:

```bash
swift build --package-path tools/macos/matrix-protected-cache-helper -c release
```

For the FIN003 synthetic Finance managed-setup lane, build the fixed,
source-bound developer artifact explicitly from the repository root:

```bash
PYTHONPATH=src .venv/bin/python scripts/macos/build_finance_helper.py
```

This recipe compiles an owned fresh source copy, strips local debug symbols,
ad-hoc signs and verifies it, then records the final executable digest with the
current two Swift source digests and builder digest. The ignored output is
`.uaa-artifacts/<arm64|x86_64>/helper` plus `helper-manifest-v1.json` under this
package. The normal SwiftPM `.build` cache is not a managed setup artifact.
Changed source, builder, output, architecture or manifest requires a fresh build.
The pinned, dependency-free Package.swift recipe must be reviewed if changed.

The release builder stages a fresh helper at
`Contents/Helpers/uaa-matrix-protected-cache-helper` before nested app signing,
then inventories the final signed bytes. Managed setup separately verifies the
source and requires exact confirmation to enroll a private copy; build output
and ad-hoc signing confer no publisher verification, source attestation,
Finance book/key creation, Keychain mutation or runtime execution authority.
