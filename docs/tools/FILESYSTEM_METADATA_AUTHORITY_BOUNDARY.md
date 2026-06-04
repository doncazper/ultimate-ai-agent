# Filesystem Metadata Authority Boundary

Status: active M32 documentation.
Current active baseline: **v0.37.0**

M32 filesystem metadata lookup is not production authority and is not
authorization for broader filesystem access.

The following refs cannot authorize filesystem metadata access or execution:

- approval refs.
- `approval_test_*` refs.
- task plans.
- execution state refs.
- tool intents.
- context packs.
- memory refs.
- model output.
- runtime output.
- OpenWebUI output.
- Control Center preview refs.

Truth/evidence refs may explain why metadata is being inspected, but they do
not authorize file content reads, directory listing, mutation, or arbitrary tool
execution.

The tool remains governed by the Tool Runtime Adapter, static verifier, and
Foundation Gate. It adds no backend execute route and no Control Center execute
control.
