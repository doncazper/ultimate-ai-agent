# Durable System Capability Map

Status: implemented read-only Python Core contract and repo-local CLI

The system capability map gives UAA a machine-readable model of its canonical
objects, product surfaces, authority lanes, capability dependencies,
incompatibilities, governance boundaries, and possible compositions. It is the
first durable substrate for answering:

- What is UAA made of?
- Which domain owns each kind of product truth?
- Which surfaces project that truth?
- Which exact capabilities and authority lanes exist?
- What does a capability depend on or conflict with?
- Which capability outputs may structurally feed another capability?
- Which coherent workflows may be latent in the current graph?

The map is not consciousness, an autonomy toggle, a roadmap replacement, or an
authority source. Connectivity never makes an operation callable.

## Canonical inputs

The default builder converges five typed sources:

1. ECO-000 canonical entity ownership and app-surface vocabulary.
2. The existing AuthorityLease lane registry, including domain, capability,
   required trust mode, status, routes, CLI refs, evidence, and unsupported
   adapter posture.
3. Any supplied `CapabilityManifest` records, including dependencies,
   conflicts, input/output modes, risk, side effects, approval, rollback,
   receipt, and evidence posture.
4. `SYSTEM_MAP_CAPABILITY_SOURCE_MODULES`, a canonical census of Python Core
   modules that construct capability manifests.
5. `SYSTEM_MAP_FEATURE_CATALOG`, the typed catalog of first-party product
   features and their relationships to graph nodes.

It does not scrape prose, infer implementation from filenames, import plugins,
load entry points, call a model/provider, fetch the web, or execute a
capability.

## Currentness and merge contract

The map is a merge-maintained architectural index. Future additions enter it
through the source closest to their truth:

- New ECO entity kinds, canonical owners, and app surfaces are automatically
  ingested from their typed enums and ownership registry.
- New AuthorityLease lanes are automatically ingested from the canonical lane
  registry.
- Every Python Core module that constructs a `CapabilityManifest` or
  `DeviceCapabilityManifest` must be listed in
  `SYSTEM_MAP_CAPABILITY_SOURCE_MODULES`.
- Every new first-party product feature must have a truthful, non-authoritative
  entry in `SYSTEM_MAP_FEATURE_CATALOG`. Planned or blocked features stay
  labelled planned or blocked; registration is not an implementation claim.
- Concrete manifests supplied to a build remain fully expanded into
  dependency, conflict, compatibility, governance, and evidence edges.

`scripts/verify_system_map_currentness.py` performs an AST census of manifest
constructor modules, rebuilds the default graph twice at a fixed timestamp,
and proves coverage for every canonical ecosystem node, authority lane,
capability source, and feature declaration. It also pins the merge-queue and
documentation contracts. The verifier is part of the master static scan and
is available directly through `make verify-system-map`.

This makes omission detectable for typed capability declarations and makes
feature registration an explicit merge obligation. It cannot infer that prose
somewhere in the repository is secretly a feature; review still must reject
feature work that avoids the typed catalog.

## Graph vocabulary

Node kinds are `domain`, `entity`, `surface`, `capability`, `route`, `cli`,
`boundary`, and `workflow`. Every node carries a distinct truth status:
`implemented`, `partial`, `declared`, `proposal_only`, `planned`, `blocked`,
`missing`, or `unknown`.

Edges describe `owned_by`, `exposed_by`, `operates_in`, `depends_on`,
`conflicts_with`, `compatible_with`, `governed_by`, `evidenced_by`,
`projects_to`, and `participates_in`. Each edge records whether it is canonical,
declared, or inferred. An inferred compatibility edge means only that a
producer output mode and consumer input mode overlap. Exact schemas, effects,
policy, availability, authority, inputs, and outcome proof still require
separate validation.

Every node, edge, graph, snapshot, and opportunity explicitly grants no
authority. Missing declared dependencies become visible `missing` nodes rather
than disappearing from the map. Dependency cycles, missing edge endpoints,
duplicate definitions, unsafe durable content, noncanonical ordering, and
fingerprint mismatches fail closed.

## Durability model

`SystemMapSnapshotStore` writes:

```text
.uaa/system_map/
  current.json
  snapshots/<snapshot-sha256>.json
```

The graph has a deterministic SHA-256 ref over canonically ordered nodes and
edges. Each snapshot has a separate SHA-256 ref binding its timestamp, graph,
opportunity proposals, and source refs. Saving uses a process/thread lock,
exclusive temporary file, file `fsync`, atomic replace, and directory `fsync`.
The immutable history copy and `current.json` must validate against the same
typed snapshot before inspection succeeds.

The local state directory is gitignored. Durable means crash-safe and
integrity-checked local state; it does not mean remote sync, public evidence,
backup, or production authority.

## Opportunity discovery

The bounded discovery pass emits `SystemMapOpportunity` proposals from two
forms of structural evidence:

- producer/consumer capability pairs with compatible declared I/O modes; and
- authority domains containing multiple complementary exact lanes.

Each proposal is bound to the exact graph ref, names its contributing
capability nodes and supporting edges, records missing authority-ladder or
validation gaps, requires operator review, and grants no authority. A proposal
does not create code, change a roadmap, activate a capability, request
approval, or execute anything.

This is deliberately a conservative first algorithm. Later product semantics
can add typed `consumes`, `produces`, and workflow-intent contracts without
changing the core rule that discovery remains evidence-backed and
proposal-only.

## CLI

Build and durably save the default map:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_system_map.py build
```

Inspect or verify the current snapshot:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_system_map.py inspect
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_system_map.py opportunities
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_system_map.py verify
```

Additional capability manifests may be supplied as one manifest, a list, or a
`{"manifests": [...]}` document:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_system_map.py build \
  --manifest-file capability-manifests.json
```

The CLI does not add an API route or Control Center surface. A future UI must
consume the same Python Core snapshot rather than rebuilding graph truth in
React.

## Current boundaries

- No runtime model or provider calls.
- No web fetch or browser automation.
- No plugin/skill import or execution.
- No connector writes, shell execution, remote execution, or background work.
- No automatic feature implementation or roadmap mutation.
- No approval, lease, policy, availability, or execution inference from a
  graph edge.
- No raw prompt, response, provider payload, local path, log content,
  credential material, or secret-like durable values.
- No production, public beta, or broad-autonomy claim.

## Verification

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_system_map.py
.venv/bin/python scripts/verify_system_map_currentness.py
make verify-system-map
.venv/bin/ruff check src/ultimate_ai_agent/core/system_map \
  src/ultimate_ai_agent/core/capabilities/registry.py \
  scripts/dev/uaa_system_map.py scripts/verify_system_map_currentness.py \
  tests/test_system_map.py
```
