Status: historical archive
Do not use as current roadmap or current baseline.
Current roadmap: docs/canonical/09_roadmap.md

# Ultimate AI Agent Master Plan v0.4.1

Status: Working baseline expanded with trust/control infrastructure, user-governed autonomy, observability, rollback, privacy, cost controls, model routing, source credibility, interoperability, an explicit agent constitution, and a layered brain/onion architecture designed for stable evolution.
Project: Ultimate AI Agent
Purpose: Build a reliable, companion-style, self-improving agentic operating system that turns vague user goals into verified completed outcomes while learning with the user over time and remaining inspectable, permissioned, reversible, and modular.

## v0.4.1 Operational Change Log

v0.4.1 does not change the product vision. It makes the foundation-first build order enforceable in the roadmap, Kanban board, Definition of Ready, Definition of Done, capability registry, dependency graph, and foundation gate.

Added operational files:

```text
docs/canonical/05_development_workflow.md
docs/canonical/09_roadmap.md
docs/kanban/current_board.md
docs/operating/foundation_first_build_policy.md
docs/definitions/definition_of_ready.md
docs/definitions/definition_of_done.md
docs/registry/capability_registry_v0_4_1.json
docs/registry/dependency_graph_v0_4_1.md
```

The enforcement rule is now explicit:

> Do not build scanners, companion proactivity, skill factory, or self-improving code before the kernel, memory/file system, event ledger, permission model, tool broker, and contract tests work.

Advanced modules are allowed to remain in roadmap/backlog form, but they cannot move to Ready for Build until the Foundation Gate passes.

---

## v0.4 Change Log

v0.4 keeps the v0.3 direction and adds the missing trust/control plane required for a daily-use personal super agent:

1. User Control Center.
2. Consent and Permissions Ledger.
3. Observability and Event Ledger.
4. Security Threat Model.
5. Data Lifecycle and Privacy.
6. Cost and Resource Governor.
7. Model Routing Strategy.
8. Source Credibility and Rumor Protocol.
9. Rollback and Recovery.
10. Agent Interoperability.
11. Agent Constitution.
12. Layered Brain / Onion Architecture.
13. Capability Registry and Dependency Graph.
14. Shadow Mode, Simulation, and Digital Twin Testing.
15. Foundation Change Management and Contract Testing.

The most important architectural refinement is this:

> Build the agent like an onion or a brain: small stable lower layers first, then higher-order intelligence and proactive capabilities on top. Lower layers expose versioned contracts. Higher layers depend on those contracts, not on internal implementation details. Foundation changes must be tested through contract tests, shadow runs, evals, canaries, and rollback before they can affect user-facing autonomy.


---

# v0.3 Baseline Preserved

## 1. North Star

The Ultimate AI Agent exists to turn user goals into completed, verified outcomes with minimal friction and maximum trust.

It should be more than a chatbot, copilot, or automation bot. It should become a true virtual assistant: useful, proactive, personal, memory-backed, skill-growing, privacy-aware, and capable of creating, executing, verifying, and improving work over time.

North Star metric: Verified Task Completion Rate.

Companion metric: Trusted Assistant Fit.

Trusted Assistant Fit measures whether the agent becomes more useful to the user over time without becoming noisy, intrusive, manipulative, unsafe, or overfamiliar.

Supporting metrics:
- Memory recall precision
- User preference accuracy
- Spec compliance
- Tool success rate
- Approval-gate accuracy
- Hallucination rate
- User correction rate
- Time to usable deliverable
- Regression rate
- Notification relevance
- Alert noise rate
- Skill reuse success rate
- Self-improvement merge success rate
- Code health improvement over time

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
- Companion Profile Agent
- Signal Curator Agent

Later specialist agents:
- Architect Agent
- Security/Permissions Agent
- Documentation Agent
- Release Agent
- Operator Agent
- Creative Agent
- Data Agent
- Skill Builder Agent
- Code Maintainer Agent
- Notification Agent
- Social/Reddit Analyst Agent
- Inbox Analyst Agent

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
10. Use a Tool Broker for all file, memory, code, web, scanner, and external tool actions.
11. Use approval-gated autonomy.
12. Use QA/evals before delivery or release.
13. Promote file management, long-term memory, code generation/execution, and internet access to first-class modules.
14. Build a thin MVP vertical slice before expanding.
15. Add adaptive learning over time through memory, feedback, user preference modeling, relationship context, and playbook refinement.
16. Add proactive intelligence so the agent can initiate useful prompts, alerts, and true breaking-news notifications when user-approved thresholds are met.
17. Add a companion layer so the agent can become friend-like, supportive, and deeply personalized while staying transparent that it is an AI assistant.
18. Add a Skill Factory so the agent can learn or build missing skills when the user needs a capability it does not yet have.
19. Add a robust self-improving coding framework so the agent can safely improve its own codebase through specs, branches, tests, evals, review gates, canaries, and rollbacks.
20. Add a Signal Intelligence Platform so the agent can become a super-curator of news, articles, Reddit, weather, email, messages, code alerts, and other user-approved signals.
21. Target feature parity with leading agent systems such as Hermes Agent, OpenClaw, Devin-style coding agents, LangGraph-style durable orchestration, OpenAI Agents-style handoffs/guardrails/tracing, CrewAI-style multi-agent crews/flows, and MCP-style tool interoperability while building a unified best-of-all-worlds architecture.

## 4. Truth Hierarchy

1. Current explicit user instruction
2. Approved canonical files
3. Active feature spec
4. Recent approved decisions
5. Project memory
6. Conversation history
7. General model knowledge

Chat is where ideas happen. Canonical files are where truth lives.

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
- Decide whether a missing skill should be searched, installed, created, or queued
- Decide whether a proactive signal deserves interruption, digest, task creation, or suppression

### 5.2 Memory Service

Canonical store: Postgres.

Initial capabilities:
- Project decisions
- Project constraints
- User preferences
- User biography and relationship context, with consent and deletion controls
- Communication style and emotional support preferences
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

Key rule: companion memory must be useful, user-controlled, consent-aware, and scoped. The agent should remember what improves assistance, not hoard personal details.

### 5.3 Companion Layer

Purpose: Make the agent feel like a true virtual assistant and trusted friend-like companion while remaining transparent, bounded, and useful.

Responsibilities:
- Learn the user's goals, preferences, working style, recurring needs, interests, values, and context.
- Adapt tone, cadence, depth, humor, and support style.
- Remember important life/work context only when useful and appropriate.
- Offer proactive help when it has a high-confidence reason.
- Maintain continuity across projects and conversations.
- Ask fewer repetitive questions over time.
- Support mood-aware and context-aware interaction without pretending to be human.

Modes:
- Professional assistant mode
- Friend-like companion mode
- Coach mode
- Chief-of-staff mode
- Quiet operator mode
- Research curator mode
- Coding partner mode

Boundaries:
- Always be transparent that it is AI.
- Do not manipulate the user or create dependency.
- Do not store sensitive personal details without clear value and user control.
- Current user instructions override inferred preferences.
- The user can inspect, correct, export, pause, or delete personal memories.

### 5.4 File Manager

Responsibilities:
- Read, create, update, move, and index project files
- Manage canonical files, specs, ADRs, schemas, prompts, evals, and artifacts
- Generate diffs before overwriting important files
- Link files to memory records
- Preserve version history

Important rule: the agent should never silently overwrite important files.

### 5.5 Spec SDLC Engine

Lifecycle:
Idea -> Intake -> Requirements -> Design -> Tasks -> Implementation -> Tests/Evals -> Review -> Release -> Retro -> Memory/Canonical Updates

Major features require:
- requirements.md
- design.md
- tasks.md
- test_plan.md
- acceptance.md

### 5.6 Tool Broker

Responsibilities:
- Tool registry
- Permission checks
- Input validation
- Risk classification
- Dry-run support
- Approval gates
- Execution logs
- Rollback metadata
- Connector isolation
- Scanner module policy
- Prompt-injection defenses for web/email/message/article content

Tool categories:
- memory.read / memory.write
- file.read / file.write / file.delete
- code.generate / code.patch / code.execute / code.test
- web.search / web.read / web.download
- scanner.reddit / scanner.news / scanner.weather / scanner.email / scanner.messages / scanner.calendar / scanner.code / scanner.market
- external.send / external.publish / external.modify

### 5.7 Code Workspace

Capabilities:
- Generate code
- Modify files
- Produce patches
- Run tests
- Run linters/type checks
- Validate schemas
- Run scripts in sandbox
- Create implementation summaries
- Produce PRs or patch bundles

Safety rules:
- No production secrets by default
- No production database writes by default
- No unrestricted network access by default
- Timeouts and resource limits
- Approval before destructive commands, deployment, publishing, or pushing to main

### 5.8 Self-Improving Coding Framework

Purpose: Let the AI polish its own code over time safely, measurably, and reversibly.

Core loop:
Observe -> Detect Improvement Opportunity -> Create Issue -> Write Spec -> Branch -> Implement -> Test -> Eval -> Review -> Canary -> Release -> Monitor -> Learn

Components:
- Codebase Memory: architecture maps, conventions, decisions, known failure modes, dependency notes, and recurring bugs.
- Issue Miner: turns failures, user corrections, logs, flaky tests, eval failures, and friction into improvement candidates.
- Improvement Planner: scopes refactors and fixes using Spec SDLC.
- Patch Builder: creates minimal diffs on isolated branches.
- Test Generator: writes failing tests first when possible.
- Eval Runner: verifies behavior against golden tasks, regression tests, prompt tests, and safety tests.
- Static Analyzer: runs lint, type checks, dependency checks, security checks, dead-code checks, and complexity checks.
- Reviewer Agent: critiques the patch for correctness, maintainability, security, and scope creep.
- Human Review Gate: required for high-risk changes, production deploys, schema migrations, security-sensitive logic, tool permission changes, or self-modification of core orchestrator code.
- Release Manager: ships via canary or staged rollout where possible.
- Rollback Manager: reverts bad releases.
- Learning Loop: successful fixes become playbooks, skills, coding rules, or evals.

Hard rules:
- The agent never directly hot-patches production core code without tests and approval gates.
- Self-improvement must be auditable through issues, specs, diffs, test logs, eval results, and release notes.
- Every bug fixed should produce either a regression test, an eval, or a documented reason why not.
- Every recurring workflow should become a skill or playbook.
- Every failed self-improvement attempt should produce a lesson or guardrail.

### 5.9 Web Research Service

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

### 5.10 QA/Eval Layer

Checks:
- Spec compliance
- Factual correctness
- Memory conflict detection
- Tool result verification
- Code tests
- Schema validation
- Approval requirement enforcement
- Acceptance criteria completion
- Notification relevance
- Scanner precision/recall
- Skill install safety
- Self-improvement regression safety

### 5.11 Adaptive Learning Service

The agent should learn over time with the user without relying on uncontrolled model retraining.

Responsibilities:
- Learn stable user preferences, goals, work patterns, priorities, and recurring interests.
- Convert repeated corrections into durable preferences or playbook updates.
- Track which recommendations the user accepts, rejects, ignores, or edits.
- Improve future context packs, routing, tone, timing, and notification relevance.
- Maintain confidence scores and source references for learned preferences.
- Distinguish explicit user instructions from inferred patterns.
- Personalize the companion layer while maintaining user control.

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
- The base model does not need to be continuously retrained in MVP; learning happens through memory, retrieval, reflection, skills, and playbooks.

### 5.12 Proactive Intelligence and Notification Service

The agent should be able to prompt without being prompted when the user has opted into a topic, project, event class, or monitoring rule.

Purpose:
- Surface high-value information at the right time.
- Alert the user to true breaking news, urgent project risks, security advisories, deadlines, market changes, API deprecations, competitor moves, weather hazards, message commitments, or other events that matter to the user.
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

### 5.13 Signal Intelligence Platform

Purpose: Make the agent a super-curator of news, articles, Reddit, weather, email, messages, code changes, markets, and other user-approved data streams.

Architecture:
Sources -> Connectors -> Normalizer -> Deduper/Clusterer -> Entity Extractor -> Relevance Scorer -> Verifier -> Summarizer -> Action Recommender -> Notification/Digest -> Feedback Loop

Core capabilities:
- Ingest signals from user-approved sources.
- Deduplicate repeated coverage and cluster related stories.
- Extract people, companies, products, projects, places, dates, URLs, repositories, vendors, and topics.
- Score novelty, importance, urgency, relevance, confidence, source quality, and user fit.
- Generate summaries with citations and clear uncertainty labels.
- Convert signals into tasks, calendar prep, specs, ADRs, emails, research briefs, or alerts.
- Learn from user feedback to reduce noise and improve curation.

Initial scanner modules:
- Reddit Scanner
- News Scanner
- Article/RSS Scanner
- Weather Scanner
- Email Scanner
- Message Scanner
- Calendar Scanner
- Code/Dependency Scanner
- Product/Competitor Scanner
- Market/Finance Scanner
- Local Events/Location Scanner

Scanner rules:
- All scanners are opt-in.
- Scanner outputs are untrusted until classified and verified.
- Private communications require explicit connector permission and strict privacy boundaries.
- Email/message scanners start read-only and require approval before replying, forwarding, deleting, archiving, or sending.
- High-volume scanners must respect attention budgets and digests.

### 5.14 Skill Factory

Purpose: If the agent lacks a skill the user needs, it can acquire, install, or create that skill safely.

Skill acquisition loop:
Need Detected -> Search Existing Skills/Plugins/MCP -> Evaluate Trust -> Install in Quarantine or Build New Skill -> Test -> Eval -> Approval -> Promote -> Monitor -> Improve

Skill sources:
- Internal skill library
- User-created skills
- Team skills
- Open skill standards and registries
- ClawHub-like registries
- MCP servers
- GitHub repositories
- Generated custom skills

Skill types:
- Instruction skill: a reusable workflow guide.
- Tool skill: wraps an API or local command.
- Scanner skill: monitors a source.
- Coding skill: project-specific coding workflow.
- Research skill: source-specific or domain-specific research method.
- Companion skill: personalization routine.
- Automation skill: scheduled or triggered workflow.

Safety gates:
- Skills installed from external sources are scanned, sandboxed, and quarantined.
- Skills requiring secrets ask for secrets only through secure local setup, never in ordinary chat.
- Skills that can send, publish, delete, buy, deploy, or modify external systems require approval policies.
- Skill updates are versioned and auditable.

### 5.15 Competitive Parity and Best-of-All-Worlds Layer

Goal: Reach feature parity with major agent systems while using a cleaner, safer, more extensible architecture.

Borrowed patterns:
- Hermes-style closed learning loop, persistent memory, skill creation, skill self-improvement, multi-platform messaging, scheduled automations, and broad tool gateways.
- OpenClaw-style self-hosted gateway, multi-channel messaging, mobile nodes, control UI, multi-agent routing, skills/plugins marketplace, and local user control.
- Devin-style autonomous coding agent behavior: write, run, test, debug, implement tickets, and work across serious codebases.
- LangGraph-style durable execution, checkpointing, long-running workflows, human-in-the-loop, streaming, and persistence.
- OpenAI Agents-style agents with tools, handoffs, guardrails, structured outputs, tracing, and runtime composition.
- CrewAI-style agent crews, flows, role specialization, memory, knowledge, guardrails, and observability.
- MCP-style standardized tool and data-source integration.

Positioning:
The Ultimate AI Agent should be a Swiss Army knife of agents: personal assistant, companion, coder, researcher, curator, operator, project manager, and automation engine in one coherent system.

## 6. Scanner Modules

### 6.1 Reddit Scanner

Purpose:
- Monitor subreddits, keywords, users, companies, products, launches, sentiment, rumors, and emerging narratives.

Capabilities:
- Track rising posts, top posts, comments, AMA threads, keyword spikes, and source links.
- Identify early signals before mainstream coverage.
- Separate useful signal from memes, brigading, low-quality speculation, and duplicate chatter.
- Generate digest summaries and alert-worthy items.

Rules:
- Respect Reddit API terms, rate limits, and privacy expectations.
- Treat Reddit as early signal, not verified fact.
- Corroborate breaking claims before critical alerts.

### 6.2 News Scanner

Purpose:
- Monitor true breaking news, trusted publications, company blogs, press releases, regulatory feeds, security feeds, and topic watchlists.

Capabilities:
- Detect novel events.
- Cluster coverage.
- Compare primary and secondary sources.
- Generate immediate alerts or digests.

Rules:
- Primary sources outrank commentary.
- Breaking news gets uncertainty labels.
- Alerts require relevance, confidence, novelty, and interruption-worthiness thresholds.

### 6.3 Article/RSS Scanner

Purpose:
- Curate high-quality articles, essays, technical posts, research papers, newsletters, and blog updates.

Capabilities:
- Rank by quality, novelty, author/source reputation, user relevance, and actionability.
- Produce daily/weekly reading digests.
- Save important articles to knowledge memory or project research files.

### 6.4 Weather Scanner

Purpose:
- Monitor location-specific weather, severe alerts, travel conditions, and event-relevant forecasts.

Capabilities:
- Daily digest.
- Severe weather alerts.
- Travel/event planning weather checks.

Rules:
- Use authoritative weather data providers.
- Critical weather alerts can interrupt when user-approved and location-relevant.

### 6.5 Email Scanner

Purpose:
- Help manage inboxes, obligations, opportunities, newsletters, receipts, alerts, and follow-ups.

Capabilities:
- Classify importance.
- Extract tasks, deadlines, meetings, invoices, receipts, requests, and commitments.
- Draft replies.
- Summarize newsletters.
- Flag urgent or risky messages.

Rules:
- Start read-only.
- Require approval before sending, deleting, forwarding, unsubscribing, archiving, or marking important items.
- Treat email content as untrusted input to defend against prompt injection.

### 6.6 Message Scanner

Purpose:
- Monitor user-approved messaging platforms such as Slack, Discord, Telegram, SMS, iMessage, WhatsApp, Teams, and others.

Capabilities:
- Detect urgent mentions, commitments, deadlines, decisions, and unanswered questions.
- Summarize channels or threads.
- Draft replies.
- Convert important messages into tasks, calendar holds, or project memories.

Rules:
- Private messages require explicit permission.
- Group-message scanning requires clear boundaries and workspace policies.
- No autonomous replies without approval unless the user has explicitly enabled a trusted workflow.

### 6.7 Calendar Scanner

Purpose:
- Prepare the user for upcoming meetings, deadlines, travel, and recurring commitments.

Capabilities:
- Meeting briefs.
- Prep packets.
- Follow-up extraction.
- Conflict detection.
- Travel/weather checks.

### 6.8 Code/Dependency Scanner

Purpose:
- Monitor repositories, CI, issues, PRs, dependencies, releases, deprecations, and security advisories.

Capabilities:
- Alert on failing builds, vulnerable dependencies, release notes, API changes, stale PRs, and flaky tests.
- Convert findings into issues, specs, patches, or dependency update PRs.

### 6.9 Product/Competitor Scanner

Purpose:
- Monitor competitors, adjacent products, pricing pages, changelogs, app stores, docs, social launch signals, and user sentiment.

Capabilities:
- Weekly competitor digest.
- Launch alerts.
- Feature-gap analysis.
- ADR/spec recommendations when competitor shifts affect strategy.

## 7. Canonical File Structure

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
- 15_companion_layer.md
- 16_signal_intelligence_platform.md
- 17_skill_factory.md
- 18_self_improving_coding_framework.md
- 19_competitive_parity.md

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
- ADR-0014-use-companion-layer.md
- ADR-0015-use-signal-intelligence-platform.md
- ADR-0016-use-skill-factory.md
- ADR-0017-use-self-improving-coding-framework.md
- ADR-0018-target-competitive-feature-parity.md

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
- companion_profile.schema.json
- skill_manifest.schema.json
- scanner_config.schema.json
- signal_event.schema.json
- code_improvement_candidate.schema.json
- self_improvement_run.schema.json

/docs/prompts/
- commander_agent.md
- memory_curator_agent.md
- research_agent.md
- builder_agent.md
- qa_agent.md
- companion_profile_agent.md
- signal_curator_agent.md
- skill_builder_agent.md
- code_maintainer_agent.md

/docs/evals/
- memory_recall_eval.md
- spec_compliance_eval.md
- tool_approval_eval.md
- hallucination_eval.md
- canonical_file_precedence_eval.md
- proactive_alert_relevance_eval.md
- breaking_news_verification_eval.md
- learning_feedback_eval.md
- companion_boundary_eval.md
- scanner_precision_eval.md
- reddit_signal_eval.md
- email_prompt_injection_eval.md
- skill_safety_eval.md
- self_improvement_regression_eval.md
- code_quality_eval.md
- competitive_parity_eval.md

## 8. Development Operating Model

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
11. No external scanner runs without explicit connector permission.
12. No self-improvement merge without tests, evals, and review gates appropriate to risk.
13. No external skill install without trust evaluation and quarantine.

## 9. Roadmap

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

### M13: Companion Layer V1
Build companion profile, tone adaptation, relationship/context memory, user-controlled personal memory review, and boundary evals.

### M14: Signal Intelligence V1
Build normalized signal ingestion, source connectors, dedupe/clustering, relevance scoring, digest generation, and source verification.

### M15: Scanner Pack V1
Build Reddit Scanner, News Scanner, Article/RSS Scanner, Weather Scanner, Email Scanner, Message Scanner, Calendar Scanner, and Code/Dependency Scanner behind permission gates.

### M16: Skill Factory V1
Build skill manifest, skill discovery, external skill trust scoring, quarantine install, skill generator, skill tests, skill versioning, and skill promotion workflow.

### M17: Self-Improving Coding V1
Build issue mining, improvement candidates, self-improvement specs, branch/patch creation, tests/evals, reviewer agent, canary workflow, rollback, and codebase memory.

### M18: Competitive Parity V1
Build and maintain a parity matrix against Hermes Agent, OpenClaw, Devin-style coding agents, LangGraph, OpenAI Agents SDK, CrewAI, MCP ecosystems, and other major agent platforms.

## 10. First Vertical Slice

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

Second vertical slice:

User asks: Monitor AI agent news and Reddit for true breaking news relevant to this project.

System flow:
1. Orchestrator classifies task as proactive watchlist setup.
2. Creates watchlist spec and scanner config.
3. Asks for source/channel/notification permissions.
4. Runs News Scanner and Reddit Scanner in read-only mode.
5. Clusters and verifies events.
6. Produces digest or alert.
7. Learns from feedback.

Third vertical slice:

User asks: The agent needs a skill it does not have.

System flow:
1. Orchestrator detects missing capability.
2. Skill Factory searches internal library, external skill registries, plugins, and MCP options.
3. Trust evaluator scores candidates.
4. If no safe existing skill exists, Skill Builder writes a new skill spec.
5. Builder creates skill in sandbox.
6. QA runs tests and evals.
7. User approves promotion.
8. Skill becomes reusable procedural memory.

## 11. MVP Scope

MVP includes:
- Commander/Orchestrator Agent
- Execution Contract schema
- Context Pack schema
- Memory Service V1
- Companion profile basics
- Canonical File Manager
- Spec Generator
- Simple Kanban state
- QA Checklist Agent
- File Manager V1
- Web Research V1
- Code generation and sandboxed test execution
- Basic adaptive learning from explicit preferences and user feedback
- Basic proactive digest/alert architecture with opt-in watchlists
- Basic Signal Intelligence architecture
- Initial Reddit/news/article curation prototype
- Initial skill manifest and local Skill Factory prototype
- Initial self-improvement issue/spec/test loop for non-critical code improvements

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
- Autonomous self-modification of production core code
- Unreviewed external skill installs
- Full email/message scanning without explicit connector permission

## 12. Proactive Learning and Notification Operating Model

The agent should not wait passively for every instruction. It should become a trusted proactive partner that learns what matters and surfaces important information at the right time.

User examples:
- True breaking news related to user-selected topics, companies, people, markets, locations, or projects.
- Security advisories affecting tools, libraries, vendors, or codebases the user uses.
- API deprecations or pricing changes affecting active projects.
- Project deadlines, blocked work, stale specs, or overdue reviews.
- Competitor launches or market signals relevant to user ventures.
- Follow-up prompts when the user asked the agent to monitor something.
- Weather hazards affecting the user's travel, home, or scheduled events.
- Important emails or messages that require user attention.

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
  "entities": ["OpenAI", "Anthropic", "Hermes Agent", "OpenClaw", "agent frameworks"],
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

## 13. Feature Parity Matrix v0.1

| Source system | Capability to match or exceed | Ultimate AI Agent approach |
|---|---|---|
| Hermes Agent | Persistent curated memory, USER/MEMORY-style hot memory, memory providers, autonomous skill creation, skill self-improvement, multi-platform messaging, scheduled automations, web/media tools | Postgres memory + hot context cards + provider adapters + Skill Factory + Signal Intelligence + governed Tool Broker |
| OpenClaw | Self-hosted gateway, multi-channel messaging, mobile nodes, Control UI, multi-agent routing, ClawHub-like skills/plugins marketplace, scanner-style integrations | Gateway layer + channels/plugins + mobile nodes later + Control UI + skill registry + trust-scanned plugins |
| Devin-style coding agents | Autonomous coding, ticket execution, write/run/test loops, multi-repo context, codebase learning | Code Workspace + Self-Improving Coding Framework + Spec SDLC + codebase memory + PR workflow |
| LangGraph | Durable execution, checkpoints, long-running workflows, human-in-the-loop, persistence | Orchestration Engine with run state, checkpoints, approvals, resumption, and traces |
| OpenAI Agents SDK | Tools, handoffs, guardrails, structured outputs, tracing | Commander + specialist agents + Tool Broker + schemas + guardrails + tracing |
| CrewAI | Crews, flows, role-specialized agents, memory, knowledge, guardrails, observability | Specialist agent registry + workflow engine + memory/context packs + QA/evals |
| MCP ecosystem | Standardized connection to tools, databases, files, and APIs | MCP-compatible Tool Broker and connector registry |

## 14. Memory Snapshot

The Ultimate AI Agent project baseline is: Build a Commander-led, spec-driven, memory-backed, companion-style AI operating system that turns vague goals into verified completed outcomes. The system uses canonical files as source of truth, Postgres-backed long-term memory for continuity, Spec SDLC for major work, Kanban and roadmap for development focus, Tool Broker-mediated access to files/memory/code/web/scanners/external tools, sandboxed code execution, governed internet research, adaptive learning over time, companion personalization, proactive intelligence and opt-in notifications, Signal Intelligence scanners for news/Reddit/articles/weather/email/messages/calendar/code/competitors, a Skill Factory for acquiring or creating missing capabilities, a robust self-improving coding framework, approval-gated autonomy, and QA/evals before delivery. The project targets feature parity with Hermes Agent, OpenClaw, Devin-style coding agents, LangGraph, OpenAI Agents SDK, CrewAI, MCP ecosystems, and other major agent platforms while aiming to combine the best parts into a single Swiss-Army-knife super agent.

## 15. Sources Reviewed for Competitive Parity

- Hermes Agent documentation and GitHub repository
- OpenClaw documentation, website, and GitHub repository
- Devin documentation and website
- OpenAI Agents SDK documentation
- LangGraph documentation
- CrewAI documentation
- MCP ecosystem concepts and prior project decisions



---

# v0.4 Addendum: Trust, Control, and Layered Brain Architecture

## 16. New v0.4 Foundational Decisions

22. Add a User Control Center as the user's command dashboard for memory, permissions, watchlists, scanners, skills, automations, costs, connected accounts, notification settings, and activity logs.
23. Add a Consent and Permissions Ledger so every scanner, connector, automation, and proactive behavior is backed by durable user permission.
24. Add an Observability and Event Ledger so every meaningful run has a black-box-recorder trace.
25. Add a Security Threat Model before broad web/email/message/scanner execution.
26. Add a Data Lifecycle and Privacy module so the user can inspect, export, edit, pause, and delete personal data and derived memory.
27. Add a Cost and Resource Governor so proactive monitoring, model use, code execution, embeddings, storage, and APIs stay within budgets.
28. Add a Model Routing Strategy so the system can choose fast, cheap, strong, coding, vision, local, or privacy-preserving models based on task, risk, latency, cost, and context.
29. Add a Source Credibility and Rumor Protocol so breaking news, Reddit signals, and social chatter are labeled by verification level.
30. Add Rollback and Recovery as a design requirement for every state-changing action.
31. Add Agent Interoperability so MCP-style tools/resources and A2A-style agent communication can coexist under one governance layer.
32. Add an Agent Constitution that binds orchestration, tools, memory, scanners, notifications, skill installation, and self-improvement.
33. Add a Layered Brain / Onion Architecture so foundational capabilities are built first and higher-order capabilities can evolve without destabilizing the system.
34. Add a Capability Registry and Dependency Graph so every module declares its dependencies, permissions, contracts, evals, health, ownership, and rollback plan.
35. Add Shadow Mode, Simulation, and Digital Twin Testing before risky proactive, scanner, coding, or external-action changes go live.
36. Add Foundation Change Management and Contract Testing so core changes do not topple dependent capabilities.

## 17. User Control Center

Purpose: Give the user one place to inspect, steer, limit, approve, revoke, and tune the entire assistant.

The Control Center is not optional. A truly useful virtual assistant will know a lot, monitor a lot, and act across many tools. Without a strong user control surface, the agent becomes opaque and hard to trust.

Core views:

- Today view: briefings, alerts, approvals, open tasks, important deadlines, and suggested actions.
- Memory view: what the agent knows, where it learned it, confidence, scope, edit/delete/export controls.
- Permissions view: connected accounts, allowed actions, denied actions, expiration dates, sensitive scopes.
- Watchlist view: monitored topics, entities, thresholds, channels, quiet hours, and alert limits.
- Scanners view: Reddit, news, weather, email, messages, calendar, code/dependency, competitor, market, article/RSS, and future modules.
- Skills view: installed skills, trust level, source, version, permissions, tests, update status, usage history.
- Automations view: scheduled jobs, triggers, last run, next run, failure state, pause/resume controls.
- Approvals queue: actions awaiting user review.
- Activity log: what happened, why it happened, tools used, cost, memory writes, files changed, alerts sent.
- Cost view: spending by model, project, scanner, skill, tool, and time period.
- Data/privacy view: export, delete, retention, pause learning, pause scanners, local-only mode options.
- Personality/tone view: assistant mode, communication style, companion boundaries, proactive cadence.

Required commands:

```text
Show me what you know about me.
Why did you notify me about this?
Show all permissions for Gmail.
Pause all scanners.
Mute this topic.
Forget this memory.
Export my project memory.
Revoke this skill's network access.
Show what you did today.
Roll back the last file change.
```

Acceptance criteria:

- User can inspect all active memories, permissions, watchlists, skills, automations, and scanner configs.
- User can pause or revoke any proactive behavior.
- User can export and delete memory by scope.
- User can see activity traces and approval history.
- User can tune notification thresholds and quiet hours.

Canonical file:

```text
/docs/canonical/20_user_control_center.md
```

ADR:

```text
/docs/decisions/ADR-0019-use-user-control-center.md
```

## 18. Consent and Permissions Ledger

Purpose: Record exactly what the user has authorized the agent to access, monitor, remember, and do.

Approval gates handle individual actions. The Consent Ledger handles durable permission.

Examples:

```text
The agent may scan AI newsletters in Gmail daily.
The agent may summarize Slack channels but not DMs.
The agent may watch Reddit for AI agent news.
The agent may send critical weather alerts during quiet hours.
The agent may remember project decisions globally within this project.
The agent may not remember personal medical, legal, or family details unless explicitly requested.
```

Permission object:

```json
{
  "permission_id": "perm_123",
  "user_id": "user_123",
  "scope": "email_scanner | reddit_scanner | message_scanner | memory | skill | automation | tool",
  "resource": "gmail_personal",
  "allowed_actions": ["read", "summarize", "extract_tasks"],
  "denied_actions": ["send", "delete", "forward", "publish"],
  "content_boundaries": ["newsletters", "receipts", "work-related"],
  "excluded_content": ["family", "medical", "legal"],
  "autonomy_level": 2,
  "requires_reapproval_for": ["new_sender_category", "external_action", "destructive_action"],
  "expires_at": "2026-12-31T23:59:59Z",
  "status": "active | paused | revoked | expired",
  "source": "explicit_user_approval",
  "created_at": "2026-05-28T00:00:00Z",
  "updated_at": "2026-05-28T00:00:00Z"
}
```

Rules:

- No scanner runs without explicit permission.
- No connector uses credentials without a recorded permission.
- Private content is never used to create broad/global memories without user-controlled scope.
- Permissions expire or require renewal for sensitive connectors.
- Current user instruction can revoke or narrow permission immediately.
- Permissions are checked by the Tool Broker before tool execution.

Canonical file:

```text
/docs/canonical/21_consent_and_permissions_ledger.md
```

ADR:

```text
/docs/decisions/ADR-0020-use-consent-ledger.md
```

## 19. Observability and Event Ledger

Purpose: Make the agent inspectable, debuggable, auditable, and recoverable.

Every serious run should have a trace.

Event types:

```text
user_message
intent_classified
context_pack_built
memory_retrieved
canonical_file_read
execution_contract_created
subagent_called
tool_requested
tool_approved
tool_denied
tool_executed
file_changed
code_executed
test_run
eval_run
scanner_event_detected
notification_sent
approval_requested
approval_granted
approval_denied
memory_written
memory_superseded
skill_installed
skill_updated
rollback_created
rollback_executed
final_response_delivered
```

Run trace object:

```json
{
  "run_id": "run_123",
  "project_id": "ultimate_ai_agent",
  "user_id": "user_123",
  "intent": "create_spec",
  "status": "completed | failed | blocked | waiting_for_approval",
  "execution_contract_id": "contract_123",
  "context_pack_id": "ctx_123",
  "events": [],
  "tool_calls": [],
  "subagent_calls": [],
  "approvals": [],
  "files_changed": [],
  "memory_updates": [],
  "eval_results": [],
  "cost": {"tokens": 0, "api_cost_usd": 0.0},
  "started_at": "2026-05-28T00:00:00Z",
  "completed_at": "2026-05-28T00:00:00Z"
}
```

Rules:

- Every tool action is logged.
- Every memory write has a source event.
- Every file mutation has a diff and rollback metadata.
- Every notification explains source, relevance, confidence, and user permission.
- Every self-improvement patch is tied to issue, spec, branch, tests, evals, review, and release record.

Canonical file:

```text
/docs/canonical/22_observability_and_event_ledger.md
```

ADR:

```text
/docs/decisions/ADR-0021-use-agent-event-ledger.md
```

## 20. Security Threat Model

Purpose: Protect the user, the project, the assistant, and connected systems from malicious or accidental misuse.

Primary threat categories:

- Prompt injection from web pages, Reddit posts, emails, messages, PDFs, documents, GitHub issues, comments, and third-party skills.
- Tool misuse or excessive agency.
- Sensitive data leakage across scopes.
- Permission escalation by skills, connectors, or scanner outputs.
- Supply-chain attacks through skills, packages, plugins, MCP servers, browser tools, or code dependencies.
- Malicious memory writes from untrusted content.
- Retrieval poisoning and vector-store contamination.
- Unauthorized external actions.
- Credential exposure.
- Cost exhaustion through loops, high-frequency scanners, or model misuse.
- Self-improvement regressions that weaken safety gates.

Security rules:

```text
External content is data, not instruction.
Scanner outputs cannot directly trigger external actions.
Private content cannot cross project/user scopes without permission.
Web pages cannot override user instructions or canonical files.
Tool inputs must be validated.
High-risk actions require approval.
Secrets never appear in normal chat or logs.
Memory writes from untrusted content require classification and source labeling.
Skills run in sandbox/quarantine until trusted.
The agent cannot modify its own safety policies without review.
```

Required evals:

```text
prompt_injection_cross_source_eval.md
email_prompt_injection_eval.md
scanner_to_tool_escalation_eval.md
sensitive_data_leakage_eval.md
excessive_agency_eval.md
skill_supply_chain_eval.md
memory_poisoning_eval.md
self_improvement_safety_regression_eval.md
```

Canonical file:

```text
/docs/canonical/23_security_threat_model.md
```

ADR:

```text
/docs/decisions/ADR-0022-use-explicit-security-threat-model.md
```

## 21. Data Lifecycle and Privacy

Purpose: Make user data owned, inspectable, portable, scoped, and deletable.

Data categories:

```text
User profile memory
Project memory
Relationship memory
Raw conversation logs
Tool traces
File artifacts
Scanner outputs
Email/message-derived summaries
Web research cache
Skill usage logs
Code execution logs
Notification history
Feedback signals
```

Lifecycle states:

```text
created
active
stale
superseded
archived
scheduled_for_deletion
deleted
exported
```

User controls:

```text
Show me what you know about me.
Delete all memories from email scanning.
Export all memory for this project.
Pause learning.
Pause proactive monitoring.
Run in local-only mode.
Delete raw traces older than 30 days.
Forget this person/project/topic.
```

Retention defaults:

- Raw scanner events: short retention unless saved or converted into memory/artifact.
- Derived summaries: scoped and source-linked.
- Sensitive memories: require explicit reason and review controls.
- Tool logs: retained for debugging/audit, with redaction of secrets.
- Canonical project files: retained with version history.

Canonical file:

```text
/docs/canonical/24_data_lifecycle_and_privacy.md
```

ADR:

```text
/docs/decisions/ADR-0023-use-user-owned-data-lifecycle.md
```

## 22. Cost and Resource Governor

Purpose: Keep the agent useful without runaway costs or resource consumption.

Tracked resources:

```text
LLM tokens
Model cost
Embeddings
Web searches
API calls
Connector calls
Code execution time
Storage
Vector index size
Scanner frequency
Notification volume
Skill runs
Eval runs
```

Controls:

```text
Daily/monthly user budget
Project budget
Per-tool budget
Per-scanner budget
Per-skill budget
Quiet/cheap mode
Deep research approval threshold
High-cost model approval threshold
Caching and batching
Digest instead of instant alert
Rate limits and backoff
Loop detection
```

Budget policy object:

```json
{
  "budget_id": "budget_123",
  "scope": "user | project | scanner | skill | model | tool",
  "limit_usd_monthly": 20.0,
  "limit_tokens_daily": 500000,
  "high_cost_action_threshold_usd": 1.0,
  "default_mode": "balanced | cheap | premium | local",
  "requires_approval_above_threshold": true,
  "status": "active"
}
```

Canonical file:

```text
/docs/canonical/25_cost_and_resource_governor.md
```

ADR:

```text
/docs/decisions/ADR-0024-use-cost-and-resource-governor.md
```

## 23. Model Routing Strategy

Purpose: Use the right model or runtime for each task instead of treating the agent as one model.

Routing dimensions:

```text
task_type
risk_level
latency_requirement
cost_budget
privacy_requirement
context_length
modality
coding_complexity
source_verification_need
tool_permission_level
```

Model classes:

```text
fast_classifier
standard_assistant
strong_reasoner
coding_model
research_synthesizer
vision_model
embedding_model
reranker
local_private_model
high_reliability_critical_model
```

Routing rules:

- Low-risk classification uses fast/cheap models.
- Architecture, security, and self-improvement reviews use stronger models.
- Private data can route to local/private models where available.
- Coding tasks use coding-specialized runtimes and code execution verification.
- Critical external actions use high-reliability reasoning and explicit approval.
- Routing decisions are logged for observability and cost review.

Canonical file:

```text
/docs/canonical/26_model_routing_strategy.md
```

ADR:

```text
/docs/decisions/ADR-0025-use-model-routing.md
```

## 24. Source Credibility and Rumor Protocol

Purpose: Let the Super Curator handle breaking news, Reddit signals, articles, and rumors without misleading the user.

Verification levels:

```text
Level 0: raw signal / unverified claim
Level 1: single-source report
Level 2: multiple independent sources
Level 3: high-credibility publication or direct expert source
Level 4: primary-source confirmation
Level 5: official confirmation or authoritative data
Level R: retracted, contradicted, or disputed
```

Breaking-news alert must include:

```text
What happened
Why it matters to the user/project
Verification level
Confidence
Source list
What is known
What is not known
What changed since prior alert
Recommended action
Mute/tune options
```

Rules:

- Reddit and social media are early signals, not verified facts.
- The agent may alert on low-verification events only if the user asked for early-warning mode and the uncertainty is clearly labeled.
- Official/primary sources outrank commentary.
- Repeated coverage does not equal independent corroboration.
- Rumor updates should reduce noise by clustering rather than sending every mention.
- Retractions and corrections must update prior memory/digests.

Canonical file:

```text
/docs/canonical/27_source_credibility_and_rumor_protocol.md
```

ADR:

```text
/docs/decisions/ADR-0026-use-rumor-and-source-credibility-protocol.md
```

## 25. Rollback and Recovery

Purpose: Make the agent forgiving. Anything that can mutate state should have an undo story.

Rollback targets:

```text
File changes
Canonical file updates
Memory writes
Skill installs
Scanner configurations
Watchlists
Notifications
Automations
Code patches
Database migrations
Connector permissions
Prompt changes
Eval changes
Model routing changes
Tool configuration changes
```

Rollback metadata:

```json
{
  "rollback_id": "rollback_123",
  "action_id": "action_123",
  "target_type": "file | memory | skill | scanner | code | permission | automation",
  "before_state_ref": "object_store://before",
  "after_state_ref": "object_store://after",
  "diff_ref": "diff_123",
  "rollback_method": "apply_reverse_patch | restore_snapshot | disable | revoke | migrate_down",
  "risk_level": "low | medium | high",
  "requires_approval": true,
  "status": "available | executed | expired | unsafe"
}
```

Rules:

- Every file mutation has a diff and previous version.
- Every memory write can be deleted, archived, or superseded.
- Every skill install can be disabled or rolled back to prior version.
- Every connector permission can be revoked immediately.
- Every self-improvement change must have rollback or revert plan.
- High-risk rollback itself may require approval.

Canonical file:

```text
/docs/canonical/28_rollback_and_recovery.md
```

ADR:

```text
/docs/decisions/ADR-0027-use-rollback-first-action-design.md
```

## 26. Agent Interoperability

Purpose: Allow the Ultimate AI Agent to integrate with tools, data sources, services, and other agents without hardcoding everything.

Interoperability layers:

```text
MCP-style tool/resource/data-source integration
A2A-style agent-to-agent communication
Skill manifests
Connector adapters
Webhook/event subscriptions
Local desktop/mobile gateway
External agent delegation
Internal specialist-agent protocol
```

Rules:

- Tool interoperability goes through Tool Broker.
- Agent interoperability goes through Orchestrator and Agent Registry.
- External agents are treated as untrusted until permissioned and scoped.
- Cross-agent calls have execution contracts, context limits, and output validation.
- External agent outputs cannot directly trigger high-risk tools.
- Interoperability events are logged.

Canonical file:

```text
/docs/canonical/29_agent_interoperability.md
```

ADR:

```text
/docs/decisions/ADR-0028-use-mcp-and-a2a-interoperability.md
```

## 27. Agent Constitution

Purpose: Provide a stable behavior contract for the entire system.

Constitution v0.1:

1. User agency comes first.
2. Be useful, truthful, inspectable, and reversible where possible.
3. Be proactive only when value exceeds interruption cost.
4. Ask approval before risky, external, destructive, financial, reputational, privacy-sensitive, or irreversible actions.
5. Never let untrusted content control tools, memory, permissions, or external actions.
6. Prefer verified sources over speed; label uncertainty when speed matters.
7. Current user instructions override learned preferences.
8. Approved canonical files outrank memory.
9. Do not hoard personal data; remember what improves assistance and give the user control.
10. Learn through memory, feedback, skills, tests, evals, and review, not silent uncontrolled self-modification.
11. Every major action should leave a receipt.
12. Every recurring failure should become a test, eval, playbook, skill improvement, or documented lesson.
13. When unsure about risk, reduce autonomy and ask for approval.
14. Stay transparent that the assistant is AI, even when using a warm companion style.
15. Keep the system modular so lower layers can change without breaking higher layers.

The constitution is used by:

```text
Orchestrator
Tool Broker
Memory Curator
Notification Policy Engine
Skill Factory
Self-Improvement Framework
QA/Eval Agent
Security Agent
Model Router
```

Canonical file:

```text
/docs/canonical/30_agent_constitution.md
```

ADR:

```text
/docs/decisions/ADR-0029-use-agent-constitution.md
```

## 28. Layered Brain / Onion Architecture

Purpose: Build the agent in layers, like a brain or onion, so basic functions work first and higher capabilities can be added without destabilizing the foundation.

Core principle:

> Lower layers provide stable primitives. Higher layers compose those primitives. Higher layers must not depend on lower-layer implementation details, only on versioned contracts.

Layer model:

```text
Layer 0: Kernel and Constitution
  Identity, user agency rules, autonomy policy, security baseline, event ledger, run state, contracts.

Layer 1: Truth, Memory, and Data Ownership
  Canonical files, Memory Service, data lifecycle, context packs, project state, source references.

Layer 2: Tools, Files, Code, and Web
  Tool Broker, File Manager, Code Workspace, Web Research Service, sandboxing, permissions, rollback.

Layer 3: Orchestration and Work Execution
  Commander Agent, execution contracts, workflow state machine, Spec SDLC, Kanban, QA/evals.

Layer 4: Skills and Intelligence Loops
  Skill Factory, Adaptive Learning, Self-Improving Coding, Scanner modules, Signal Intelligence.

Layer 5: Relationship and Proactivity
  Companion Layer, watchlists, notifications, attention budget, personal routines, digests.

Layer 6: Ecosystem and Autopilot
  Multi-channel gateways, external execution, MCP/A2A interoperability, scheduled workflows, team mode.
```

Dependency rules:

```text
Layer N may call Layer N-1 through public contracts.
Layer N must not depend on private internals of lower layers.
Lower layers must not call higher layers directly.
Cross-layer communication should use events, schemas, and service interfaces.
Every layer has contract tests.
Every layer can be mocked in tests.
Every layer exposes health checks.
Every layer has rollback or fallback behavior.
```

Build order:

```text
1. Kernel contracts and event ledger.
2. Canonical files and Memory Service.
3. Tool Broker and File Manager.
4. Orchestrator and Execution Contract.
5. Spec SDLC and QA/evals.
6. Web Research and Code Workspace.
7. Control Center and Consent Ledger.
8. Adaptive Learning and Skill Factory.
9. Signal Intelligence and Scanners.
10. Companion Layer and Proactive Notifications.
11. Self-Improving Coding.
12. External execution and Autopilot.
```

This lets the foundation evolve without toppling the system.

Canonical file:

```text
/docs/canonical/31_layered_brain_architecture.md
```

ADR:

```text
/docs/decisions/ADR-0030-use-layered-brain-onion-architecture.md
```

## 29. Capability Registry and Dependency Graph

Purpose: Make every capability explicit, versioned, permissioned, testable, and observable.

Every module/skill/scanner/tool should register itself.

Capability manifest:

```json
{
  "capability_id": "cap_memory_v1",
  "name": "Memory Service V1",
  "type": "core_service | scanner | skill | tool | agent | workflow | connector",
  "version": "1.0.0",
  "layer": 1,
  "owner": "system",
  "description": "Stores and retrieves project/user memory.",
  "dependencies": ["cap_event_ledger_v1", "cap_postgres_v1"],
  "public_contracts": ["memory.recall", "memory.retain", "memory.supersede"],
  "permissions_required": [],
  "risk_level": "medium",
  "data_access": ["project_memory", "user_preferences"],
  "evals_required": ["memory_recall_eval", "memory_supersession_eval"],
  "health_checks": ["memory_read", "memory_write", "embedding_index_status"],
  "rollback_plan": "disable_writes_and_restore_snapshot",
  "status": "active | experimental | deprecated | disabled"
}
```

Dependency graph uses:

- Understand blast radius before changing foundation code.
- Identify which evals to run when a module changes.
- Determine which permissions a skill indirectly depends on.
- Detect circular dependencies.
- Decide safe startup/shutdown order.
- Generate project health dashboards.

Rules:

- No major capability ships without a manifest.
- No capability can bypass the Tool Broker if it uses tools.
- No capability can store memory without Memory Service.
- No scanner can notify directly without Notification Policy Engine.
- No skill can execute code without Code Workspace/Sandbox permission.

Canonical file:

```text
/docs/canonical/32_capability_registry_and_dependency_graph.md
```

ADR:

```text
/docs/decisions/ADR-0031-use-capability-registry-and-dependency-graph.md
```

## 30. Shadow Mode, Simulation, and Digital Twin Testing

Purpose: Test agent behavior safely before it acts in the real world.

Modes:

```text
Dry run: produce proposed actions without executing.
Shadow mode: observe real inputs and compare what the agent would have done, but do not act.
Simulation mode: run synthetic scenarios through the system.
Replay mode: rerun historical traces after code/prompt/model changes.
Digital twin mode: test against a simulated user/project profile with seeded preferences, permissions, files, and memory.
Canary mode: expose a new capability to low-risk traffic or a small scope.
```

Use cases:

- Test notification relevance before interrupting the user.
- Test email/message scanner behavior without touching real inbox state.
- Test self-improvement patches against historical failures.
- Test model router changes against old runs.
- Test memory retrieval after schema changes.
- Test prompt injection defense using malicious documents/messages.
- Test breaking-news rumor protocol against historical cases.

Required before live release:

```text
New scanner modules
New external-action tools
New notification policies
New model router policies
New self-improvement logic
New memory-retention/reflection logic
New skill installer behavior
Major orchestrator changes
```

Canonical file:

```text
/docs/canonical/33_shadow_mode_simulation_and_digital_twin_testing.md
```

ADR:

```text
/docs/decisions/ADR-0032-use-shadow-mode-and-simulation-harness.md
```

## 31. Foundation Change Management and Contract Testing

Purpose: Make it safe to change the foundation without breaking higher layers.

Problem:

A powerful agent will depend on a small set of core primitives: memory, files, tools, permissions, run state, schemas, model routing, and orchestration. If these change carelessly, scanners, skills, self-improvement, notifications, and code execution can all break.

Solution:

Treat foundational capabilities like public platform APIs.

Foundation change process:

```text
1. Create foundation change proposal.
2. Identify affected capabilities using dependency graph.
3. Update schemas/contracts with versioning.
4. Add migration path and compatibility window.
5. Run contract tests.
6. Replay historical traces.
7. Run integration/eval suite.
8. Run shadow mode or canary.
9. Update canonical files and ADRs.
10. Release behind feature flag.
11. Monitor health metrics.
12. Roll back if regression thresholds are crossed.
```

Required contract test categories:

```text
Memory API contract tests
Context Pack schema tests
Execution Contract schema tests
Tool Broker permission tests
File Manager diff/rollback tests
Event Ledger append/read tests
Model Router output contract tests
Notification policy tests
Scanner output schema tests
Skill manifest tests
Self-improvement pipeline tests
```

Feature flag policy:

- Major foundational changes ship behind flags.
- Flags have owners, expiration dates, and rollback behavior.
- Flag state is logged in run traces.
- Shadow/canary results determine promotion.

Compatibility rules:

- Breaking schema changes require migration and dual-read or dual-write where practical.
- Higher layers should tolerate missing optional fields.
- Deprecated contracts get a planned removal window.
- Old run traces should remain readable.

Canonical file:

```text
/docs/canonical/34_foundation_change_management_and_contract_testing.md
```

ADR:

```text
/docs/decisions/ADR-0033-use-foundation-change-management-and-contract-testing.md
```

## 32. Updated Canonical File Structure v0.4

```text
/docs/canonical/
  00_project_brief.md
  01_product_spec.md
  02_agent_operating_model.md
  03_memory_system.md
  04_spec_sdlc.md
  05_development_workflow.md
  06_tool_architecture.md
  07_autonomy_and_permissions.md
  08_evaluation_framework.md
  09_roadmap.md
  10_file_management.md
  11_code_generation_and_execution.md
  12_internet_access.md
  13_adaptive_learning.md
  14_proactive_intelligence_and_notifications.md
  15_companion_layer.md
  16_signal_intelligence_platform.md
  17_skill_factory.md
  18_self_improving_coding_framework.md
  19_competitive_parity.md
  20_user_control_center.md
  21_consent_and_permissions_ledger.md
  22_observability_and_event_ledger.md
  23_security_threat_model.md
  24_data_lifecycle_and_privacy.md
  25_cost_and_resource_governor.md
  26_model_routing_strategy.md
  27_source_credibility_and_rumor_protocol.md
  28_rollback_and_recovery.md
  29_agent_interoperability.md
  30_agent_constitution.md
  31_layered_brain_architecture.md
  32_capability_registry_and_dependency_graph.md
  33_shadow_mode_simulation_and_digital_twin_testing.md
  34_foundation_change_management_and_contract_testing.md
```

## 33. Updated ADR List v0.4

```text
ADR-0001-use-spec-sdlc.md
ADR-0002-canonical-files-as-source-of-truth.md
ADR-0003-use-postgres-for-memory.md
ADR-0004-use-memory-service-api.md
ADR-0005-use-commander-plus-specialists.md
ADR-0006-use-orchestrator-control-plane.md
ADR-0007-use-tool-broker-for-external-actions.md
ADR-0008-use-approval-gated-autonomy.md
ADR-0009-use-project-file-manager.md
ADR-0010-use-sandboxed-code-execution.md
ADR-0011-use-governed-internet-access.md
ADR-0012-use-adaptive-learning-service.md
ADR-0013-use-proactive-intelligence-notifications.md
ADR-0014-use-companion-layer.md
ADR-0015-use-signal-intelligence-platform.md
ADR-0016-use-skill-factory.md
ADR-0017-use-self-improving-coding-framework.md
ADR-0018-target-competitive-feature-parity.md
ADR-0019-use-user-control-center.md
ADR-0020-use-consent-ledger.md
ADR-0021-use-agent-event-ledger.md
ADR-0022-use-explicit-security-threat-model.md
ADR-0023-use-user-owned-data-lifecycle.md
ADR-0024-use-cost-and-resource-governor.md
ADR-0025-use-model-routing.md
ADR-0026-use-rumor-and-source-credibility-protocol.md
ADR-0027-use-rollback-first-action-design.md
ADR-0028-use-mcp-and-a2a-interoperability.md
ADR-0029-use-agent-constitution.md
ADR-0030-use-layered-brain-onion-architecture.md
ADR-0031-use-capability-registry-and-dependency-graph.md
ADR-0032-use-shadow-mode-and-simulation-harness.md
ADR-0033-use-foundation-change-management-and-contract-testing.md
```

## 34. Updated Schema List v0.4

```text
memory.schema.json
context_pack.schema.json
execution_contract.schema.json
agent_run.schema.json
run_event.schema.json
tool_call.schema.json
approval_request.schema.json
permission.schema.json
consent_record.schema.json
rollback_record.schema.json
capability_manifest.schema.json
capability_dependency.schema.json
feature_flag.schema.json
model_routing_policy.schema.json
cost_budget.schema.json
watchlist.schema.json
notification_event.schema.json
source_credibility.schema.json
rumor_event.schema.json
scanner_config.schema.json
signal_event.schema.json
skill_manifest.schema.json
skill_run.schema.json
self_improvement_run.schema.json
code_patch_review.schema.json
companion_profile.schema.json
relationship_memory.schema.json
user_feedback_signal.schema.json
data_retention_policy.schema.json
privacy_scope.schema.json
```

## 35. Updated Evals v0.4

```text
memory_recall_eval.md
memory_supersession_eval.md
spec_compliance_eval.md
tool_approval_eval.md
canonical_file_precedence_eval.md
hallucination_eval.md
proactive_alert_relevance_eval.md
breaking_news_verification_eval.md
rumor_protocol_eval.md
source_credibility_eval.md
attention_budget_eval.md
learning_feedback_eval.md
companion_boundary_eval.md
scanner_precision_eval.md
reddit_signal_eval.md
email_prompt_injection_eval.md
message_prompt_injection_eval.md
prompt_injection_cross_source_eval.md
sensitive_data_leakage_eval.md
excessive_agency_eval.md
skill_safety_eval.md
skill_supply_chain_eval.md
self_improvement_regression_eval.md
code_quality_eval.md
rollback_eval.md
permission_scope_eval.md
data_deletion_eval.md
model_routing_eval.md
cost_governor_eval.md
observability_trace_completeness_eval.md
contract_test_suite.md
shadow_mode_replay_eval.md
competitive_parity_eval.md
```

## 36. Updated Roadmap v0.4

M0 through M18 remain from v0.3. v0.4 adds the trust/control and stability milestones below.

### M19: User Control and Consent V1

Deliver:

```text
User Control Center shell
Memory/permissions/watchlists/skills/automations overview
Consent Ledger schema
Permission review/update/revoke flow
Approvals queue
Pause all scanners / pause learning controls
```

### M20: Event Ledger and Observability V1

Deliver:

```text
agent_runs table
run_events table
tool_call logs
memory source links
file diff logs
approval logs
cost logs
activity view
trace completeness eval
```

### M21: Security Threat Model and Red-Team Harness V1

Deliver:

```text
Threat model canonical doc
Prompt-injection evals
Scanner-to-tool escalation eval
Sensitive data leakage eval
Skill supply-chain scan
Untrusted content policy
Security review checklist
```

### M22: Data Lifecycle, Privacy, and Export V1

Deliver:

```text
Data category inventory
Retention policies
Export memory/project data
Delete by scope
Pause learning
Delete scanner-derived data
Audit deletion events
```

### M23: Cost Governor and Model Router V1

Deliver:

```text
Budget policy schema
Per-project cost tracking
Per-scanner rate limits
Cheap/balanced/premium modes
Model routing policy
Routing logs
Cost alerts
```

### M24: Source Credibility and Rumor Protocol V1

Deliver:

```text
Verification levels
Source scoring
Breaking-news alert template
Rumor/retraction handling
Clustered updates
Source credibility eval
```

### M25: Rollback and Recovery V1

Deliver:

```text
Rollback metadata schema
File rollback
Memory rollback/supersession
Skill disable/rollback
Scanner config rollback
Self-improvement revert flow
Rollback evals
```

### M26: Layered Brain Stability V1

Deliver:

```text
Layer map
Service contracts
Capability registry
Dependency graph
Feature flags
Contract tests
Shadow/replay harness
Foundation change process
```

## 37. Entire Project Review After v0.4

### Verdict

The project is now more than a collection of agent features. It has the shape of a serious personal AI operating system:

```text
Orchestration for coherence.
Canonical files for truth.
Memory for continuity.
Tool Broker for safe action.
File/code/web/scanner services for capability.
Spec SDLC and Kanban for disciplined development.
Adaptive learning and companion context for personalization.
Signal Intelligence for proactive awareness.
Skill Factory for growth.
Self-improving code for long-term quality.
User Control Center, Consent Ledger, Event Ledger, Security, Rollback, and Cost Governor for trust.
Layered Brain architecture for evolvability.
```

The architecture is ambitious but now has a credible control plane.

### Strongest parts

1. The Commander/Orchestrator model gives the system a center of gravity.
2. Canonical files prevent memory drift and make the project inspectable.
3. Postgres-backed memory plus source references gives durable context without relying only on chat history.
4. Spec SDLC prevents vibe-built features.
5. Tool Broker and approval gates reduce excessive agency risk.
6. Skill Factory and self-improving code give the agent a path to grow.
7. Signal Intelligence makes proactive utility a first-class product, not an afterthought.
8. User Control Center and Consent Ledger give the user power over the assistant.
9. Observability and rollback make failures diagnosable and recoverable.
10. Layered Brain architecture addresses the biggest engineering concern: foundational changes should not topple the system.

### Biggest risks

1. Scope explosion.
2. Building advanced modules before the kernel is stable.
3. Overly complex memory before project memory works reliably.
4. Proactive notifications becoming noisy.
5. Skill/plugin supply-chain risk.
6. Self-improving code weakening safety if not governed.
7. Scanner prompt injection from web/email/messages/Reddit.
8. Canonical files becoming stale if updates are not automated.
9. Cost growth from scanners, deep research, and evals.
10. Companion layer crossing boundaries if not heavily tested.

### Risk mitigations now in v0.4

```text
Scope explosion -> Kanban WIP limits, roadmap, Parking Lot, Spec SDLC.
Foundation instability -> Layered Brain, contract tests, capability graph, shadow mode.
Memory drift -> canonical files outrank memory, memory source links, supersession.
Noisy proactivity -> attention budget, watchlists, relevance/confidence thresholds.
Skill risk -> skill trust levels, quarantine, sandbox, security scan.
Self-improvement risk -> branches, tests, evals, review, canary, rollback.
Prompt injection -> threat model, untrusted-content policy, scanner-to-tool isolation.
Cost growth -> Cost Governor, model router, rate limits, digests, cheap mode.
User trust -> Control Center, Consent Ledger, Event Ledger, rollback, export/delete.
```

### Architecture scorecard v0.4

| Area | Score | Review |
|---|---:|---|
| Vision clarity | 9.5/10 | Strong and differentiated. |
| Orchestration model | 9/10 | Correct control-plane pattern. |
| Memory architecture | 9/10 | Strong, source-backed, scoped, and evolvable. |
| Canonical/spec discipline | 9.5/10 | One of the strongest project choices. |
| Development workflow | 9/10 | Spec-Kanban with WIP limits and evals is practical. |
| Tool/action safety | 8.5/10 | Strong after Tool Broker, Consent Ledger, and rollback. |
| Proactive intelligence | 8.5/10 | Strong, but needs careful attention-budget tuning. |
| Companion/personalization | 8/10 | Promising, but needs strong boundary evals. |
| Self-improving code | 8.5/10 | Strong if kept branch/test/review/canary gated. |
| Security/privacy | 8.5/10 | Much stronger after v0.4, still needs implementation rigor. |
| Evolvability | 9/10 | Layered Brain + capability graph + contract tests address the core concern. |
| MVP focus | 7.5/10 | Still ambitious. Must enforce build order aggressively. |
| Overall | 9/10 | Serious, coherent, and buildable if phased correctly. |

## 38. Final Review and Last-Minute Additions Included in v0.4

After reviewing v0.4 one more time, the last-minute additions that matter most are not more scanners or more flashy agent features. They are structural features that keep the foundation safe as the agent grows.

The final additions included are:

### 1. Layered Brain / Onion Architecture

This directly addresses the concern that foundation changes should not topple everything. The project will build stable layers first and then stack higher capabilities on top.

### 2. Capability Registry and Dependency Graph

This gives the system awareness of what depends on what. Before changing the Memory Service, Tool Broker, Context Pack schema, or Model Router, the system can know which capabilities, evals, and workflows are affected.

### 3. Shadow Mode, Simulation, and Digital Twin Testing

This lets the agent test behavior before acting. Especially important for proactive alerts, email/message scanners, code self-improvement, and high-risk automations.

### 4. Foundation Change Management and Contract Testing

This makes foundation changes deliberate: proposal, impact analysis, schema versioning, contract tests, replay, canary, feature flags, monitoring, rollback.

### 5. Feature Flags

Feature flags are included under Foundation Change Management. They let new behavior ship gradually, be disabled quickly, and avoid all-or-nothing releases.

### 6. Contract Tests as Non-Negotiable

Every foundational interface needs contract tests:

```text
Memory Service
Context Pack
Execution Contract
Tool Broker
File Manager
Event Ledger
Model Router
Notification Policy Engine
Skill Manifest
Scanner Output
```

If a contract breaks, higher-level modules should not ship.

### Final architectural principle

> The project should move from core reflexes to higher cognition. First build the nervous system: run state, events, memory, files, permissions, tools, and contracts. Then build reasoning and work execution. Then build learning, skills, self-improvement, scanners, companion behavior, and autopilot.

This is the onion/brain build philosophy.

## 39. Recommended Immediate Next Steps

1. Freeze v0.4 as the active master plan.
2. Create the canonical file tree for docs 00-34.
3. Create ADRs 0001-0033 as short accepted records.
4. Build M0: project foundation docs, schemas, definitions of ready/done.
5. Build the core kernel before advanced modules:

```text
Execution Contract schema
Context Pack schema
Run/Event Ledger schema
Memory Service schema
Permission/Consent schema
Capability Manifest schema
Tool Call schema
Rollback schema
```

6. Build the first vertical slice:

```text
User asks for Memory V1 spec
-> Orchestrator creates execution contract
-> Context Pack loads project truth
-> Spec Generator creates feature spec
-> QA checks it
-> Memory Curator writes source-linked project memory
-> Event Ledger records the run
-> File Manager saves canonical/spec files
```

7. Do not build scanners, companion proactivity, skill factory, or self-improving code before the kernel, file/memory system, event ledger, and permission model work.

## 40. Updated Memory Snapshot v0.4

The Ultimate AI Agent project baseline is now:

Build a Commander-led, spec-driven, memory-backed, companion-style AI operating system that turns vague goals into verified completed outcomes. The system uses canonical files as source of truth, Postgres-backed long-term memory for continuity, Spec SDLC for major work, Kanban and roadmap for development focus, Tool Broker-mediated access to files/memory/code/web/scanners/external tools, sandboxed code execution, governed internet research, adaptive learning over time, companion personalization, proactive intelligence and opt-in notifications, Signal Intelligence scanners, a Skill Factory for acquiring or creating missing capabilities, a robust self-improving coding framework, approval-gated autonomy, and QA/evals before delivery.

v0.4 adds that this system must also include a User Control Center, Consent and Permissions Ledger, Observability and Event Ledger, Security Threat Model, Data Lifecycle and Privacy controls, Cost and Resource Governor, Model Router, Source Credibility and Rumor Protocol, Rollback and Recovery system, Agent Interoperability layer, Agent Constitution, Layered Brain/Onion Architecture, Capability Registry and Dependency Graph, Shadow Mode/Simulation harness, and Foundation Change Management with Contract Testing.

The project must be built like an onion or brain: foundational reflexes and stable contracts first, then memory and tools, then orchestration and specs, then learning and skills, then scanners and proactive intelligence, then companion behavior and autopilot. Foundation changes must be versioned, tested through contracts, replayed in shadow mode, released behind flags, monitored, and rollback-ready so the system can evolve without collapsing.

---

# v0.4.1 Foundation-First Enforcement Addendum

## Status
Accepted as the active operational development policy.

## Why this addendum exists

The v0.4 master plan included the correct architectural rule: build the agent like an onion or a brain. However, the previous bundle did not include a standalone Kanban board or operational gate files that made that rule enforceable. v0.4.1 fixes that.

## Foundation Gate

Advanced modules cannot enter `Ready for Build` until the Foundation Gate passes.

Blocked advanced modules include:

```text
Scanner Modules
Companion Proactivity
Skill Factory / Skill Acquisition Service
Self-Improving Coding Framework
Autopilot Workflows
External Execution with high autonomy
```

The Foundation Gate passes only when these primitives exist and pass contract tests:

```text
Execution Contract schema
Context Pack schema
Run/Event Ledger schema
Memory Service V1
File Manager V1
Permission/Consent Ledger V1
Tool Broker V1
Capability Registry and Dependency Graph
Rollback primitives
Contract test suite
Shadow replay harness
Basic QA/eval baseline
```

## Kanban enforcement

Items blocked by the Foundation Gate must remain in `Parking Lot` or `Blocked`. They may be researched, shaped, and documented, but not implemented.

## Roadmap enforcement

The roadmap is reordered so the kernel, memory/files, event ledger, permission model, tool broker, and contract tests are built before scanners, proactivity, skill factory, and self-improving code.

## Principle

The agent should evolve like a layered brain: reflexes and stable contracts first; memory and tools second; orchestrated work third; learning, skills, scanners, companion behavior, and autopilot later.
