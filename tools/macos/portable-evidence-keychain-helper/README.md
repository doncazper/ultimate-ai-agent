# UAA Portable Evidence Keychain Helper

This purpose-specific macOS helper creates and uses Ed25519 keys stored as
non-synchronizing, device-only Keychain generic-password items that are
accessible only while the device is unlocked. The helper exchanges bounded JSON over
standard input and output and never returns the private key seed.
Signing rejects payloads outside UAA's exact portable-mission-evidence Ed25519
domain; the helper is not a general-purpose signing interface.

It does **not** claim Secure Enclave Ed25519 support, non-exportability from the
Keychain implementation, signer identity, notarization, non-repudiation, or an
external timestamp. UAA must invoke an explicitly installed binary only after
checking its regular-file posture, ownership, permissions, protocol, and pinned
SHA-256 fingerprint. Runtime signing never builds or downloads this helper.

This source and its installer are available from a trusted UAA source checkout;
they are not included in the Python wheel. Installation is restricted to the
fixed per-user UAA helper directory, refuses symlinked or unmanaged existing
installs, and pins the installed executable fingerprint in safe metadata.

Build locally:

```bash
swift build --package-path tools/macos/portable-evidence-keychain-helper -c release
```

The built binary is local output and must not be committed.
