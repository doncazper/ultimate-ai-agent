# Open Design System

Status: Active design governance for v0.19.0. Documentation only.

Open Design for Ultimate AI Agent means the design source of truth lives in this repository: reviewed documentation, reviewed component code, and future repo-owned design tokens. Proprietary canvases, screenshots, AI UI generators, design-to-code systems, and design SaaS exports may assist future review, but they are not authority.

Open Design does not replace OpenWebUI. OpenWebUI remains the preferred conversational web shell. Open Design governs custom CCC surfaces: CCC Web, CCC iOS, CCC Android, and CCC macOS.

The Control Center and future Mobile Companion should share these principles:

- operational interfaces before marketing surfaces.
- user control, consent, safety, receipts, and status clarity before decoration.
- status, risk, authority, and non-authoritative states must be visible in text.
- planned, disabled, blocked, simulated, dry-run, manual-only, validation-only, preview-only, and read-only states must not look executable.
- design artifacts must be reviewed like docs or code.

Repo-owned source of truth:

- `docs/design/*` defines design principles and governance.
- reviewed Control Center components define current implementation reality.
- future tokens should be stored in the repo, inspectable, portable, and reviewed.
- canonical docs, API contracts, verifier scripts, and Foundation Gate outrank design tools.

Tooling boundary:

- no design tools are enabled by this milestone.
- no design SaaS is authority.
- no design SaaS dependency is added.
- no external design sync is enabled.
- no automatic design-to-code is allowed.
- no automatic design-to-code commit is allowed.
- no design plugin enablement is allowed.

Open-source, self-hosted, portable, and inspectable workflows should be evaluated first where practical. Vendor tools such as Figma, Stitch, Framer, screenshot-to-code, design-to-code, or AI UI generators may be evaluated later only as optional import/export aids under an explicit future milestone.

v0.18.2 adds no UI behavior, frontend route, backend API route, runtime execution, model/provider call, remote execution, mobile sensor access, plugin enablement, dependency, design-tool integration, or production Control Center authority.
