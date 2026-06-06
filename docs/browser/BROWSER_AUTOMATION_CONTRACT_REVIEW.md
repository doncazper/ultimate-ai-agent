# M73 Browser Automation Contract Review

M73 implements Browser Automation Contract Review. It is contract-only,
review-only, disabled by default, deterministic, and non-authoritative.

M73 reviews future browser automation capability categories before any browser
runtime exists. The only review-ready candidate is a future M74 observe-only
adapter contract. M73 performs no browser automation and grants no browser
automation authority.

M73 allows:

- safe browser contract metadata.
- safe adapter refs.
- safe policy refs.
- safe risk refs.
- stable review decisions.
- stable reason codes.
- safe receipt plans.
- evaluator boundaries revalidate safety-critical fields.

M73 denies:

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

Approval refs, `approval_test_` refs, context refs, memory refs, tool-intent
refs, model-output refs, and arbitrary authority refs are identifiers only.
They cannot authorize browser automation.

M74 remains future.
