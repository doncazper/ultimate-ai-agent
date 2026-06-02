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
