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
