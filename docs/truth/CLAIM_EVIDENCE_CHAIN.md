# Claim Evidence Chain

Status: Active for v0.29.1 / M25.

An M25 evidence chain links claim refs, evidence refs, source refs, event refs,
receipt refs, memory refs, conflict refs, stale refs, and revocation refs.

Refs must be structured. Arbitrary strings are not authority. Claims cannot
self-verify by citing the claim ref as its own source or evidence.
Unrecognized source ref prefixes are treated as unknown and denied for
verification-success statuses. Explicit `TruthSourceKind.unknown` evidence is
also denied.

Evidence chains contain safe summaries and refs only. They do not contain raw
prompt text, raw model output, raw file content, raw transcripts, secrets,
credentials, private keys, or unredacted sensitive content.
