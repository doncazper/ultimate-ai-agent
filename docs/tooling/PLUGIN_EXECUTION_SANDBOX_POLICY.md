# M96 Plugin Execution Sandbox Policy

The M96 policy is disabled by default and allows only the built-in test plugin sandbox path. Policy validation requires:

- built-in test plugin only
- sandbox required
- manifest permission checks
- audit receipt
- revocation
- deterministic output
- safe refs only
- evaluator boundaries revalidate safety-critical fields

The policy denies external plugin loading, marketplace plugin use, arbitrary plugin code, runtime import, networked plugin fetch, plugin secret access, raw plugin payload, shell execution, network access, browser automation, filesystem mutation, model provider call, memory write, context injection, backend route, Control Center control, dependency, and production authority.

M97 remains future.
