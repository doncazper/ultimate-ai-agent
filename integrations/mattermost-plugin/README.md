# UAA Mattermost Agent Rooms Plugin

This package is the in-repo Mattermost server plugin scaffold for UAA Agent
Rooms. Mattermost is the room and bot surface; UAA remains the authority layer.

Initial local configuration:

```text
UAA_MATTERMOST_BRIDGE_ENABLED=1
UAA_MATTERMOST_BRIDGE_BEARER=<local bridge bearer>
UAA_MATTERMOST_REPLY_ENABLED=1
```

The plugin registers `/uaa`, observes committed posts, ignores bot/self messages,
deduplicates post IDs, sends bounded message previews to UAA, and posts returned
reply commands as configured role bots.

Current slice limitations:

- Slash commands return local ephemeral acknowledgements only; authoritative
  role binding, trigger changes, and disable operations remain UAA API flows.
- Role bot accounts are mapped through explicit local plugin settings. Automatic
  bot creation/`EnsureBot` lifecycle management is reserved for a later reviewed
  slice.
- Empty allowed channel configuration means no channels send events to UAA.

Development notes:

- Mattermost plugins are manifest-defined and may include a Go server component.
- The server component uses Mattermost hooks such as `MessageHasBeenPosted`.
- Bot posting should use plugin-managed bot users and the Mattermost Plugin API.
- The plugin must not store UAA bearer values in logs, send full transcripts to
  UAA, or bypass UAA approvals for tool/capability actions.
