# Task Input Boundary

Status: active M29 contract. Current active baseline: **v0.33.1**.

Task plans may reference safe reviewed refs. They must not carry raw user prompts, raw model output, raw file content, raw transcripts, secrets, credentials, private local paths, or unreviewed payloads.

M29 denies non-authoritative inputs as plan authority:

- model output refs
- memory refs
- context-pack refs
- tool-intent refs
- approval refs
- runtime output refs
- OpenWebUI output refs
- Control Center preview refs
- unknown refs

Memory remains recall, not authority. Context packs remain plans, not injection. Tool intents remain validation-only contracts, not execution.

The evaluator revalidates current object fields, so model_copy-mutated raw
content flags, secret-like metadata, and authority refs remain denied at the
decision boundary.

M30-M40 remain planned/provisional.
