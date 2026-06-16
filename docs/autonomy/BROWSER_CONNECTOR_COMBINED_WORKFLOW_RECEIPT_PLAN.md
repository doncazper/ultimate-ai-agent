# M137 Receipt Plan

M137 receipt plans are no-effect receipt plans. They store safe summaries, safe
refs, browser action plan refs, connector action plan refs, workflow step refs,
and dependency order refs only.

M137 receipts must not store raw browser DOM, raw connector payloads, raw
prompts, raw provider payloads, cookies, credentials, secrets, browser action
results, connector action results, combined workflow runtime output, dependency
execution output, tool output, shell output, network payloads, model payloads,
memory writes, context injection material, or production authority evidence.

Receipt plans exist only so reviewers can verify the declared no-effect M137
contract.
