# Test Corpus Modernization

Status: Phase 01 inventory and retirement/replacement guardrails implemented.

Tracking source: GitHub issue 341.

## Goal

Reduce verification latency and maintenance cost without reducing the defect
classes, safety assertions, exact-head evidence, or operator-visible quality
that the test corpus proves.

The modernization sequence is:

1. deterministic inventory and retirement/replacement guardrails;
2. deterministic fixture foundations;
3. subsystem-by-subsystem setup deduplication with assertion equivalence;
4. slow-test optimization without weaker coverage; and
5. deterministic shard rebalancing after final timing measurement.

Independent subsystem work may be prepared concurrently when fixtures, files,
and contracts do not overlap. Merge admission remains dependency- and
evidence-aware rather than globally one-task-at-a-time.

## Phase 01 Contract

`scripts/verification/test_corpus_guard.py` inventories stable Python test-file
declarations from the shard runner's exact recursive `tests/test_*.py` scope,
including hidden subdirectories, and Control Center `.test`/`.spec` declarations
across the complete default Vitest file scope; Control Center discovery applies
Vitest's `node_modules` and `.git` directory exclusions instead of pytest's
broader generated-environment exclusions,
including inherited pytest class tests, Python parameterization bound to
resolvable decorator syntax, ordered
pre-declaration parameter-data bindings, and in-place mutations visible at
collection time, parameter-data-bound frontend titles, supported runner import
aliases, and extended test APIs. Changes to a parameter set change its stable
declaration ref, so removing a collected case cannot retain the prior inventory
identity.
Identifier-backed frontend parameter sets, including identifiers embedded in
literal arrays or objects, bind to the preceding static `const` initializer or
to a relative import's exported static `const` initializer.
Nested spread and supported collection expressions bind to the same sources.
Supported static frontend registration loops resolve the collected runtime title
and emit one declaration identity per collection item. Identity binds only to
item values read by that title, while source evidence retains the complete item,
so unused-field changes recheck the test without falsely retiring it and unchanged
items survive neighboring-row changes. Runtime-title whitespace and Unicode are
preserved exactly; numeric-title coercion, sparse arrays, asynchronous
registration loops, unresolved helper calls, and mutated aliases fail closed.
Enclosing static suite titles are part of each frontend identity, and
comment-separated or compound unbraced control-flow registrations fail closed.
Python imported parameter data and imported parameter-ID helpers are bound to
the exact referenced declaration and its recursively resolvable local
dependencies. Dynamic parameter-module imports, including calls through assigned
import-function aliases, fail closed. Changes to an
imported initializer or ID helper, including one in
another test module, recheck the dependent test file. Dynamic, mutated,
ambiguous, or unresolved parameter bindings and collection-changing
`conftest.py` hooks, including custom Python item/module/directory collectors,
fail closed. Collection hooks in changed repository plugins
registered through a `conftest.py` `pytest_plugins` binding, including one in a
hidden directory beneath `tests`, also fail closed, and changes to the plugin
registration set itself are collection-configuration changes,
as do parameterized fixtures declared by those registered plugins.
Wildcard imports in tests, class-body parameter bindings,
repository-file/directory-backed local or imported parameter data (including
aliased readers, directory enumeration, and constructed classes), and changes
to pytest collection configuration
in `pyproject.toml`, `pytest.toml`, `.pytest.toml`, `pytest.ini`, `.pytest.ini`,
`tox.ini`, or `setup.cfg` also fail closed; every `tox.ini` change is rejected.
Changes to the canonical pytest shard runner or its command manifest also fail
closed because those files define which Python tests execute.
Python test-class aliases, assigned or imported `unittest.TestCase` aliases
(with dynamic construction, module-attribute writes, or incompatible rebinding
rejected),
collected-class
metaclasses (including inherited local metaclasses), direct or aliased `globals()`
namespace mutation (including assignment-expression aliases), direct module
namespace writes through zero-argument `globals()`, `locals()`, or `vars()`, indirect module
namespace rebinding, module-level `__test__` bindings, imported test functions
or locally resolvable collected test classes, test methods assigned
or declared inside class-body control flow, aliased module-level `pytestmark`
parameterization, and post-definition parameterization calls through aliases
are likewise rejected because their collected identities cannot be represented
safely. Parameterized fixtures, execution-time rebinding of imported pytest
fixture roots or directly imported fixture aliases, and local parameterized-fixture decorator
factories at module or class scope (including expanded option mappings), with
unqualified attribute-based fixture decorators rejected rather than silently
treated as pytest fixtures, dynamic
module/class `pytestmark` mutations through direct, aliased, or chained-assignment
bindings, post-definition `__test__` writes to local classes or their direct or
bounded-unpacking aliases, post-definition `__init__` or `__new__` writes to
local classes or their aliases, and direct, augmented, deleted, conditional, or
indirect function-level `__test__` writes (including through bounded aliases) fail
closed; bounded function aliases participate in static function-level `__test__`
writes (including assignment-expression aliases), deletion of a resolved
function-level `__test__` override restores the declaration, bounded static
falsy function-level values are treated as disabled, incompatible execution-time
rebinding of a recognized `unittest.TestCase` alias, including conditional
constructor targets, indirect `setattr`/`delattr` mutations, imported `unittest`
module aliases, and class-body writes through `globals()`, including from executable
function defaults, annotations, decorators, or class bodies that write a declared
global, fails closed,
class-level parametrizing `pytestmark`, unresolved or bare parametrization
decorators, module-level collection-aborting pytest calls and their assignment
aliases, and changed `pytest_generate_tests` hooks also fail closed. Frontend
registrations inside unresolved function (including one with a bounded TypeScript
return annotation, type predicate, or object-type operator), constrained generic method, or callback
bodies, ordinary or computed instance-field initializers (including fields after
method bodies), relative side-effect imports even when comments separate the
keyword and module or the runtime import uses an empty named clause, conditional
`if`/`switch` suite exits before later registrations, and expression-conditional
registrations and runner aliases fail closed; ordinary, typed,
parenthesized, or nested angle-bracket-asserted test/suite API aliases are rejected,
including bounded nontrivial initializers that retain a recognized runner API
reference rather than invoking it,
and recognized runner APIs also fail closed when shadowed in a local
binding position or by a non-runner import. Parameterized-suite detection uses
the complete resolved runner-alias set. Changes to the Control Center Vitest or
Playwright collection configuration, or to its `package.json` `pretest`, `test`,
or `posttest` lifecycle command, also fail closed.
`scripts/verify_test_corpus_guard.py`
provides the direct inspection command. For a pull request the guard compares
every changed test file with the exact CI comparison base. A removed or renamed
declaration must have one durable entry in
`docs/verification/test_corpus_retirements.json`.
Git rename collapsing is disabled for this comparison, so moving a test file
explicitly retires its old path-bound stable refs even when its declarations
are otherwise unchanged.

Each retirement entry must identify:

- the exact retired test ref;
- one or more replacements that are present in the current corpus;
- a substantive reason;
- a typed assertion-equivalence artifact plus the SHA-256 ref recomputed from
  its canonical JSON; and
- a typed verification-evidence artifact plus the SHA-256 ref recomputed from
  its canonical JSON.

The assertion artifact binds every replacement ref to an independently derived
`test-source-ref:sha256:*` over only that exact inventoried function or frontend
call expression. Unrelated imports, helpers, or neighboring tests do not
invalidate an accepted historical source ref, while changes to the replacement
declaration do; prose cannot stand in for preserved assertion evidence. The
verification artifact has a
bounded field reserved for independently attested exact-head GitHub evidence.
The repository-constructed GitHub transport envelope is explicitly
non-authoritative and is rejected even when its internally reported receipt and
Foundation Gate run are passed. Phase 01 does not add live GitHub fetching, a
credentialed status client, or a new attestation trust root. Until a later
accepted scope provides an independently verifiable immutable GitHub run or
artifact identity, real test retirements therefore fail closed. Schema tests
inject a bounded validator only to exercise the retirement contract; that test
seam does not grant repository verification authority. The nested artifacts
and their enclosing artifacts are
content-bound as `assertion-ref:sha256:*` and `test-result-ref:sha256:*` values;
arbitrary summaries, status strings, or well-shaped hashes are insufficient.
Records accepted
on the exact comparison commit are immutable: later candidates must preserve
the complete typed record field-for-field. If a historical replacement is later
retired, its own new record must preserve the replacement chain and retain at
least one active replacement.
Every newly added retirement record must correspond to a declaration removed
relative to the bound comparison commit. When a local comparison commit is
unavailable, existing multi-hop replacement chains remain valid only when they
terminate at an active test.

Missing or malformed canonical CI base commits, malformed inventories,
duplicate refs, missing replacements, weak reasons, modified historical
records, or unaccounted removals fail closed. Base-to-HEAD, index, worktree,
and untracked test paths are unioned under fixed byte and path-count budgets,
and the exact base commit supplies both the path comparison and prior content.
A local checkout without a comparison ref reports an explicit local-only
unavailable state; hosted verification may not use that fallback. Adding this
guard does not retire any test.
Worktree test files and the retirement ledger are read as bounded,
single-link regular-file identities by walking every repository-relative path
component through pinned no-follow directory descriptors; substitutions,
symlinked parents, or mid-read identity changes fail closed.
Historical source refs are used only when the replacement file or declaration
is absent; unsafe, oversized, mutated, or undecodable worktree content never
falls back to historical evidence.

Retirement reasons are bounded and rejected when repository redaction rules
detect credential-like values, raw prompt/response/log/path markers, local user
paths, usernames, hostnames, serials, or environment dumps. The verifier
envelope applies its own content-free transport validation before acceptance.
The durable result stores only repository code metadata, counts, and hashes.
It does not store raw test output, application payloads, prompts, responses,
credentials, host identity, or local paths.

## Later Phase Rules

- Fixture deduplication must preserve assertion and failure-mode equivalence.
- A surviving, blocked, unknown, or unmeasured mutation prevents retirement.
- Slow-test optimization must compare equivalent cold and warm runs.
- Timeouts and skips are not performance fixes.
- Shard rebalancing happens after behavior-preserving changes and keeps the
  canonical shard/worker budget unless a separately accepted architecture
  change proves a better budget.
- No phase weakens Foundation Gate, OpenAPI, policy, approval, redaction,
  supply-chain, or exact-head checks.

## Authority

This is verification infrastructure only. It grants no model, provider,
network, browser, connector, shell, plugin, production, or release authority.
