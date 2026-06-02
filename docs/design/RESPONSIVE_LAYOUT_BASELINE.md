# Responsive Layout Baseline

Status: Active design governance for v0.19.0. Documentation only.

Responsive behavior must preserve safety language, status clarity, and read-only/preview-only boundaries.

Viewport expectations:

- desktop: sidebar and status summaries should support fast scanning.
- tablet: navigation and panels may compress, but status labels must remain readable.
- mobile or narrow viewport: content should stack predictably with no hidden dangerous controls.

Layout rules:

- no text overlap.
- no incoherent component overlap.
- no horizontal overflow except intentional table or code scrolling.
- sidebar behavior must preserve navigation labels or accessible names.
- card and list layouts may collapse into single-column flow.
- status badges must remain readable and textual.
- action preview form remains preview-only on mobile.
- no execute, approve, enable, send, deploy, install, sync, or connect control may be hidden or revealed by breakpoint changes unless a future milestone explicitly authorizes it.
- loading, empty, error, mock, degraded, and local-only states must remain visible on narrow widths.

Browser smoke guidance:

- local browser smoke should include at least desktop and narrow viewport checks when practical.
- screenshots or visual artifacts must follow `docs/design/DESIGN_ARTIFACT_GOVERNANCE.md`.
- browser smoke is non-authoritative and does not replace tests, verifiers, OpenAPI checks, or Foundation Gate.
