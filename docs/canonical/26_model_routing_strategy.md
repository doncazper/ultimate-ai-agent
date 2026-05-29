# 26 Model Routing Strategy

Status: Canonical foundation spec, v0.4.5
Owner: Commander / Orchestrator Team
Layer: Foundation service used by Layers 0–6
Related ADR: `docs/decisions/ADR-0025-use-model-routing.md`
Related schemas:
- `docs/schemas/model_capability.schema.json`
- `docs/schemas/model_route.schema.json`
- `docs/schemas/model_routing_policy.schema.json`
- `docs/schemas/model_eval_result.schema.json`

## Purpose

The Ultimate AI Agent should not behave as if it is one model. It should be a model-routed agent system where each task is delegated to the cheapest, fastest, safest, most capable model or runtime that can reliably complete that task.

The Model Router is a foundation service. It allows the agent to use multiple model classes for maximum efficiency, quality, privacy, and resilience.

## Core principle

> Use the cheapest, fastest, safest model that can reliably complete the task, and escalate only when complexity, risk, privacy, uncertainty, or verification requirements justify it.

The Orchestrator decides what must happen. The Model Router decides which model class or runtime should perform each step. The Tool Broker controls actions. The Cost Governor controls spend. The Event Ledger records routing decisions. QA/evals measure whether routing worked.

## Why this is foundational

Model routing must exist before high-volume or high-autonomy modules are built. Scanners, proactive intelligence, skill acquisition, and self-improving code will create many small decisions. Without routing, the system becomes too expensive, too slow, too noisy, and too dependent on a single model.

New foundation rule:

> No high-volume scanners, proactive alerts, skill acquisition, self-improving code, or autopilot workflows until the Model Router, Cost Governor, Event Ledger, privacy routing policy, fallback behavior, and routing evals work.

## Responsibilities

The Model Router is responsible for:

```text
Selecting model classes for tasks
Selecting actual model providers/runtimes from a capability registry
Applying cost, latency, privacy, and risk policies
Escalating difficult or risky tasks to stronger models
Routing sensitive tasks to local/private models where required
Choosing verification models when independent review is needed
Logging routing decisions and results
Triggering fallback on failure, timeout, low confidence, or policy conflict
Recording cost, latency, tokens, and eval outcomes
Learning from evals and feedback over time
```

The Model Router is not responsible for:

```text
Executing external actions
Bypassing the Tool Broker
Changing permissions
Writing memories directly
Mutating files directly
Approving risky actions
Replacing QA/evals
```

## Runtime architecture

```text
User Request
  ↓
Commander / Orchestrator
  ↓
Execution Contract
  ↓
Task Decomposition
  ↓
Model Router
  ↓
Selected Model / Runtime
  ↓
Tool Broker if tools are needed
  ↓
QA / Eval / Verification
  ↓
Event Ledger + Cost Governor + Feedback Store
```

## Model classes

The system should route by model class first, not by fixed vendor/model name. Actual providers can be swapped through the capability registry.

| Model class | Primary use | Default risk level | Notes |
|---|---|---:|---|
| `fast_classifier` | Intent, risk, tags, triage, dedupe, routing | Low | Cheap and fast; should not make major decisions alone. |
| `standard_assistant` | Daily chat, routine summaries, drafts, basic plans | Low/Medium | Default everyday model. |
| `strong_reasoner` | Architecture, complex planning, security review, high-risk judgment | Medium/High | Used selectively because it is more expensive. |
| `coding_model` | Code generation, patching, refactoring, tests, migrations | Medium/High | Must be paired with sandbox execution and review. |
| `research_synthesizer` | Web research, source comparison, docs synthesis, breaking news | Medium/High | Must cite and separate fact from inference. |
| `vision_model` | Screenshots, UI, diagrams, PDFs, charts, images | Medium | Used for multimodal input. |
| `audio_model` | Voice input/output, transcription, meeting audio | Medium | Optional in MVP; needed before voice mode. |
| `embedding_model` | Semantic indexing, memory search, document retrieval | Low | Not used for final reasoning. |
| `reranker` | Memory/document/source ranking | Low | Improves retrieval quality before reasoning. |
| `local_private_model` | Sensitive local notes, offline/private summarization | Medium | Preferred for private data when quality is sufficient. |
| `structured_output_model` | JSON/schema-constrained outputs | Low/Medium | Used for contract generation and extraction. |
| `small_batch_worker` | High-volume scanner triage and repetitive transforms | Low | Must obey batch/cost budgets. |
| `long_context_model` | Large files, long threads, large research packs | Medium | Should be used only when chunking is insufficient. |
| `high_reliability_critical_model` | Critical verification and high-risk decisions | High | May be a strong model, multi-model review, or model-plus-rules path. |

## Routing decision inputs

Every routing decision should consider:

```text
task_type
subtask_type
risk_level
privacy_level
latency_requirement
cost_mode
cost_budget_remaining
context_length
modality
required_output_format
tool_use_required
coding_complexity
source_verification_need
user_preference
project_policy
connected_account_policy
current_model_health
historical_eval_performance
confidence_threshold
fallback_policy
```

## Cost modes

The user or project can set a cost mode:

| Cost mode | Behavior |
|---|---|
| `cheap` | Prefer fast/standard models, limited research, no ensembles unless required. |
| `balanced` | Use stronger models for architecture, security, code review, and high uncertainty. |
| `premium` | Use best available models and deeper verification for quality. |
| `critical` | Use strong model plus independent verification and explicit approval gates. |
| `local_private` | Prefer local/private models; require approval before cloud routing sensitive data. |

## Privacy routing modes

| Privacy level | Default routing behavior |
|---|---|
| `public` | Any approved cloud model may be used. |
| `project_private` | Approved project models only; logs must not leak across projects. |
| `personal_sensitive` | Prefer local/private model; cloud requires explicit policy allowance. |
| `regulated_or_secret` | Local/private or approved secure enclave only; human approval may be required. |
| `unknown` | Treat as sensitive until classified. |

## Routing modes

### 1. Single-model routing

One task goes to one model.

```text
Classify this email → fast_classifier
```

### 2. Pipeline routing

Different stages use different models.

```text
Ingest → classify → retrieve → synthesize → verify → deliver
```

### 3. Escalation routing

Start cheap; escalate only if confidence is low, risk is high, or output fails checks.

```text
fast_classifier → standard_assistant → strong_reasoner
```

### 4. Verification routing

One model produces, another critiques.

```text
coding_model creates patch
strong_reasoner reviews architecture/security
sandbox tests validate behavior
```

### 5. Ensemble routing

Multiple models independently answer or verify. Use only for high-impact, high-uncertainty tasks because it is expensive.

### 6. Local-first routing

Sensitive tasks use a local/private model first. Escalation to cloud requires policy approval.

## Task-to-model matrix

| Task | Primary model class | Verifier |
|---|---|---|
| Intent classification | `fast_classifier` | None unless low confidence |
| Risk classification | `fast_classifier` | `strong_reasoner` for high risk |
| Memory retrieval | `embedding_model` + `reranker` | QA for critical tasks |
| Memory write extraction | `structured_output_model` | Memory Curator / schema validation |
| Daily summaries | `standard_assistant` | Lightweight QA |
| Breaking news | `research_synthesizer` | `strong_reasoner` for interrupt-level alerts |
| Reddit triage | `fast_classifier` / `small_batch_worker` | `standard_assistant` for selected clusters |
| Email triage | `fast_classifier` / `local_private_model` | `standard_assistant` if needed |
| Architecture design | `strong_reasoner` | QA/eval model |
| Code patching | `coding_model` | Tests + `strong_reasoner` |
| Self-improvement patch | `coding_model` | Tests + security + approval |
| File summarization | `standard_assistant` | `strong_reasoner` if sensitive/high-impact |
| UI/image review | `vision_model` | `standard_assistant` |
| External action approval | `strong_reasoner` | Human approval |
| Proactive alert decision | `standard_assistant` | `strong_reasoner` for interrupt-level alerts |
| Structured schema generation | `structured_output_model` | Schema validator |

## Public interfaces

The Orchestrator and specialist agents interact with the Model Router through a stable service contract.

```ts
modelRouter.routeTask(input: RouteTaskInput): Promise<ModelRoute>
modelRouter.executeRoute(route: ModelRoute, payload: ModelPayload): Promise<ModelRunResult>
modelRouter.verifyResult(input: VerifyResultInput): Promise<VerificationRoute>
modelRouter.recordFeedback(input: ModelFeedbackSignal): Promise<void>
modelRouter.getPolicy(projectId?: string, userId?: string): Promise<ModelRoutingPolicy>
modelRouter.listCapabilities(filter?: CapabilityFilter): Promise<ModelCapability[]>
modelRouter.estimateCost(input: RouteTaskInput): Promise<CostEstimate>
modelRouter.replayRoute(routeId: string): Promise<RouteReplayResult>
```

## Required schemas

The following schemas are required before implementation:

```text
model_capability.schema.json
model_route.schema.json
model_routing_policy.schema.json
model_eval_result.schema.json
```

The model capability schema describes which model classes exist, what modalities they support, whether they can use tools, cost bands, privacy limits, structured-output reliability, context limits, known strengths, known weaknesses, and eval performance.

The model route schema records the selected model class, actual provider/model, route reason, policy version, cost estimate, privacy handling, fallback plan, verification plan, and Event Ledger linkage.

The routing policy schema defines cost modes, privacy modes, escalation thresholds, task-to-model defaults, blocked routes, and critical-action verification requirements.

The eval result schema records whether a route was cost-effective, accurate, private, timely, and compliant with risk/approval policies.

## Event Ledger requirements

Every routing decision must be logged as an event sequence:

```text
model_route.requested
model_route.selected
model_route.executed
model_route.fallback_used
model_route.escalated
model_route.verified
model_route.failed
model_route.feedback_recorded
```

Minimum event fields:

```text
run_id
task_id
route_id
policy_version
requested_model_class
selected_model_class
selected_provider_model
reason_for_selection
privacy_level
cost_mode
risk_level
estimated_cost
actual_cost
latency_ms
input_tokens
output_tokens
fallbacks_available
fallback_used
verification_required
verification_route_id
confidence
error_state
eval_result_id
```

## Fallback and escalation policy

Fallback is required when:

```text
selected model unavailable
timeout occurs
schema validation fails
confidence below threshold
safety filter triggers
privacy policy conflict detected
cost budget exceeded
result fails QA/eval gate
```

Escalation is required when:

```text
task risk is high
external action is requested
self-improving code is involved
security/privacy impact exists
breaking-news alert would interrupt the user
model uncertainty remains after first pass
current model output conflicts with canonical files
```

Fallback behavior must be deterministic and policy-driven. The system should not improvise new model choices without logging the reason.

## Critical verification policy

For high-risk tasks, the producing model cannot be the only verifier.

High-risk examples:

```text
self-improving code
external actions
security-sensitive changes
permission changes
financial/destructive/reputational actions
canonical architecture changes
breaking-news interrupt alerts
```

Required verification pattern:

```text
producer model → independent verifier model → deterministic checks/evals → approval gate if required
```

## Cost Governor integration

The Model Router must consult the Cost Governor before using expensive models, long-context models, ensembles, or high-frequency scanner batches.

The Cost Governor may return:

```text
approved
approved_with_warning
requires_user_approval
denied_budget_exceeded
fallback_to_cheaper_model
batch_or_defer
```

## Consent and privacy integration

The Model Router must consult the Consent/Permission Ledger for sensitive data routing.

Examples:

```text
Personal messages may only use local_private_model unless the user opts into cloud processing.
Work emails may use approved cloud models but may not be used for model training.
Project code may use coding_model, but secrets must be redacted before routing.
Regulated or secret data requires explicit policy and possibly human approval.
```

## Capability Registry integration

Every model class and provider-specific model must be registered as a capability.

Capability manifest fields:

```text
model_class
provider
provider_model_id
supported_modalities
supports_tools
supports_structured_output
context_window
cost_band
latency_band
privacy_classification
allowed_data_classes
blocked_data_classes
known_strengths
known_weaknesses
eval_scores
fallbacks
status
```

## Routing algorithm sketch

```text
1. Receive subtask and execution contract.
2. Classify task type, risk, privacy, modality, and output requirements.
3. Load project/user model policy.
4. Ask Cost Governor for budget constraints.
5. Filter model capabilities by modality, privacy, tool needs, context, and policy.
6. Select cheapest model class that meets quality threshold.
7. Attach fallback and verification plan.
8. Log route selection.
9. Execute route.
10. Validate output format and safety constraints.
11. Escalate or fallback if needed.
12. Run verification route when required.
13. Record eval/cost/latency/confidence.
14. Send result to Orchestrator.
```

## Contract tests

Required before the Model Router can pass Foundation Gate:

```text
low-risk classification routes to fast_classifier
architecture review routes to strong_reasoner
code patch routes to coding_model and independent verifier
sensitive personal note routes to local_private_model or requires approval
breaking-news interrupt routes to research_synthesizer plus verifier
external action routes to high_reliability_critical_model plus approval
budget-exceeded route falls back or defers
selected route is logged in Event Ledger
fallback path is logged when primary model fails
privacy-blocked route does not leak payload to disallowed model
```

## Evals

Required eval files:

```text
docs/evals/model_routing_eval.md
docs/evals/model_cost_efficiency_eval.md
docs/evals/model_privacy_routing_eval.md
docs/evals/model_critical_verification_eval.md
```

## Acceptance criteria

Model Routing V1 is accepted when:

```text
Model class registry exists.
Model capability schema exists.
Route schema exists.
Routing policy schema exists.
Eval result schema exists.
At least ten routing contract tests pass.
Routing decisions are logged to the Event Ledger.
Cost Governor is consulted for expensive routes.
Consent Ledger is consulted for sensitive routes.
Fallback behavior is deterministic and logged.
Critical tasks require independent verification.
A task-to-model matrix exists and is used by the Orchestrator.
Foundation Gate includes Model Router V1.
```

## Open questions

```text
Which model providers are approved for MVP?
Which tasks must always use local/private routing?
What is the default monthly budget for scanner-heavy projects?
What is the threshold for multi-model ensemble verification?
Which evaluation scores should update routing policy automatically?
```


## v0.5.3 remediation note

Model routing must respect Secret Broker boundaries, privacy routing, event-level cost attribution, and provider/credential policies. Sensitive data should not be routed to cloud models unless the active policy allows it.
