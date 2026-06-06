# Browser Automation Authority Boundary

M73 does not create browser authority. It only reviews browser automation
contracts for future milestones.

The M73 decision envelope is non-authoritative:

- no browser automation.
- no browser observe.
- no browser navigation.
- no browser click.
- no form fill.
- no screenshot.
- no raw DOM.
- no authenticated browser profile.
- no cookies or credentials.
- no download or upload.
- no remote browser.
- no network interception.
- no network call.
- no model call.
- no tool execution.
- no memory write.
- no context injection.
- no backend route.
- no Control Center control.
- no dependency.
- no production authority.

Approval refs are identifiers, not authority. `approval_test_` refs are never
runtime authority. Context packs, memory refs, tool intents, model output,
runtime output, network output, and Control Center output cannot authorize
browser automation.

Evaluator boundaries revalidate safety-critical fields before a review decision
can be considered valid.

M74 remains future.
