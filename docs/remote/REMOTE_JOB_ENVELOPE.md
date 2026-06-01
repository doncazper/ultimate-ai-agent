# Remote Job Envelope

The M10.5 remote job envelope is a foundation-only dry-run contract. It carries IDs, summaries, requested capability names, audit refs, and metadata. It must not carry raw prompts, files, personal data, secrets, credentials, or executable payloads.

No live networking exists in this milestone.
No job dispatch exists in this milestone.
No remote approvals exist in this milestone.

Dry-run results must report:

- dispatch_performed=false
- remote_execution_performed=false
- subagent_launched=false
- tools_executed=[]
- network_connections_opened=[]
- output_trust_level=untrusted_remote_output

