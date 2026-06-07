# M94 Low-Risk Browser Click Receipt Plan

The M94 receipt plan stores safe refs only and safe summary only metadata for a
low-risk click. It binds the click ref, exact M93 promotion decision ref, exact
click approval ref, scoped session ref, allowlisted page ref, allowlisted action
ref, safe target ref, audit ref, replay ref, and revocation ref.

Receipt data must not store raw DOM, screenshots, browser state handles, raw
prompt data, raw provider payloads, or secret-like values. Evaluator boundaries
revalidate receipt fields and deny model_copy-mutated receipt plans that hide
unsafe browser activity.

The receipt plan records no form submission, no typing, no purchase, no
download, no upload, no authentication, no account change, no destructive
action, no credential or cookie access, no raw DOM, no screenshot, no broad
navigation, no external network, no shell execution, no plugin execution, no
model call, no memory write, no context injection, no backend route, no Control
Center control, no dependency, and no production authority.

M95 remains future.
