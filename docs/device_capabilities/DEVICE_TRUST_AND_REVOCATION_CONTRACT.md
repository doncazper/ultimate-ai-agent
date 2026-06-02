# Device Trust And Revocation Contract

Status: M20 contract-only trust planning.

Future device trust requires a pairing or trust handshake contract before
runtime use. M20 adds no device pairing runtime and no trust handshake runtime.

Future trust contracts must declare pairing requirement, revocation requirement,
session scope, local approval requirement, receipt requirement, safe summary,
and metadata refs.

Device trust changes must be receipt-backed. Device revocation must be
supported before any future capability can be considered active. Revocation must
not depend on a device client being the agent brain. Device clients are not the
agent brain and are not approval authority.

M20 adds no signing, provisioning, keychain, keystore, App Store, Play Store,
native build workflow, background service, or OS permission integration.

## v0.24.1 M20 Hardening Note

v0.24.1 keeps trust and revocation contract-only. Device pairing runtime is
future. Device identity runtime is future. Revocation plans remain
contract-only, receipt-backed, and non-authoritative. A device trust plan
cannot make a device client the agent brain, cannot approve actions, cannot
execute actions, and cannot bypass Approval Authority, Consent Ledger, Tool
Broker, Event Ledger, Secret Broker, Redaction, or Foundation Gate. M21 remains
planned/provisional.
