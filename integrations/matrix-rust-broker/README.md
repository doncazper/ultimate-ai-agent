# UAA Matrix Rust Broker

This macOS-first broker is the native Matrix execution boundary for the exact
human-commanded Messenger lanes. It pins `matrix-sdk` 0.18.0 and Rust 1.93.0,
uses the SDK's encrypted SQLite store, and keeps Matrix sessions and store keys
in explicitly non-synchronizing standard macOS login-Keychain items. Their
availability follows the Keychain lock boundary. This CLI helper intentionally
does not select the entitlement-only Data Protection Keychain; an app-bundled
broker may graduate to that store in a separately signed packaging milestone.

The broker is not standing authority. Python Core starts it for one exact
request, supplies a random authentication key over an inherited anonymous file
descriptor, and connects to the random loopback port printed in the bounded
readiness record. The request and response are HMAC-authenticated. The broker
accepts one request, enforces a singleton store lock and a content-free replay
ledger, then exits. Credentials, Matrix session JSON, message bodies, raw Matrix
identifiers, and local paths are never written to broker logs or receipts.

The broker only accepts loopback homeservers in this milestone. A later scoped
milestone must explicitly graduate any remote target.

Build and test with:

```bash
PATH=/opt/homebrew/opt/rustup/bin:$PATH cargo +1.93.0 build --locked --release \
  --manifest-path integrations/matrix-rust-broker/Cargo.toml
PATH=/opt/homebrew/opt/rustup/bin:$PATH cargo +1.93.0 test --locked \
  --manifest-path integrations/matrix-rust-broker/Cargo.toml
```
