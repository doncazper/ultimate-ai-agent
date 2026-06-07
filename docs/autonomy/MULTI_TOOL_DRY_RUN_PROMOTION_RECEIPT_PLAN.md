# Multi-Tool Dry-Run Promotion Receipt Plan

M93 receipt plans store safe refs only, safe summary only, and plan hash refs only. They do not store raw tool payload, raw provider payload, raw prompt, secrets, dry-run payload bodies, real-run payload bodies, or execution output.

The receipt binds the promotion ref, exact M92 decision ref, promotion approval ref, dry-run plan ref, dry-run plan hash ref, real-run plan ref, real-run plan hash ref, and safe tool refs.

The receipt records no unapproved real execution, no real-run execution, no tool execution, no autonomous execution, no session start, no background worker, no backend route, no Control Center control, no dependency, and no production authority.

Evaluator boundaries revalidate receipt fields. M94 remains future.
