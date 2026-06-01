# Remote Node Security Model

M10.5 remote nodes are foundation-only metadata records. Risky node capabilities default false:

- job execution
- subagent launch
- tool calls
- sandbox use
- network access
- personal-data access
- file writes
- message sends
- action approval
- critical work
- background work

No live networking exists in this milestone.
No job dispatch exists in this milestone.
No remote approvals exist in this milestone.

Remote nodes cannot approve their own actions, cannot approve user approvals, and cannot convert credentials into consent. Unknown nodes are denied.

