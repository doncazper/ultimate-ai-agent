# Design Tooling Policy

Status: Active design governance for v0.18.3. Documentation only.

Design tools are development aids, not authority. Figma, Stitch, Framer, design-to-code tools, screenshot-to-code tools, and AI UI generator tools are not enabled by this milestone.

Policy:

- no design tools are enabled.
- future use requires explicit milestone approval.
- design SaaS cannot be source of truth.
- no external design sync.
- no automatic design sync.
- no automatic design-to-code.
- no automatic design-to-code commits.
- no design plugin enablement.
- design-to-code output must be reviewed like code.
- screenshots and design artifacts must not contain secrets.
- screenshots and design exports must not contain personal data, credentials, prompts, memory contents, file contents, receipts with sensitive data, private hostnames, private IPs, tokens, keys, or key material.

Tool governance mapping:

- `docs/canonical/66_external_tooling_and_codex_plugin_governance.md` governs external tooling authority.
- `docs/tooling/CODEX_PLUGIN_CAPABILITY_INVENTORY.md` records plugin capability classes.
- `docs/tooling/CODEX_PLUGIN_RISK_POLICY.md` classifies design tooling as future-only unless approved.
- `docs/backlog/codex_plugin_enablement_backlog.md` tracks future plugin lifecycle work.

Browser may be used only for local UI verification under the existing local browser smoke policy. Chrome authenticated profile control and Computer Use remain disabled. Build iOS Apps and Build macOS Apps remain disabled for design work.
