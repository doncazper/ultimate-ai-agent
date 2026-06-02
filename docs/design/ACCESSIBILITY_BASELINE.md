# Accessibility Baseline

Status: Active design governance for v0.19.1. Documentation only.

The Control Center must be understandable by keyboard, screen reader, and visual inspection. Safety state must not depend on color alone.

Baseline requirements:

- semantic headings in route order.
- keyboard navigation for links, forms, and controls.
- visible focus indicators.
- visible disabled states that do not imply availability.
- readable contrast for text, status badges, alerts, and controls.
- status text must not be color-only.
- responsive layouts must not overlap text or controls.
- horizontal overflow is allowed only for intentional tables or code-like content.
- reduced motion preference should be respected before adding motion.
- no hidden action controls.
- explicit action labels.
- safe and redacted errors.
- accessible loading states with `role="status"` or equivalent.
- accessible empty states that explain absence without suggesting failure authority.
- accessible error states with `role="alert"` when action is needed.
- no dark-pattern approval UI.
- no deceptive disabled controls.

Approval and preview surfaces must clearly state when no action occurred. Future M15 approval, receipt, and event UI must preserve this baseline before implementation.
