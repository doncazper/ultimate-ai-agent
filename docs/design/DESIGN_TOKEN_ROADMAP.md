# Design Token Roadmap

Status: Future roadmap for v0.18.2. Documentation only.

Future tokens should be repo-owned, inspectable, portable, reviewed, and generated only from reviewed source files. No package dependency, Tailwind dependency, shadcn dependency, design system package, icon pack, or animation library is added by v0.18.2.

Future token groups:

- color roles: surface, text, border, accent, warning, danger, success, info, muted, focus.
- typography roles: page title, section title, panel title, body, caption, badge, code.
- spacing roles: page, section, panel, control, list, inline, table.
- radius roles: control, panel, badge, modal, table.
- elevation/shadow roles: none, raised, overlay, focus.
- status/risk tokens: safe, low, medium, high, critical, forbidden, read-only, preview-only, blocked, planned, disabled, degraded, mock.
- density levels: compact, standard, review.
- motion tokens: none, subtle, attention, reduced-motion fallback.
- focus tokens: ring color, ring width, offset, high-contrast alternative.
- layout/breakpoint tokens: narrow, tablet, desktop, wide, table-scroll threshold.

Implementation rules:

- no token implementation is added unless already present.
- no package dependency is added.
- no Tailwind or shadcn dependency is added.
- no design SaaS export is authoritative.
- future tokens should be stored in repo source and covered by review/verifier rules.
