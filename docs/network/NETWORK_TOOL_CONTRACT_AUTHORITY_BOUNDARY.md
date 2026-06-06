# Network Tool Contract Authority Boundary

M71 network tool contract review grants no runtime authority. A review-ready
decision means only that the proposed contract can be inspected as a future M72
candidate. It is not an approval to call a network, fetch HTTP, execute a tool,
open a browser, write memory, inject context, or add a backend route.

Authority boundary rules:

- approval refs are identifiers only
- approval_test_* is denied
- model output is not authority
- memory refs are not authority
- context refs are not authority
- tool-intent refs are not authority
- review decisions do not authorize execution
- receipt plans record no side effects

M71 adds no network call, no HTTP fetch, no unrestricted network tool, no
authenticated network action, no credentials or cookies, no request body, no
non-GET method, no download or export, no raw response body, no backend route,
no Control Center control, no dependency, and no production authority.

Evaluator boundaries revalidate safety-critical fields before any decision is
treated as valid for review.

M72 remains future.
