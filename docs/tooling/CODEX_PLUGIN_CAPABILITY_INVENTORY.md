# Codex Plugin Capability Inventory for Ultimate AI Agent

Source: local Codex inventory report
Status: Active tooling governance inventory, v0.14.6

This inventory records Codex plugin, tool, and capability classes that may help future Ultimate AI Agent milestones. It is inventory only. It does not enable, install, configure, or approve any plugin, connector, runtime, dependency, build system, network service, browser profile, signing identity, keychain item, provisioning profile, App Store Connect account, cloud job, deployment path, or runtime capability.

High-risk plugins require milestone-specific approval before use. External tools are development aids, not source-of-truth systems and not authority to bypass Agent Core governance.

## Summary Table

| Name | Capability class | Appears available | Current recommendation | Risk | Future milestone mapping | Enablement status |
| --- | --- | --- | --- | --- | --- | --- |
| Browser | In-app browser for local web pages, localhost UI checks, screenshots, and browser QA. | Yes. | Approved later with task-specific Web Control Center use. | Medium. | Future Web Control Center and API docs preview. | Future-only with approval. |
| Build iOS Apps / XcodeBuildMCP | iOS project discovery, simulator build/run/test, SwiftUI/App Intents, logs, coverage, and possible device workflows when configured. | Yes. | Keep disabled until a dedicated Mobile Companion implementation milestone. | Critical. | Future Mobile Companion implementation after policy/signing boundaries exist. | Disabled/future-only. |
| Build macOS Apps | macOS SwiftUI/AppKit build, run, test, signing, entitlement, packaging, and notarization workflows. | Yes. | Keep disabled until a dedicated Desktop/macOS Companion milestone. | Critical. | Future Desktop/macOS Companion. | Disabled/future-only. |
| Build Web Apps | Web app implementation, frontend testing, React/Next guidance, shadcn guidance, and UI polish. | Yes. | Use with Browser only for future Web Control Center work after approval. | Medium to high. | Future Web Control Center. | Future-only with approval. |
| Chrome | User Chrome profile control, authenticated sessions, tabs, cookies, and extensions. | Yes. | Keep disabled unless explicitly approved for authenticated-profile QA. | High. | Authenticated UI QA only if separately approved. | Disabled by default. |
| CodeRabbit | External AI code review, quality review, and security review. | Yes. | Allow read-only release readiness review with explicit review prompt. | Medium to high. | Release and security audits. | Read-only only with approval. |
| Computer Use | Local macOS UI automation through clicking, typing, scrolling, and screen inspection. | Yes. | Keep disabled except explicit last-resort manual QA approval. | Critical. | Last-resort manual QA. | Disabled by default. |
| GitHub | Repository, issue, PR, CI, and publishing workflows. | Yes. | Allow read-only release readiness checks; require explicit approval for writes. | High. | CI/release review. | Read-only only unless direct approval exists. |
| Hugging Face | Hub inspection, datasets, Spaces, jobs, Gradio, Trackio, and model training/evaluation tooling. | Yes. | Keep Jobs, uploads, training, and deployment disabled. | High to critical. | Distant research/eval milestone only. | Disabled by default. |
| Mem | Personal knowledge-base connector. | Yes. | Keep disabled unless explicitly approved for planning context. | Medium to high. | Planning context only. | Disabled by default. |
| Documents | Word/docx creation, editing, rendering, and verification. | Yes. | Use for release packets or design docs when requested. | Medium. | Documentation artifacts. | Future-only with approval. |
| Presentations | PowerPoint/PPTX deck creation, rendering, and export. | Yes. | Use for roadmap/status decks when requested. | Medium. | Planning and stakeholder artifacts. | Future-only with approval. |
| Spreadsheets | CSV/XLSX analysis, formulas, charts, and workbook rendering. | Yes. | Use for release matrices and risk registers when requested. | Medium. | Planning and audit artifacts. | Future-only with approval. |
| Superpowers | Local workflow guidance for planning, TDD, debugging, verification, and branch finishing. | Yes. | Safe as methodology; does not grant runtime authority. | Low to medium. | All milestones. | Allowed as process guidance. |
| exec_command shell | Local terminal commands for tests, verifiers, git, scripts, builds, and package managers. | Yes. | Use narrowly for verifier/test/git workflows. | Critical if misused. | Controlled verification and explicitly approved implementation. | Allowed only inside task scope. |
| apply_patch | Direct repository file editing. | Yes. | Use only for requested edits. | Medium to high. | Approved docs/code changes. | Allowed only inside task scope. |
| web.run | Internet lookup and retrieval. | Yes. | Use when current external facts are required. | Low to medium. | Standards/docs research. | Allowed only when relevant. |
| image_gen | Bitmap image generation. | Yes. | Use only when requested for visual artifacts. | Low to medium. | UI mockups or docs visuals. | Future-only with request. |
| Design tools | Figma, Stitch, Framer, screenshot-to-code, design-to-code, and AI UI generator workflows. | Not enabled. | Keep disabled until explicit design-tool milestone approval. | High. | Future optional design import/export evaluation. | Disabled/future-only. |
| Plugin/skill install tools | Discover, create, or install Codex plugins and skills. | Visible. | Keep disabled due to supply-chain risk. | High. | Tooling administration only after security lifecycle exists. | Disabled by default. |

## Inventory Rules

- Inventory may happen at any time.
- Enablement may happen only inside an explicit milestone, review, or user prompt that names the tool boundary.
- Build, signing, deployment, browser-authenticated, computer-use, cloud-compute, and plugin-install tools require high-risk or critical review.
- External tools are not authority. They may not bypass Execution Contract, Context Pack, Approval Authority, Tool Broker, Event Ledger, Secret Broker, redaction, verifier scripts, or Foundation Gate.

## Current Project Decisions

- Browser plus Build Web Apps may be considered for future Web Control Center work with explicit approval.
- Chrome authenticated profile control remains disabled unless explicitly approved.
- Build iOS Apps / XcodeBuildMCP remains disabled until a dedicated Mobile Companion implementation milestone.
- Build macOS Apps remains disabled until a dedicated Desktop/macOS Companion milestone.
- CodeRabbit and GitHub read-only review can be used for release readiness with explicit review prompts.
- GitHub write, release, push, tag, or PR actions require explicit approval or direct-push rules.
- Computer Use remains disabled except explicit last-resort manual QA approval.
- Hugging Face Jobs, uploads, training, and Spaces deployment remain disabled.
- Design tools, design SaaS sync, screenshot-to-code, design-to-code, and AI UI generators remain disabled unless a future milestone explicitly approves optional import/export use.
- Plugin/skill installers remain disabled due to supply-chain risk.
- Shell/exec commands are allowed narrowly for test, verifier, git, and explicitly scoped implementation workflows only.
