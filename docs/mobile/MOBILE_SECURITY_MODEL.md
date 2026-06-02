# Mobile Security Model

Status: Current M19 mobile security planning doc for v0.23.0.

Mobile Companion clients are control surfaces, not the agent brain. Python
Agent Core remains authority. M19 adds no mobile implementation, no Android
app, no iOS app, no native build workflow, no sensor access, no OS permission
integration, no signing, no keystore, no provisioning, no App Store workflow,
and no Play Store workflow.

Security boundaries:

- no secrets in browser, local, or mobile storage.
- no raw prompt display.
- no raw file display.
- no raw memory display.
- no raw credential display.
- no raw capture payload display.
- no mobile approval execution.
- no local mobile action execution.
- no background services.
- no external send.
- no silent capture.
- no silent memory write.

Mobile capture, phone output, and sensor output are not trusted source of truth.
Receipts and evidence refs are safe summaries only until future reviewed
milestones define stronger authority.
