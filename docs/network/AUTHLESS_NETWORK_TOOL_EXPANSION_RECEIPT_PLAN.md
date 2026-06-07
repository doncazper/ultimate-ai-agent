# Authless Network Tool Expansion Receipt Plan

M95 receipt plans store safe refs only and redacted preview only. They may identify the request ref, scoped session ref, scope ref, target host ref, target path ref, audit ref, and revocation ref.

Receipt plans do not store raw network responses, raw headers, credential headers, cookies, query strings, request body, account action data, provider model payloads, shell output, plugin output, memory writes, context injection payloads, downloads, exports, or side effects.

Receipt plans preserve audit and revocation reviewability without becoming authority. Evaluator boundaries revalidate receipt fields before accepting a decision. M96 remains future.
