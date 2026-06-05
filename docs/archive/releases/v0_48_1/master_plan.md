# v0.48.1 Master Plan

## Scope

Repair the M44 release verifier mismatch found during pushed-release review of
v0.48.0.

## Changes

- Add a narrow M44 source-only skeleton allowance to the historical frontend
  artifact verifier.
- Keep `Package.swift`, Xcode projects, Info.plist, entitlements, native build
  workflow, signing/store workflow, TestFlight, sensors, permission integration,
  approvals, context injection, memory writes, file mutation, and execution
  blocked.
- Add regression coverage for the verifier allowance.
- Update active baseline metadata and release documentation for v0.48.1.

## Non-Goals

v0.48.1 does not start M45. It adds no local iOS connection, backend routes,
mobile runtime, network calls, native build workflow, signing workflow,
TestFlight pipeline, approval capture, approval execution, context injection,
memory write, file mutation, execution, dependencies, or production authority.
