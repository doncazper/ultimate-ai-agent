# M96 Plugin Execution Sandbox Receipt Plan

M96 receipt plans store safe refs only. A receipt may include:

- request ref
- plugin ref
- action ref
- sandbox ref
- audit ref
- safe output ref
- reason codes

Receipts store no raw plugin payload, no secret material, no external plugin package, no marketplace payload, no fetched plugin content, no shell output, no network response, no filesystem mutation result, no model provider payload, and no production authority evidence.

The receipt is audit evidence for the built-in test plugin sandbox only. It is not authority for M97 recurring automation.

M97 remains future.
