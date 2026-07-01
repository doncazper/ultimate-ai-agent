# Ultimate AI Agent Master Plan v0.3

> [!IMPORTANT]
> Historical planning artifact. This file is not active product truth, does not grant runtime authority, and must not be used as current implementation guidance. Active truth starts in README.md, docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md, docs/kanban/current_board.md, and accepted foundation docs such as docs/tooling/UAA_MCP_GATEWAY_FOUNDATION.md and docs/remote/UAA_A2A_GATEWAY_FOUNDATION.md.


Status: Working baseline expanded with companion learning, skill acquisition, self-improving code, signal intelligence, scanner modules, and competitive parity goals.
Project: Ultimate AI Agent
Purpose: Build a reliable, companion-style agentic operating system that turns vague user goals into verified completed outcomes while learning with the user over time.

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

