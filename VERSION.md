# Ultimate AI Agent Version

Current active baseline: **v0.12.1**

v0.12.1 hardens the M8 API validation boundary so FastAPI/Pydantic validation errors do not echo raw invalid input values or secret-like fields. It keeps the M8 simulated model runtime adapter harness dry-run only and adds Foundation Gate coverage for API validation secret-echo regressions.
