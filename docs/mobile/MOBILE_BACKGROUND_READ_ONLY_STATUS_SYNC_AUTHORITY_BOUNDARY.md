# Mobile Background Read-Only Status Sync Authority Boundary

M106 status sync reports are not authority.

They do not start background workers, schedule jobs, run daemons, request OS
background fetch, prompt for OS background permissions, trigger push delivery,
handle device tokens, call external services, perform network sync, expose raw
status payloads, write memory, inject context, execute tools, add routes, add
Control Center controls, add dependencies, or grant production authority.

Safe status refs and safe status summaries are review evidence only. They do
not authorize background collection, mobile runtime work, push execution,
network delivery, context injection, memory writes, broad autonomy, or M107.
