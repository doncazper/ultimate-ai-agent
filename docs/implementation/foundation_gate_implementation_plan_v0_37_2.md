# Foundation Gate Implementation Plan v0.37.2

Status: active Foundation Gate plan.
Current active baseline: **v0.37.2**

v0.37.2 adds Foundation Gate and static verifier coverage for the local
developer launcher tooling.

Gate-adjacent coverage includes:

- local developer launcher docs exist.
- launcher command wrapper and Python launcher exist.
- launcher binds backend and frontend commands to `127.0.0.1` only.
- launcher rejects `0.0.0.0` and non-loopback hosts.
- launcher uses subprocess argument lists and does not use `shell=True`.
- launcher state is ignored under `.uaa/`.
- macOS `.command` template generation avoids production installer, `sudo`,
  launch daemon, and `/usr/local/bin` behavior.
- no backend routes are added.
- no Control Center execute controls are added.
- no dependencies are added.
- OpenAPI path count remains `74`.
- M34 remains planned/provisional.

## Skill Package Security Rule

Skill Package Security Rule remains in force. All skills are untrusted packages by default.
Any future skill package must have a manifest, declared permissions,
source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping,
Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities
before any future enablement.

v0.37.2 adds no production installer, backend route, task/action/tool execution,
model/provider call, memory write, filesystem mutation beyond launcher-local
PID/log files, dependency, M34 work, or production authority.
