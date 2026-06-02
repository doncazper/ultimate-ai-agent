# Component Taxonomy

Status: Active design governance for v0.19.0. Documentation only.

This taxonomy names current and future Control Center component classes. It does not implement new components.

| Component | Purpose | Allowed behavior | Must not do | Accessibility and safety notes |
| --- | --- | --- | --- | --- |
| AppShell | Frame navigation and page chrome. | Show navigation, safety status, and page content. | Execute actions or imply production authority. | Landmark structure, keyboard navigation, visible read-only status. |
| Navigation | Move between local shell routes. | Link to documented frontend pages. | Hide execution controls or add undocumented routes. | Clear labels and current-page state. |
| StatusCard | Summarize one status item. | Show label, status, summary. | Use color-only status. | Text status and compact readable layout. |
| SummaryPanel | Group related status summaries. | Present read-only summaries. | Mutate state. | Semantic headings and list/table clarity. |
| RiskBadge | Show risk level. | Display safe, low, medium, high, critical, or forbidden. | Soften critical/forbidden states. | Text label required. |
| StatusBadge | Show capability state. | Display read-only, preview-only, validation-only, dry-run-only, simulated-only, planned, disabled, blocked, degraded, mock, local-only. | Use enabled language for disabled/planned states. | Text label required. |
| ReadOnlyTable | Scan route, event, receipt, or capability rows. | Display redacted data with optional table scrolling. | Inline execute or approve actions. | Header cells, row labels, responsive scroll. |
| DetailPanel | Inspect selected item details. | Show redacted read-only fields. | Resolve credentials or expose secrets. | Structured headings and safe empty/error states. |
| PreviewForm | Collect preview-only request metadata. | Submit only approved preview endpoints. | Execute, approve, send, deploy, enable, install, sync, or connect. | Explicit no-action copy and safe errors. |
| SafeAlert | Surface important safety state. | Announce info, warning, or danger states. | Hide risk behind color only. | `role="status"` or `role="alert"` as appropriate. |
| LoadingState | Show pending local checks. | Explain what is loading. | Hide indefinite blocked state. | Accessible status text. |
| EmptyState | Explain absence of data. | State what is unavailable. | Suggest future/planned features are available. | Accessible status text. |
| ErrorState | Show sanitized failure. | Display safe redacted error. | Echo secrets or raw invalid input. | Alert role when user attention is needed. |
| MockDataBanner | Identify mock fallback. | Mark mock and non-authoritative. | Let mock look live. | Text label and explanation. |
| ConnectionStateBanner | Show local backend state. | Show unknown, checking, online, degraded, offline, or mock fallback. | Treat connected/online as authority or readiness. | Text state and local-only wording. |
| BlockedCapabilityNotice | Explain blocked capability. | State reason and boundary. | Offer bypass control. | Text reason and no dark pattern. |
| PlannedCapabilityNotice | Explain future capability. | Mark future/not implemented. | Present as enabled. | Visible planned/disabled copy. |
| NonAuthoritativeNotice | Mark data that cannot prove truth. | Explain limitation. | Let model/mock/simulated output become authority. | Text notice near affected content. |
| ReceiptSummaryCard | Future M15 receipt summary. | Read-only redacted receipt summary. | Expose secrets or execute follow-up action. | Must follow M15 review and redaction rules. |
| EventSummaryCard | Future M15/M16 event summary. | Read-only redacted event summary. | Trigger replay or dispatch. | Must preserve event/source context. |
| ApprovalSummaryCard | Future M15 approval summary. | Read-only approval status and details. | Grant approval or treat arbitrary refs as authority. | No dark patterns; Approval Authority remains backend/core. |
