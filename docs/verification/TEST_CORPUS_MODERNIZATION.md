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
import-function aliases, and module-executed dynamic Python code through `exec`,
`eval`, `compile`, `__import__`, or bounded aliases fail closed. Changes to an
imported initializer or ID helper, including one in
another test module, recheck the dependent test file. Changes to an ancestor
test-package `__init__.py` also recheck every test beneath that package because
package initialization is an implicit collection dependency; a changed
initializer that contains a module-level pytest collection abort in either
revision fails closed. Dynamic, mutated,
ambiguous, or unresolved parameter bindings and collection-changing
`conftest.py` hooks, including custom Python item/module/directory collectors,
fail closed. Collection hooks in changed repository plugins
registered through a `conftest.py` `pytest_plugins` binding or imported directly
under a recognized hook name, including one in a hidden directory beneath
`tests` and the bounded transitive local dependencies of those plugins, also
fail closed, and changes to the plugin
registration set itself are collection-configuration changes,
as do fixtures declared by those registered plugins or imported into a
`conftest.py` from a local module, including imports in module-executed compound
statements. Changes to ordinary, parameterized, or
autouse fixtures in a `conftest.py` or registered plugin, and to their bounded
local dependency closure, fail closed. Module-local autouse fixture source,
transitive helper bindings, imported module-object dependency closures, and
execution posture are bound into every affected test ref. Post-definition fixture
applications also resolve bounded module aliases before classifying their target.
The canonical hosted CI workflow,
local toolchain action, lane wrapper, shard runner, command manifest, directly
loaded pytest plugins, and their bounded transitive local dependency closure are
part of the same fail-closed change boundary. Configuration-
and session-time hooks such as `pytest_addoption`, `pytest_cmdline_parse`,
`pytest_configure`, `pytest_load_initial_conftests`, `pytest_plugin_registered`,
and `pytest_sessionstart` are included in that fail-closed hook boundary.
Wildcard imports in tests, class-body parameter bindings,
repository-file/directory-backed local or imported parameter data (including
aliased readers, directory enumeration, and constructed classes), and changes
to pytest collection configuration
in `pyproject.toml`, `pytest.toml`, `.pytest.toml`, `pytest.ini`, `.pytest.ini`,
`tox.ini`, or `setup.cfg` also fail closed; pytest `pytest11` entry-point
registration changes, development-dependency changes, and `uv.lock` changes are
included, and every `tox.ini` change is rejected.
Changes to the canonical pytest shard runner or its command manifest also fail
closed because those files define which Python tests execute.
Python test-class aliases, assigned or imported `unittest.TestCase` aliases and
bounded aliases of an imported `unittest` module used in class bases (with
dynamic construction, module-attribute writes, or incompatible rebinding
rejected),
collected-class
metaclasses (including inherited local metaclasses), direct or aliased `globals()`
namespace mutation (including assignment-expression aliases), direct module
namespace writes or mutator calls through zero-argument `globals()`, `locals()`, or
`vars()` (while function-local `locals()` and `vars()` remain ordinary local
state), writes through the current `sys.modules[__name__]` module object, indirect module
namespace rebinding, module-level `__test__` bindings, imported test functions
or locally resolvable collected test classes, test methods assigned
or declared inside class-body control flow, aliased module-level `pytestmark`
parameterization, and post-definition parameterization calls through aliases
are likewise rejected because their collected identities cannot be represented
safely. Parameterized fixtures, including parameterized fixture factories
applied after function definition, execution-time rebinding of imported pytest
fixture roots, their `fixture` attributes, or directly imported fixture aliases,
and local parameterized-fixture decorator
factories at module or class scope (including expanded option mappings), with
unqualified attribute-based fixture decorators rejected rather than silently
treated as pytest fixtures, dynamic
module/class `pytestmark` mutations through direct, aliased, or chained-assignment
bindings, post-definition `__test__` writes to local classes or their direct or
bounded-unpacking aliases, post-definition `__init__` or `__new__` writes to
local classes or their aliases, post-definition writes to `test*` class
attributes, and direct, augmented, deleted, conditional, or
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
class-level parameterization through `pytestmark`, rebound or mutated imported
pytest mark aliases, unresolved or bare parameterization
decorators, module-level collection-aborting pytest calls and their assignment
aliases, module-level `unittest.SkipTest` raises and aliases (including imports
from `unittest.case` and imported aliases of that module), class-body unittest
skip state, mutations of pytest
collection classes, and changed
`pytest_generate_tests` hooks also fail closed. Static `skip`, `skipif`, and
`xfail(run=False)` decorators and module/class `pytestmark` forms are bound into
declaration identity, including referenced condition bindings and the effective
order of competing `xfail` marks, so disabling an active test retires its prior
ref instead of silently preserving it. Python fixture argument consumption,
name-bound default posture, imported fixture implementations, and imported
fixture `name=` overrides through direct or aliased pytest decorators are
identity-bound, as are `usefixtures` marks.
Frontend `skip`, `fixme`, `todo`,
`skipIf`, and `runIf` execution posture is collision-bound separately from the
user title; a trivia-free conditional token stream, literal values, and enclosing
suite disable posture are part of every affected child declaration identity for
the same reason.
Parenthesized/conditional/logical runner callees and property-API writes to
global runner bindings fail closed, including `Reflect.defineProperty`. Eager or
otherwise unresolved `import.meta.glob` registration imports, including generic
calls, fail closed. Generic direct runner calls and executable `eval`/`Function`
registration sources, including string-literal computed `globalThis` access,
fail closed. Type-only
runner imports remain allowed inside complete type-alias declarations, including
generic constraints. Descriptor-level pytest collection-class mutations, ordinary
local conftest imports, and post-definition unittest skip writes through direct
attributes, `__dict__`, or `vars()` namespaces and bounded aliases of those
namespaces also fail closed.
Statically non-callable module constants and literal containers may retain
`test*` or `Test*` names because pytest does not collect those values. Frontend
registrations inside unresolved function (including one with a bounded TypeScript
return annotation, type predicate, or object-type operator), constrained generic method, or callback
bodies, ordinary or computed instance-field initializers (including fields after
method bodies and classes with generic object-type heritage), relative
side-effect imports even when comments separate the
keyword and module or the runtime import uses an empty named clause, CommonJS
registration dependencies, invocations
of imported local registration helpers at module or suite scope, conditional
`if`/`switch` suite exits before later registrations, and expression-conditional
registrations and runner aliases fail closed; ordinary, typed,
parenthesized, or nested angle-bracket-asserted test/suite API aliases are rejected,
including bounded nontrivial initializers that retain a recognized runner API
reference rather than invoking it and results of unrecognized runner methods
such as `bind`,
and recognized runner APIs also fail closed when invoked through optional
chaining, invoked indirectly through `call`, `apply`, `bind`, `globalThis`, or a
sequence-expression callee, dynamically imported from a supported runner,
mutated through dot or string-literal computed `globalThis` access, including
computed modifier and parameterizer chains, or
shadowed in a local
binding position or by a non-runner import. Parameterized-suite detection uses
the complete resolved runner-alias set. Changes to any supported
`vite.config.{js,mjs,cjs,ts,mts,cts}` or
`vitest.config.{js,mjs,cjs,ts,mts,cts}` candidate in the Control Center, its
Playwright collection configuration, any transitive local static ESM or CommonJS
dependency (including no-substitution template-literal `require` calls) of those
configuration files, configured Vitest setup files and their
transitive local dependencies, or its `package.json` `pretest`, `test`, or
`posttest` lifecycle command, also fail closed. Changes to the Control Center
frontend dependency manifest or resolved `package-lock.json` or
`npm-shrinkwrap.json` are part of the same fail-closed collection boundary.
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
