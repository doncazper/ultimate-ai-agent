# Task Input Boundary

Status: active M29 contract. Current active baseline: **v0.33.0**.

Task plans may reference safe reviewed refs. They must not carry raw user prompts, raw model output, raw file content, raw transcripts, secrets, credentials, private local paths, or unreviewed payloads.

M29 denies non-authoritative inputs as plan authority:

- model output refs
- memory refs
- context-pack refs
- tool-intent refs
- approval refs
- runtime output refs
- OpenWebUI output refs
- unknown refs

Memory remains recall, not authority. Context packs remain plans, not injection. Tool intents remain validation-only contracts, not execution.

M30-M40 remain planned/provisional.
