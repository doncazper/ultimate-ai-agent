# Hybrid Adaptive Task Decomposer + Capability Registry

The task decomposition subsystem adds a typed, registry-bound planning layer
without replacing the existing milestone planning, execution, tool broker,
approval, or runtime contracts.

It lives under `ultimate_ai_agent.core.task_decomposition` and is designed for
local deterministic orchestration over explicitly registered capabilities.
It does not add backend routes, shell execution, network execution, provider
calls, browser automation, plugin execution, memory writes, context injection,
or production authority.

## Main Contracts

- `CapabilityRoutingCard`: compact discovery metadata used for search and
  ranking.
- `CapabilityContract`: full execution contract with schemas, limitations,
  permissions, side effects, handler metadata, retry, cache, concurrency,
  eval, and healthcheck fields.
- `TaskIntent`: classified request metadata including goal, constraints,
  ambiguity, complexity, risk, expected output, and success criteria.
- `TaskPlan`: typed plan with registry-bound `TaskNode` entries.
- `PlanValidationResult`: fail-fast validation report with reason codes and
  approval requirements.
- `DAGExecutionResult`: deterministic execution summary with per-node records
  and concise observations.

## Register A Capability

```python
from ultimate_ai_agent.core.task_decomposition import (
    CapabilityRegistry,
    build_echo_tool_capability,
)
from ultimate_ai_agent.core.task_decomposition.examples import echo_summary_handler

registry = CapabilityRegistry()
registry.register(build_echo_tool_capability(), echo_summary_handler)
```

Handlers are in-memory adapters supplied by the caller. The registry does not
import arbitrary handler strings or let a planner invent tools. If a plan
references an unregistered capability, validation fails.

For local/dev testing, use `CapabilityRegistryStore` to persist contracts as
JSON:

```python
from ultimate_ai_agent.core.task_decomposition import (
    CapabilityRegistryStore,
    CapabilityRegistryStoreConfig,
)

store = CapabilityRegistryStore(
    CapabilityRegistryStoreConfig(registry_path=".uaa/task_decomposition_registry.json")
)
store.ensure_example_registry()
```

## Decompose And Validate

```python
from ultimate_ai_agent.core.task_decomposition import TaskDecomposer

decomposer = TaskDecomposer(registry)
plan = decomposer.decompose("Summarize this request directly.")
validation = decomposer.validate_plan(plan)

assert validation.valid
```

The decomposer selects among:

- `direct`
- `linear_plan`
- `dag_plan`
- `react_loop`
- `tree_search`
- `skill_reuse`
- `human_in_loop`

Selection is deterministic and based on the classified intent plus the
capabilities returned by the registry.

## Execute A DAG Plan

```python
import asyncio

from ultimate_ai_agent.core.task_decomposition import DAGExecutor

result = asyncio.run(DAGExecutor(registry, parallel=True).execute(plan))
assert result.status == "succeeded"
```

The executor:

- validates the plan before execution,
- topologically schedules nodes,
- can run independent nodes concurrently with `asyncio`,
- respects per-capability concurrency limits,
- validates inputs before each capability call,
- validates outputs after each capability call,
- retries according to each capability contract,
- pauses high-risk or approval-bound nodes as `awaiting_approval`,
- records only concise observations and safe summaries.

## Approval Gates

Capabilities require approval when they are high or critical risk, access
private or secret data, declare dangerous permissions such as write, shell,
network, external API, credential, publish, send, delete, or spend, or set
`requires_approval=True`.

At plan time, risky capability nodes must declare `requires_approval=True` or
depend on a `human_approval` node. At execution time, the call context must
include the approved capability id:

```python
from ultimate_ai_agent.core.task_decomposition import CapabilityCallContext

context = CapabilityCallContext(
    approved_capability_ids=["capability:write-preview"],
)
```

Shell, MCP, handoff, and external API execution modes are represented in the
contract schema but are not implemented by this subsystem. They remain denied
unless a future reviewed milestone adds a safe adapter.

Approval can be validated through the existing `LocalApprovalAuthority` by
binding a capability id to an approval ref:

```python
from ultimate_ai_agent.core.task_decomposition import CapabilityCallContext

context = CapabilityCallContext(
    run_id="task-decomposition-run:local",
    actor_id="local_actor",
    approval_refs={"capability:gated-summary": "appr_..."},
)
```

The approval grant must match the same run id, actor id, capability id,
`invoke_capability` action, risk level, and data classification.

## Local Dev API

The canonical `ultimate_ai_agent.api.app` OpenAPI boundary does not expose
task-decomposition routes. That boundary is path-count gated by historical
milestone tests.

For self-testing, use the standalone local/dev FastAPI app in
`ultimate_ai_agent.core.task_decomposition.dev_api`:

- `GET /task-decomposition/catalog`
- `POST /task-decomposition/examples/init`
- `POST /task-decomposition/capabilities/register`
- `POST /task-decomposition/classify`
- `POST /task-decomposition/decompose`
- `POST /task-decomposition/plans/validate`
- `POST /task-decomposition/approval-request`
- `POST /task-decomposition/plans/execute`
- `POST /task-decomposition/run`

Example:

```bash
PYTHONPATH=src .venv/bin/python -m ultimate_ai_agent.core.task_decomposition.cli \
  --registry .uaa/task_decomposition_registry.json serve-api --port 8765

curl -X POST http://127.0.0.1:8765/task-decomposition/examples/init
curl -X POST http://127.0.0.1:8765/task-decomposition/run \
  -H 'content-type: application/json' \
  -d '{"raw_request":"Summarize this request directly."}'
```

The registry file defaults to `.uaa/task_decomposition_registry.json`. Override
it with `UAA_TASK_DECOMPOSITION_REGISTRY=/path/to/registry.json`.

## Local CLI

The CLI is available without adding a package entry point:

```bash
PYTHONPATH=src .venv/bin/python -m ultimate_ai_agent.core.task_decomposition.cli \
  --registry .uaa/task_decomposition_registry.json init-examples

PYTHONPATH=src .venv/bin/python -m ultimate_ai_agent.core.task_decomposition.cli \
  --registry .uaa/task_decomposition_registry.json run "Summarize this request."
```

For developer-only approval smoke tests, pass `--approve capability:id`. For
exact approval authority validation, pass `--approval-ref capability:id=appr_...`
and `--approval-grant /path/to/grant.json`.

## Kernel Adapter

`TaskDecompositionKernelAdapter` lets kernel-adjacent callers preview or run a
task decomposition flow without changing `MinimumKernelRunner` behavior:

```python
from ultimate_ai_agent.core.task_decomposition.kernel_adapter import (
    TaskDecompositionKernelAdapter,
)

preview = TaskDecompositionKernelAdapter().preview("Summarize this request.")
```

## Learning Hooks

`ReflectionStore` records short structured reflections after failures,
approval pauses, skips, and repairs. Successful repeated plan fragments can be
promoted through an optional caller-supplied hook:

```python
from ultimate_ai_agent.core.task_decomposition import ReflectionStore

promoted = []
store = ReflectionStore(promotion_hook=promoted.append, promotion_threshold=3)
store.record_execution(plan, result)
```

The store keeps only safe summaries, reason codes, plan ids, node ids, and
capability ids.

## Migration Notes

- Existing `core.planning` contracts remain the review-only milestone plan
  evaluator. Use them where legacy no-effect plan review is required.
- Existing `core.execution` contracts remain the no-effect state machine. Use
  `DAGExecutor` only for registry-bound local callable/workflow capabilities.
- Existing `ToolRegistry`, `ToolBroker`, and tool runtime adapters are not
  replaced. `CapabilityRegistry.register_tool_manifest()` can expose legacy
  tool metadata as a capability routing contract, while handler registration
  stays explicit and separate.
- Existing approval authority remains the source of exact-scope approval policy
  for broader framework flows. This subsystem enforces local approval gates
  before invocation and can be adapted to stricter approval authorities by the
  caller.
- The current implementation is ready for local self-testing with safe
  registered Python handlers and workflow handlers. It is not production
  authority and does not enable real shell, browser, network, provider, plugin,
  mobile, or remote execution adapters.
