# M145 Authority Boundary

M145 is safety-mode policy authority only. It can validate safe refs and record
a no-effect safety mode record for review.

M145 must not start enterprise runtime, start pro runtime, enforce plans,
implement billing, define a billing plan boundary, start account tenant runtime,
start role runtime, share workspaces, start auth runtime, perform login, handle
credentials, start connector runtime, start plugin marketplace runtime, execute
actions, add backend routes, add Control Center controls, add dependencies,
start beta release, or grant production authority.

Enterprise and Pro refs remain policy refs only. They do not grant plan
enforcement, account runtime, billing authority, or production authority.
