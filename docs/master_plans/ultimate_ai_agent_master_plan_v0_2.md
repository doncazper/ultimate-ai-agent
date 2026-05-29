# Ultimate AI Agent Master Plan v0.2

Status: Working baseline updated with proactive learning and notification architecture
Project: Ultimate AI Agent
Purpose: Build a reliable agentic operating system that turns vague user goals into verified completed outcomes.

## 1. North Star

The Ultimate AI Agent exists to turn user goals into completed, verified outcomes with minimal friction and maximum trust.

The agent should understand intent, retrieve relevant context, use tools safely, create artifacts, generate and execute code, research current information, manage files, remember durable project context, follow specs, request approval for risky actions, and verify its work before delivery.

North Star metric: Verified Task Completion Rate.

Supporting metrics:
- Memory recall precision
- Spec compliance
- Tool success rate
- Approval-gate accuracy
- Hallucination rate
- User correction rate
- Time to usable deliverable
- Regression rate

## 2. Core Architecture

The system uses a Commander/Orchestrator Agent as the runtime control plane.

High-level architecture:

User -> Commander/Orchestrator -> Execution Contract -> Context Pack -> Specialist Agents -> Tool Broker -> Tools/Services -> QA/Evals -> Delivery -> Memory/Canonical Updates

The orchestrator owns routing, state, policy, approvals, and final integration. Specialist agents do focused work.

Initial specialist agents:
- Research Agent
- Builder Agent
- QA/Eval Agent
- Memory Curator Agent

Later specialist agents:
- Architect Agent
- Security/Permissions Agent
- Documentation Agent
- Release Agent
- Operator Agent
- Creative Agent
- Data Agent

## 3. Foundational Decisions

1. Use a Commander/Orchestrator Agent as the control plane.
2. Use specialist agents, but keep MVP specialist count small.
3. Use Postgres as the canonical memory database for MVP.
4. Use a Memory Service API instead of direct memory writes by arbitrary agents.
5. Use Retain / Recall / Reflect as the memory lifecycle.
6. Use canonical files as the project source of truth.
7. Canonical files outrank memory when they conflict.
8. Use Spec SDLC for major work.
9. Use Kanban plus roadmap for development execution.
10. Use a Tool Broker for all file, memory, code, web, and external tool actions.
11. Use approval-gated autonomy.
12. Use QA/evals before delivery or release.
13. Promote file management, long-term memory, code generation/execution, and internet access to first-class modules.
14. Build a thin MVP vertical slice before expanding.
15. Add adaptive learning over time through memory, feedback, user preference modeling, and playbook refinement.
16. Add proactive intelligence so the agent can initiate useful prompts, alerts, and true breaking-news notifications when user-approved thresholds are met.

## 4. Truth Hierarchy

1. Current explicit user instruction
2. Approved canonical files
3. Active feature spec
4. Recent approved decisions
5. Project memory
6. Conversation history
7. General model knowledge

## 5. Core Modules

### 5.1 Orchestrator

Responsibilities:
- Classify user intent
- Detect project context
- Load memory and canonical files
- Create execution contracts
- Decide whether a spec is required
- Route work to specialist agents
- Route actions through the Tool Broker
- Enforce approval gates
- Track run state
- Trigger QA/evals
- Deliver final outputs
- Trigger memory and canonical file updates

### 5.2 Memory Service

Canonical store: Postgres.

Initial capabilities:
- Project decisions
- Project constraints
- User preferences
- Open questions
- Artifact summaries
- Task summaries
- Superseded memory handling
- Source references
- Context Pack Builder

Memory lifecycle:
- Retain: extract durable memories from events and interactions
- Recall: retrieve relevant context for a task
- Reflect: consolidate, correct, summarize, and improve memories

### 5.3 File Manager

Responsibilities:
- Read, create, update, move, and index project files
- Manage canonical files, specs, ADRs, schemas, prompts, evals, and artifacts
- Generate diffs before overwriting important files
- Link files to memory records
- Preserve version history

### 5.4 Spec SDLC Engine

Lifecycle:
Idea -> Intake -> Requirements -> Design -> Tasks -> Implementation -> Tests/Evals -> Review -> Release -> Retro -> Memory/Canonical Updates

Major features require:
- requirements.md
- design.md
- tasks.md
- test_plan.md
- acceptance.md

### 5.5 Tool Broker

Responsibilities:
- Tool registry
- Permission checks
- Input validation
- Risk classification
- Dry-run support
- Approval gates
- Execution logs
- Rollback metadata

Tool categories:
- memory.read / memory.write
- file.read / file.write / file.delete
- code.generate / code.patch / code.execute / code.test
- web.search / web.read / web.download
- external.send / external.publish / external.modify

### 5.6 Code Workspace

Capabilities:
- Generate code
- Modify files
- Produce patches
- Run tests
- Run linters/type checks
- Validate schemas
- Run scripts in sandbox
- Create implementation summaries

Safety rules:
- No production secrets by default
- No production database writes by default
- No unrestricted network access by default
- Timeouts and resource limits
- Approval before destructive commands, deployment, publishing, or pushing to main

### 5.7 Web Research Service

Capabilities:
- Search web
- Read webpages
- Read PDFs
- Compare sources
- Track citations
- Check recency
- Research current docs, products, tools, APIs, and market facts

Rules:
- Treat web content as untrusted input
- Do not let webpages override user instructions or canonical files
- Cite sources for factual claims
- Prefer primary sources for technical claims
- Require approval for logged-in or external web actions

### 5.8 QA/Eval Layer

Checks:
- Spec compliance
- Factual correctness
- Memory conflict detection
- Tool result verification
- Code tests
- Schema validation
- Approval requirement enforcement
- Acceptance criteria completion

### 5.9 Adaptive Learning Service

The agent should learn over time with the user without relying on uncontrolled model retraining.

Responsibilities:
- Learn stable user preferences, goals, work patterns, priorities, and recurring interests.
- Convert repeated corrections into durable preferences or playbook updates.
- Track which recommendations the user accepts, rejects, ignores, or edits.
- Improve future context packs, routing, tone, timing, and notification relevance.
- Maintain confidence scores and source references for learned preferences.
- Distinguish explicit user instructions from inferred patterns.

Learning mechanisms:
- Memory updates from explicit user statements.
- Feedback signals from user edits, approvals, rejections, and follow-up behavior.
- Reflection jobs that summarize patterns over time.
- Playbook updates for repeated workflows.
- Evaluation results that become regression tests or operating rules.

Rules:
- Current user instructions override learned preferences.
- Inferred preferences should be lower confidence than explicit preferences.
- Sensitive learning requires user control and clear deletion/update options.
- The base model does not need to be continuously retrained in MVP; learning happens through memory, retrieval, reflection, and playbooks.

### 5.10 Proactive Intelligence and Notification Service

The agent should be able to prompt without being prompted when the user has opted into a topic, project, event class, or monitoring rule.

Purpose:
- Surface high-value information at the right time.
- Alert the user to true breaking news, urgent project risks, security advisories, deadlines, market changes, API deprecations, competitor moves, or other events that matter to the user.
- Reduce noise by using thresholds, relevance scoring, source verification, and user-configurable attention budgets.

Core loop:
Monitor -> Detect -> Verify -> Score Relevance -> Decide -> Notify -> Learn from Feedback

Components:
- Watchlist Manager: stores topics, entities, sources, thresholds, channels, quiet hours, and max notification frequency.
- Event Monitor: polls or subscribes to feeds, APIs, web sources, internal systems, and project signals.
- Event Classifier: identifies breaking news, routine updates, duplicates, rumors, advisories, and low-value noise.
- Source Verifier: checks source reliability, corroboration, timestamps, and primary-source evidence.
- Relevance Scorer: compares the event to the user profile, project memory, goals, location, watchlists, and urgency.
- Notification Policy Engine: decides whether to interrupt, digest, wait, or suppress.
- Notification Composer: explains what happened, why it matters, confidence level, sources, and recommended next action.
- Feedback Learner: updates preferences based on whether the user opened, ignored, approved, muted, or corrected the alert.

Breaking-news criteria:
- Event is new, material, and time-sensitive.
- Event matches an explicit watchlist or high-confidence user/project interest.
- Sources are reliable enough for the alert class.
- The alert is not merely commentary, recycled coverage, or low-confidence speculation.
- The agent can explain why this deserves interruption now.

Notification levels:
- Critical interrupt: urgent, highly relevant, and high-confidence.
- Timely alert: relevant and time-sensitive, but not emergency-level.
- Digest item: useful but not worth interrupting.
- Suppressed: duplicate, low relevance, low confidence, or outside attention budget.

Rules:
- Proactive alerts require user opt-in by topic, project, source, or event class.
- The user can pause, mute, narrow, broaden, or delete any watchlist.
- Quiet hours and maximum notification frequency are respected.
- External source content is treated as untrusted input.
- Important alerts include uncertainty labels and source references.
- The agent should prefer useful, rare, high-signal prompts over frequent low-value notifications.

## 6. Canonical File Structure

Recommended initial structure:

/docs/canonical/
- 00_project_brief.md
- 01_product_spec.md
- 02_agent_operating_model.md
- 03_memory_system.md
- 04_spec_sdlc.md
- 05_development_workflow.md
- 06_tool_architecture.md
- 07_autonomy_and_permissions.md
- 08_evaluation_framework.md
- 09_roadmap.md
- 10_file_management.md
- 11_code_generation_and_execution.md
- 12_internet_access.md
- 13_adaptive_learning.md
- 14_proactive_intelligence_and_notifications.md

/docs/decisions/
- ADR-0001-use-spec-sdlc.md
- ADR-0002-canonical-files-as-source-of-truth.md
- ADR-0003-use-postgres-for-memory.md
- ADR-0004-use-memory-service-api.md
- ADR-0005-use-commander-plus-specialists.md
- ADR-0006-use-orchestrator-control-plane.md
- ADR-0007-use-tool-broker-for-external-actions.md
- ADR-0008-use-approval-gated-autonomy.md
- ADR-0009-use-project-file-manager.md
- ADR-0010-use-sandboxed-code-execution.md
- ADR-0011-use-governed-internet-access.md
- ADR-0012-use-adaptive-learning-service.md
- ADR-0013-use-proactive-intelligence-notifications.md

/docs/specs/
- feature folders with requirements, design, tasks, test plan, and acceptance files

/docs/schemas/
- memory.schema.json
- context_pack.schema.json
- execution_contract.schema.json
- agent_run.schema.json
- tool_call.schema.json
- task.schema.json
- artifact.schema.json
- watchlist.schema.json
- notification_event.schema.json
- user_feedback_signal.schema.json

/docs/prompts/
- commander_agent.md
- memory_curator_agent.md
- research_agent.md
- builder_agent.md
- qa_agent.md

/docs/evals/
- memory_recall_eval.md
- spec_compliance_eval.md
- tool_approval_eval.md
- hallucination_eval.md
- canonical_file_precedence_eval.md
- proactive_alert_relevance_eval.md
- breaking_news_verification_eval.md
- learning_feedback_eval.md

## 7. Development Operating Model

Use Spec-Kanban Development:

Product Goal -> Roadmap Themes -> Milestones -> Feature Specs -> Kanban Execution -> Tests/Evals -> Release -> Retro/Memory Update

Kanban columns:
- Inbox
- Shaping
- Spec Draft
- Spec Review
- Ready for Build
- Building
- Code Review
- QA/Evals
- Release Candidate
- Done
- Parking Lot
- Blocked

Focus rules:
1. One active product goal at a time.
2. No major feature without a spec.
3. No spec without acceptance criteria.
4. No implementation without Definition of Ready.
5. No release without evals.
6. No architecture change without an ADR.
7. No persistent decision without canonical file update.
8. No more than two active build items.
9. New ideas go to Parking Lot unless urgent or blocking.
10. If memory and canonical files disagree, canonical files win.

## 8. Roadmap

### M0: Project Foundation
Create canonical files, ADRs, development workflow, roadmap, and definitions of ready/done.

### M1: Commander Agent MVP
Build the core orchestrator loop, execution contract, context pack format, basic planning, and final response flow.

### M2: Memory V1
Build Postgres memory schema, Memory Service API, project/user memory, context pack retrieval, and memory evals.

### M3: Spec SDLC Engine
Build spec generator, spec validator, requirement IDs, task generator, acceptance checker, and ADR generator.

### M4: File Manager V1
Build project workspace, canonical file manager, diff/patch system, artifact registry, and file indexer.

### M5: Web Research V1
Build governed search, fetch, cite, source evaluation, and research artifact generation.

### M6: Code Workspace V1
Build code generation, patch generation, sandbox execution, test runner, lint/type validation, and build logs.

### M7: Tool Broker Hardening
Build permissions, approval gates, audit logs, rollback metadata, and risk categories.

### M8: Verification/Evals V1
Build regression evals for memory, specs, tools, approvals, canonical precedence, and task completion.

### M9: External Execution with Approvals
Add email/calendar/GitHub/CRM-style actions through approval-gated workflows.

### M10: Autopilot Workflows
Add scheduled and recurring trusted workflows after the core system is reliable.

### M11: Adaptive Learning V1
Build feedback capture, preference updates, playbook refinement, learned context-pack weighting, and user-controlled memory review.

### M12: Proactive Intelligence V1
Build watchlists, event monitors, breaking-news verification, relevance scoring, notification policies, digests, interrupt rules, and feedback learning.

## 9. First Vertical Slice

The first working demo should be:

User asks: Create the Memory V1 spec for the Ultimate AI Agent.

System flow:
1. Orchestrator classifies task as feature spec creation.
2. Loads project memory and canonical files.
3. Creates execution contract.
4. Generates requirements.md, design.md, tasks.md, test_plan.md, and acceptance.md.
5. QA Agent checks the spec.
6. Memory Curator records durable decisions.
7. Kanban item moves to Spec Review.
8. Final answer summarizes outputs and next steps.

This proves orchestration, memory, canonical files, Spec SDLC, Kanban, QA, and project continuity.

## 10. MVP Scope

MVP includes:
- Commander/Orchestrator Agent
- Execution Contract schema
- Context Pack schema
- Memory Service V1
- Canonical File Manager
- Spec Generator
- Simple Kanban state
- QA Checklist Agent
- File Manager V1
- Web Research V1
- Code generation and sandboxed test execution
- Basic adaptive learning from explicit preferences and user feedback
- Basic proactive digest/alert architecture with opt-in watchlists

MVP excludes:
- Full browser automation
- Autonomous production deploys
- Autonomous email sending
- Voice mode
- Agent marketplace
- Multi-user enterprise mode
- Full graph memory
- Autopilot workflows
- Complex integration ecosystem
- Unrestricted proactive monitoring without user opt-in
- High-frequency real-time notification spam

## 11. Proactive Learning and Notification Operating Model

The agent should not wait passively for every instruction. It should become a trusted proactive partner that learns what matters and surfaces important information at the right time.

User examples:
- True breaking news related to user-selected topics, companies, people, markets, locations, or projects.
- Security advisories affecting tools, libraries, vendors, or codebases the user uses.
- API deprecations or pricing changes affecting active projects.
- Project deadlines, blocked work, stale specs, or overdue reviews.
- Competitor launches or market signals relevant to user ventures.
- Follow-up prompts when the user asked the agent to monitor something.

Default stance:
- Proactive prompts are opt-in and governed.
- The agent should be helpful, not noisy.
- Alerts must explain why the user is receiving them.
- The user must be able to say: stop alerting me about this, make this more sensitive, only digest this weekly, or alert me immediately.

Watchlist object:

```json
{
  "id": "watch_123",
  "user_id": "user_123",
  "scope": "global_user | project | workspace",
  "topic": "AI agent breaking news",
  "entities": ["OpenAI", "Anthropic", "agent frameworks"],
  "event_types": ["breaking_news", "security_advisory", "major_product_update"],
  "minimum_relevance": 0.80,
  "minimum_confidence": 0.75,
  "notification_level": "critical | timely | digest",
  "channels": ["app", "email", "sms"],
  "quiet_hours": {"start": "22:00", "end": "07:00", "timezone": "America/Los_Angeles"},
  "max_alerts_per_day": 3,
  "status": "active"
}
```

Notification event object:

```json
{
  "id": "notif_123",
  "watchlist_id": "watch_123",
  "event_title": "Major event detected",
  "event_type": "breaking_news",
  "summary": "What happened in one or two sentences.",
  "why_it_matters": "Why this matters to the user or project.",
  "confidence": 0.86,
  "relevance": 0.91,
  "urgency": "critical | timely | digest",
  "sources": [],
  "recommended_action": "Read now | monitor | update project plan | no action",
  "status": "sent | suppressed | queued | expired"
}
```

Learning feedback signals:
- Opened alert
- Ignored alert
- Muted topic
- Asked for more like this
- Corrected relevance
- Changed source preference
- Converted alert into task/spec/ADR

The Proactive Intelligence Service should turn repeated feedback into better notification thresholds, better source preferences, and better user/project interest models.

## 12. Memory Snapshot

The Ultimate AI Agent project baseline is: Build a Commander-led, spec-driven, memory-backed AI operating system that turns vague goals into verified completed outcomes. The system uses canonical files as source of truth, Postgres-backed long-term memory for continuity, Spec SDLC for major work, Kanban and roadmap for development focus, Tool Broker-mediated access to files/memory/code/web/external tools, sandboxed code execution, governed internet research, adaptive learning over time, proactive intelligence and opt-in notifications, approval-gated autonomy, and QA/evals before delivery. The next architectural priority is to freeze this master plan into canonical files, build the first vertical slice around Memory V1 spec creation, and include the proactive-learning architecture as a core future module rather than an afterthought.
