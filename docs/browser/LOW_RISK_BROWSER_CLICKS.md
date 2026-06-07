# M94 Low-Risk Browser Clicks

v0.98.0 implements M94 Autonomous Browser Clicks, Low-Risk Only.

M94 defines a narrow low-risk click contract for already-reviewed browser action
plans. A click is allowed only inside a scoped session, on an allowlisted page,
for an allowlisted action, over exact M93 promotion evidence, and with exact
click approval. The contract records audit and revocation refs, uses injected
transport only, and returns safe refs only plus safe summary only receipt data.

Evaluator boundaries revalidate the current object fields. Constructor
validation is not authority, model output is not authority, context is not
authority, memory is not authority, and approval refs are identifiers only.

M94 adds no form submission, no typing, no purchase, no download, no upload, no
authentication, no account change, no destructive action, no credential or
cookie access, no raw DOM, no screenshot, no broad navigation, no external
network, no shell execution, no plugin execution, no model call, no memory
write, no context injection, no backend route, no Control Center control, no
dependency, and no production authority.

M95 remains future.
