# Mobile Permission Model v1 Consent and Revocation

M100 defines consent and revocation contracts for future mobile permissions.
Consent is not runtime authority in M100.

Consent requirements:

- actor-bound consent refs.
- device-bound consent refs.
- exact permission and scope binding.
- non-transferable consent.
- replay-safe consent.
- renewal requirements.
- explicit revocation model.

Revocation requirements:

- revocation binds to the exact consent ref.
- revocation binds to the same actor, device, and permission ref.
- revocation is modeled as immediate for future runtime use.
- revocation performs no side effects in M100.

The consent and revocation model adds no runtime permission prompts, no native
permission request, no mobile sensor access, no background collection, no push
execution, no backend route, no dependency, and no production authority.

M100 implemented/released this contract-only model. Do not start M101 from the
consent or revocation docs.
