# UAA Prompt Module Compiler

Status: implemented local build/inspection boundary; runtime activation remains
blocked

## Purpose

UAA now has a Python Agent Core compiler for repository-owned prompt and skill
instruction modules. It replaces hand-maintained concatenation with a typed,
deterministic dependency graph while preserving UAA's local-first and
fail-closed authority boundaries.

This is a build and inspection capability. It does not call a model, import or
execute a skill, inject context into a live run, open a pull request, or grant
execution authority.

## Implemented Contract

`PromptModuleManifest` defines:

- one or more explicit entry modules
- typed module roles: `system`, `developer`, `skill`, or `context`
- stability tiers
- repository-relative source refs
- dependency edges
- strict string, integer, and boolean variables
- bounded string variable lengths and reserved control-token rejection
- bounded descriptor-anchored manifest/module reads and compiled-output byte budgets

The compiler validates the entire declared graph and fails closed on:

- missing entry modules or dependencies
- direct or transitive cycles
- duplicate ids, entries, dependencies, or required variables
- undeclared, missing, mistyped, or disallowed variables
- invalid or nested template control syntax
- absolute, traversing, missing, out-of-repository, symlink, non-regular, or
  path-substituted manifest/source paths
- non-UTF-8 source material
- manifest, module, render-expansion, or compiled-output budget exhaustion

Repository schema gates use `PromptModuleManifestSchemaValidator`. It applies
Draft 2020-12 plus the declared `x-uaa-uniqueBy` rule for module ids; generic
JSON Schema validators cover the portable constraints but cannot express
property-level array uniqueness by themselves.

Every declared module source is read through the bounded repository path
guards so a parked source cannot hide a missing, oversized, symlinked, or
otherwise unsafe path. Only the transitive dependency closure of the selected
entry modules is rendered into the compiled artifact. Unselected modules do
not contribute prompt text and do not require their variables. Dependencies
are emitted before dependents using stable lexical tie-breaking, so identical
inputs produce identical output and receipts.

## Template Grammar

The template surface is deliberately non-executable:

```text
{{ variable_name }}

{% if boolean_variable %}
included when true
{% else %}
included when false
{% endif %}
```

Nested conditionals, loops, macros, expressions, attribute access, function
calls, environment reads, and arbitrary code are unsupported. Variable values
must be provided explicitly through the CLI or Python contract and must match
their declarations.

## Safe Receipts And Drift

Each compilation returns a transient artifact plus a deterministic receipt.
The receipt contains:

- bundle and entry refs
- normalized manifest contract hash
- dependency-first module order
- per-module source refs, sizes, and SHA-256 hashes
- a full declared-source contract hash, including parked modules
- dependency-graph and variable-contract hashes
- supplied variable names, never values
- compiled artifact hash and byte count
- explicit false authority flags

Receipts contain no raw prompt text or variable values. A reviewed golden
receipt can therefore detect source, graph, ordering, variable-contract, or
compiled-artifact drift without persisting prompt bodies as evidence.

The UAA runtime capability foundation prompt pack is the first dogfooded
bundle:

- `docs/prompts/uaa_runtime_capability_foundation/prompt_module_manifest.json`
- `docs/prompts/uaa_runtime_capability_foundation/prompt_module_golden_receipt.json`

Its existing verifier now compiles the graph and compares the result with the
golden receipt. The existing shell wrapper atomically emits and passes that
exact verified compiler artifact to Codex from an in-memory handoff, without
reopening the review copy, so the same Python Core contract backs direct CLI
use and the pack-specific operator path.

## CLI

Inspect the selected closure and full reverse-dependency map:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_prompt_compiler.py inspect \
  --manifest docs/prompts/uaa_runtime_capability_foundation/prompt_module_manifest.json
```

Inspect the blast radius of a changed module:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_prompt_compiler.py inspect \
  --manifest docs/prompts/uaa_runtime_capability_foundation/prompt_module_manifest.json \
  --changed phase-05
```

Compile and check the reviewed receipt:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_prompt_compiler.py compile \
  --manifest docs/prompts/uaa_runtime_capability_foundation/prompt_module_manifest.json \
  --check-receipt docs/prompts/uaa_runtime_capability_foundation/prompt_module_golden_receipt.json \
  --output <output-path>
```

The CLI prints only safe metadata and hashes. Compiled prompt text is written
only when an operator explicitly supplies `--output`.

## Relationship To Existing UAA Graphs

UAA's task decomposition and durable mission orchestration already use
execution dependency graphs. The prompt compiler adds the missing
composition-time graph for instruction modules. It does not replace task DAGs,
the capability registry, `PolicyEngine`, `LocalApprovalAuthority`, route
classification, or the Foundation Gate.

The reverse-dependency inspection result is intended for focused tests and
review scope. It is not authority to modify affected modules automatically.

## Explicitly Blocked

- runtime model or provider calls
- automatic skill discovery, loading, activation, import, or execution
- hidden prompt or context injection
- prompt cache writes
- raw prompt, variable, response, or provider-payload persistence in receipts
- automatic improvement implementation
- automatic branch, commit, push, pull request, or merge
- connector writes, browser automation, and unrestricted shell execution
- public distribution or production authority

Self-learning may later create a safe improvement candidate that names module
refs and graph impact. Any patch or pull-request lane still requires a separate
accepted, approval-bound implementation milestone with exact scope, rollback,
redaction, idempotency, and review evidence.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/test_prompt_module_compiler.py \
  tests/test_uaa_runtime_capability_foundation_prompt_pack.py -q
.venv/bin/ruff check \
  src/ultimate_ai_agent/core/prompt_compiler \
  scripts/dev/uaa_prompt_compiler.py \
  scripts/verify_uaa_runtime_capability_foundation_prompt_pack.py \
  tests/test_prompt_module_compiler.py \
  tests/test_uaa_runtime_capability_foundation_prompt_pack.py
PYTHONPATH=src .venv/bin/python \
  scripts/verify_uaa_runtime_capability_foundation_prompt_pack.py --json
```
