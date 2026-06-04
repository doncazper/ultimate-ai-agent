# Ultimate AI Agent Version

Current active baseline: **v0.37.2**

v0.37.2 adds a local developer launcher for prototype testing. It provides
terminal commands for doctor, start, ui, status, logs, stop, and restart, plus
a macOS .command launcher generator for opening the local Control Center.

It is localhost-only and developer-only, stores only local PID/log files under
ignored launcher state, and adds no production installer, backend routes,
tool/action execution, model/provider calls, memory writes, filesystem mutation
beyond launcher-local PID/log files, dependencies, M34 work, or production
authority.
