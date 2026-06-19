# M167 Live Model Production Hardening Non-Goals

M167 does not grant new production authority. It depends on M166 for production
authority and only hardens the evidence required to keep that authority honest.

M167 does not add:

- backend routes
- Control Center controls
- dependencies
- OpenWebUI admin behavior
- OpenWebUI plugin installation
- model/provider calls from the report builder
- llama.cpp process launch from the report builder
- model download from the report builder
- unrestricted web fetching
- raw prompt export
- raw response export
- raw provider payload export
- credential export
- raw local path export
- raw log export
- username export
- env dump export
- unreviewed side effects

Generated fixture evidence is non-authoritative. It exists only to exercise the
contract. M167 passes only when actual live evidence is reviewed live evidence
and every required hardware profile and hardening lane is bound to safe refs.

