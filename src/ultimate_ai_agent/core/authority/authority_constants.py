AUTHORITY_STATE_LOCK_KEY = "authority-state"
AUTHORITY_BUDGET_RECEIPTS_FILE = "authority_budget_receipts.jsonl"
AUTHORITY_DISPATCH_RECEIPTS_FILE = "authority_dispatch_receipts.jsonl"
AUTHORITY_STATE_REDACTIONS = (
    "safe_refs_only",
    "bounded_summaries_only",
    "raw_prompt_omitted",
    "raw_response_omitted",
    "raw_log_omitted",
    "local_paths_omitted",
    "provider_payload_omitted",
    "credentials_omitted",
)

PORTABLE_EVIDENCE_SIGN_TOOL_REF = "tool-ref:portable-evidence-sign:v1"
PORTABLE_EVIDENCE_KEY_CREATE_TOOL_REF = "tool-ref:portable-evidence-key-create:v1"
PORTABLE_EVIDENCE_KEY_ROTATE_TOOL_REF = "tool-ref:portable-evidence-key-rotate:v1"
PORTABLE_EVIDENCE_KEY_REVOKE_TOOL_REF = "tool-ref:portable-evidence-key-revoke:v1"
PORTABLE_EVIDENCE_KEY_MARK_LOST_TOOL_REF = "tool-ref:portable-evidence-key-mark-lost:v1"
PORTABLE_EVIDENCE_KEY_CLEANUP_TOOL_REF = (
    "tool-ref:portable-evidence-key-material-cleanup:v1"
)

MATRIX_HARNESS_INSPECT_TOOL_REF = "tool-ref:matrix-harness-inspect:v1"
MATRIX_HARNESS_SMOKE_TOOL_REF = "tool-ref:matrix-harness-smoke:v1"
MATRIX_HARNESS_START_TOOL_REF = "tool-ref:matrix-harness-start:v1"
MATRIX_HARNESS_FIXTURE_SEED_TOOL_REF = "tool-ref:matrix-harness-fixture-seed:v1"
MATRIX_HARNESS_STOP_TOOL_REF = "tool-ref:matrix-harness-stop:v1"
MATRIX_HARNESS_RESET_TOOL_REF = "tool-ref:matrix-harness-reset:v1"

MATRIX_DISCOVERY_READ_TOOL_REF = "tool-ref:matrix-discovery-read:v1"
MATRIX_AUTH_METHODS_READ_TOOL_REF = "tool-ref:matrix-auth-methods-read:v1"
MATRIX_SESSION_CREDENTIAL_AUTH_CREATE_TOOL_REF = (
    "tool-ref:matrix-session-credential-auth-create:v1"
)
MATRIX_SESSION_SSO_LAUNCH_TOOL_REF = "tool-ref:matrix-session-sso-launch:v1"
MATRIX_SESSION_SSO_CALLBACK_TOOL_REF = "tool-ref:matrix-session-sso-callback-consume:v1"
MATRIX_SESSION_REFRESH_TOOL_REF = "tool-ref:matrix-session-refresh:v1"
MATRIX_SESSION_LOGOUT_TOOL_REF = "tool-ref:matrix-session-logout:v1"
MATRIX_SESSION_REVOKE_ALL_TOOL_REF = "tool-ref:matrix-session-revoke-all:v1"
MATRIX_CREDENTIAL_STORE_ROTATE_TOOL_REF = "tool-ref:matrix-credential-store-rotate:v1"
MATRIX_CREDENTIAL_DELETE_TOOL_REF = "tool-ref:matrix-credential-delete:v1"

MATRIX_SYNC_READ_TOOL_REF = "tool-ref:matrix-sync-read:v1"
MATRIX_TIMELINE_PAGINATE_READ_TOOL_REF = "tool-ref:matrix-timeline-paginate-read:v1"
MATRIX_ROOM_STATE_READ_TOOL_REF = "tool-ref:matrix-room-state-read:v1"
MATRIX_RECEIPT_PROJECT_READ_TOOL_REF = "tool-ref:matrix-receipt-project-read:v1"
MATRIX_TYPING_PROJECT_READ_TOOL_REF = "tool-ref:matrix-typing-project-read:v1"
MATRIX_CACHE_READ_TOOL_REF = "tool-ref:matrix-cache-read:v1"
MATRIX_CACHE_WRITE_TOOL_REF = "tool-ref:matrix-cache-write:v1"
MATRIX_CACHE_MIGRATE_TOOL_REF = "tool-ref:matrix-cache-migrate:v1"
MATRIX_CACHE_PURGE_TOOL_REF = "tool-ref:matrix-cache-purge:v1"
MATRIX_CACHE_KEY_CREATE_TOOL_REF = "tool-ref:matrix-cache-key-create:v1"
MATRIX_CACHE_KEY_ROTATE_TOOL_REF = "tool-ref:matrix-cache-key-rotate:v1"
MATRIX_CACHE_KEY_DELETE_TOOL_REF = "tool-ref:matrix-cache-key-delete:v1"

# Exact MSG-MX-008 human-commanded messaging tools. These are lane identifiers,
# not standing connector authority.
MATRIX_MESSAGING_OPERATIONS = (
    "send",
    "reply",
    "thread",
    "reaction",
    "edit",
    "redaction",
    "typing",
    "read_receipt",
    "draft_write",
    "draft_read",
    "outbox_enqueue",
    "outbox_read",
    "outbox_transition",
    "outbox_discard",
    "desktop_notify",
)

# Exact MSG-MX-009 room, local-search, and media lanes. These remain
# request-scoped bindings; they are not connector-wide room or filesystem
# authority.
MATRIX_ROOMS_MEDIA_BINDING_SPECS = (
    ("dm_create", "messages", "mutate", "ask_before_changes"),
    ("room_create", "messages", "mutate", "ask_before_changes"),
    ("room_join", "messages", "mutate", "ask_before_changes"),
    ("room_leave", "messages", "destructive", "full_machine_access_session"),
    ("invite_send", "messages", "admin", "ask_before_changes"),
    ("invite_accept", "messages", "mutate", "ask_before_changes"),
    ("invite_reject", "messages", "destructive", "full_machine_access_session"),
    ("invite_withdraw", "messages", "admin", "ask_before_changes"),
    ("room_power_role_write", "messages", "admin", "ask_before_changes"),
    ("space_mapping_write", "messages", "admin", "ask_before_changes"),
    ("notification_settings_write", "messages", "mutate", "ask_before_changes"),
    ("history_visibility_write", "messages", "admin", "ask_before_changes"),
    ("pin_write", "messages", "mutate", "ask_before_changes"),
    ("account_room_preference_write", "messages", "mutate", "ask_before_changes"),
    ("search_local_read", "messages", "read", "ask_before_changes"),
    ("media_upload", "messages", "upload", "ask_before_changes"),
    ("media_download_quarantine", "messages", "download", "ask_before_changes"),
    ("media_materialize", "files", "write", "ask_before_changes"),
    ("media_preview", "files", "read", "ask_before_changes"),
    ("media_cleanup", "files", "destructive", "full_machine_access_session"),
)

# Exact lane bindings accepted by the generic AuthorityLease store. Keeping
# these bindings in the authority package prevents the coarse ``messages``
# domain from becoming a standing grant for future connector or send lanes.
MATRIX_HARNESS_EXACT_AUTHORITY_BINDINGS = (
    (
        "read",
        "authority-lane-ref:matrix-harness-inspect",
        "authority-capability-ref:matrix-harness-inspect-v1",
        "authority-adapter-ref:matrix-harness-inspect-v1",
        MATRIX_HARNESS_INSPECT_TOOL_REF,
    ),
    (
        "read",
        "authority-lane-ref:matrix-harness-smoke",
        "authority-capability-ref:matrix-harness-smoke-v1",
        "authority-adapter-ref:matrix-harness-smoke-v1",
        MATRIX_HARNESS_SMOKE_TOOL_REF,
    ),
    (
        "execute",
        "authority-lane-ref:matrix-harness-start",
        "authority-capability-ref:matrix-harness-start-v1",
        "authority-adapter-ref:matrix-harness-start-v1",
        MATRIX_HARNESS_START_TOOL_REF,
    ),
    (
        "mutate",
        "authority-lane-ref:matrix-harness-fixture-seed",
        "authority-capability-ref:matrix-harness-fixture-seed-v1",
        "authority-adapter-ref:matrix-harness-fixture-seed-v1",
        MATRIX_HARNESS_FIXTURE_SEED_TOOL_REF,
    ),
    (
        "execute",
        "authority-lane-ref:matrix-harness-stop",
        "authority-capability-ref:matrix-harness-stop-v1",
        "authority-adapter-ref:matrix-harness-stop-v1",
        MATRIX_HARNESS_STOP_TOOL_REF,
    ),
    (
        "mutate",
        "authority-lane-ref:matrix-harness-reset",
        "authority-capability-ref:matrix-harness-reset-v1",
        "authority-adapter-ref:matrix-harness-reset-v1",
        MATRIX_HARNESS_RESET_TOOL_REF,
    ),
)

# Exact session-scoped connector bindings accepted by MSG-MX-005. Tuple fields
# are: authority domain, authority capability, lease scope, required trust mode,
# lane ref, capability ref, adapter ref, and tool ref. These records are an
# allowlist, not a broad Matrix or messages authority switch.
MATRIX_SESSION_EXACT_AUTHORITY_BINDINGS = (
    (
        "messages",
        "read",
        "session",
        "read_only",
        "authority-lane-ref:matrix-discovery-read",
        "authority-capability-ref:matrix-discovery-read-v1",
        "authority-adapter-ref:matrix-discovery-read-v1",
        MATRIX_DISCOVERY_READ_TOOL_REF,
    ),
    (
        "messages",
        "read",
        "session",
        "read_only",
        "authority-lane-ref:matrix-auth-methods-read",
        "authority-capability-ref:matrix-auth-methods-read-v1",
        "authority-adapter-ref:matrix-auth-methods-read-v1",
        MATRIX_AUTH_METHODS_READ_TOOL_REF,
    ),
    (
        "messages",
        "mutate",
        "session",
        "ask_before_changes",
        "authority-lane-ref:matrix-session-credential-auth-create",
        "authority-capability-ref:matrix-session-credential-auth-create-v1",
        "authority-adapter-ref:matrix-session-credential-auth-create-v1",
        MATRIX_SESSION_CREDENTIAL_AUTH_CREATE_TOOL_REF,
    ),
    (
        "browser",
        "execute",
        "session",
        "ask_before_changes",
        "authority-lane-ref:matrix-session-sso-launch",
        "authority-capability-ref:matrix-session-sso-launch-v1",
        "authority-adapter-ref:matrix-session-sso-launch-v1",
        MATRIX_SESSION_SSO_LAUNCH_TOOL_REF,
    ),
    (
        "messages",
        "mutate",
        "session",
        "ask_before_changes",
        "authority-lane-ref:matrix-session-sso-callback-consume",
        "authority-capability-ref:matrix-session-sso-callback-consume-v1",
        "authority-adapter-ref:matrix-session-sso-callback-consume-v1",
        MATRIX_SESSION_SSO_CALLBACK_TOOL_REF,
    ),
    (
        "messages",
        "mutate",
        "session",
        "ask_before_changes",
        "authority-lane-ref:matrix-session-refresh",
        "authority-capability-ref:matrix-session-refresh-v1",
        "authority-adapter-ref:matrix-session-refresh-v1",
        MATRIX_SESSION_REFRESH_TOOL_REF,
    ),
    (
        "messages",
        "mutate",
        "session",
        "ask_before_changes",
        "authority-lane-ref:matrix-session-logout",
        "authority-capability-ref:matrix-session-logout-v1",
        "authority-adapter-ref:matrix-session-logout-v1",
        MATRIX_SESSION_LOGOUT_TOOL_REF,
    ),
    (
        "messages",
        "destructive",
        "session",
        "full_machine_access_session",
        "authority-lane-ref:matrix-session-revoke-all",
        "authority-capability-ref:matrix-session-revoke-all-v1",
        "authority-adapter-ref:matrix-session-revoke-all-v1",
        MATRIX_SESSION_REVOKE_ALL_TOOL_REF,
    ),
    (
        "system_settings",
        "write",
        "session",
        "ask_before_changes",
        "authority-lane-ref:matrix-credential-store-rotate",
        "authority-capability-ref:matrix-credential-store-rotate-v1",
        "authority-adapter-ref:matrix-credential-store-rotate-v1",
        MATRIX_CREDENTIAL_STORE_ROTATE_TOOL_REF,
    ),
    (
        "system_settings",
        "destructive",
        "session",
        "full_machine_access_session",
        "authority-lane-ref:matrix-credential-delete",
        "authority-capability-ref:matrix-credential-delete-v1",
        "authority-adapter-ref:matrix-credential-delete-v1",
        MATRIX_CREDENTIAL_DELETE_TOOL_REF,
    ),
)

# Exact MSG-MX-006 read-only sync and protected-cache bindings. These entries
# make each lane eligible for request-scoped lease evaluation; they are not a
# connector-wide read switch and do not include any external write capability.
MATRIX_SYNC_EXACT_AUTHORITY_BINDINGS = (
    (
        "messages",
        "read",
        "session",
        "read_only",
        "authority-lane-ref:matrix-sync-read",
        "authority-capability-ref:matrix-sync-read-v1",
        "authority-adapter-ref:matrix-sync-read-v1",
        MATRIX_SYNC_READ_TOOL_REF,
    ),
    (
        "messages",
        "read",
        "session",
        "read_only",
        "authority-lane-ref:matrix-timeline-paginate-read",
        "authority-capability-ref:matrix-timeline-paginate-read-v1",
        "authority-adapter-ref:matrix-timeline-paginate-read-v1",
        MATRIX_TIMELINE_PAGINATE_READ_TOOL_REF,
    ),
    (
        "messages",
        "read",
        "session",
        "read_only",
        "authority-lane-ref:matrix-room-state-read",
        "authority-capability-ref:matrix-room-state-read-v1",
        "authority-adapter-ref:matrix-room-state-read-v1",
        MATRIX_ROOM_STATE_READ_TOOL_REF,
    ),
    (
        "messages",
        "read",
        "session",
        "read_only",
        "authority-lane-ref:matrix-receipt-project-read",
        "authority-capability-ref:matrix-receipt-project-read-v1",
        "authority-adapter-ref:matrix-receipt-project-read-v1",
        MATRIX_RECEIPT_PROJECT_READ_TOOL_REF,
    ),
    (
        "messages",
        "read",
        "session",
        "read_only",
        "authority-lane-ref:matrix-typing-project-read",
        "authority-capability-ref:matrix-typing-project-read-v1",
        "authority-adapter-ref:matrix-typing-project-read-v1",
        MATRIX_TYPING_PROJECT_READ_TOOL_REF,
    ),
    (
        "messages",
        "read",
        "session",
        "read_only",
        "authority-lane-ref:matrix-cache-read",
        "authority-capability-ref:matrix-cache-read-v1",
        "authority-adapter-ref:matrix-cache-read-v1",
        MATRIX_CACHE_READ_TOOL_REF,
    ),
    (
        "messages",
        "mutate",
        "session",
        "ask_before_changes",
        "authority-lane-ref:matrix-cache-write",
        "authority-capability-ref:matrix-cache-write-v1",
        "authority-adapter-ref:matrix-cache-write-v1",
        MATRIX_CACHE_WRITE_TOOL_REF,
    ),
    (
        "messages",
        "mutate",
        "session",
        "ask_before_changes",
        "authority-lane-ref:matrix-cache-migrate",
        "authority-capability-ref:matrix-cache-migrate-v1",
        "authority-adapter-ref:matrix-cache-migrate-v1",
        MATRIX_CACHE_MIGRATE_TOOL_REF,
    ),
    (
        "messages",
        "destructive",
        "session",
        "full_machine_access_session",
        "authority-lane-ref:matrix-cache-purge",
        "authority-capability-ref:matrix-cache-purge-v1",
        "authority-adapter-ref:matrix-cache-purge-v1",
        MATRIX_CACHE_PURGE_TOOL_REF,
    ),
    (
        "system_settings",
        "write",
        "session",
        "ask_before_changes",
        "authority-lane-ref:matrix-cache-key-create",
        "authority-capability-ref:matrix-cache-key-create-v1",
        "authority-adapter-ref:matrix-cache-key-create-v1",
        MATRIX_CACHE_KEY_CREATE_TOOL_REF,
    ),
    (
        "system_settings",
        "write",
        "session",
        "ask_before_changes",
        "authority-lane-ref:matrix-cache-key-rotate",
        "authority-capability-ref:matrix-cache-key-rotate-v1",
        "authority-adapter-ref:matrix-cache-key-rotate-v1",
        MATRIX_CACHE_KEY_ROTATE_TOOL_REF,
    ),
    (
        "system_settings",
        "destructive",
        "session",
        "full_machine_access_session",
        "authority-lane-ref:matrix-cache-key-delete",
        "authority-capability-ref:matrix-cache-key-delete-v1",
        "authority-adapter-ref:matrix-cache-key-delete-v1",
        MATRIX_CACHE_KEY_DELETE_TOOL_REF,
    ),
)

# Exact MSG-MX-007 crypto/device/backup/recovery authority bindings. This is an
# allowlist for request-scoped evaluation only. Every corresponding action is
# still marked unsupported until a persistent, fenced Rust-crypto broker exists.
_MATRIX_CRYPTO_BINDING_SPECS = (
    ("crypto_store_initialize", "system_settings", "mutate", "ask_before_changes"),
    ("crypto_store_key_rotate", "system_settings", "mutate", "ask_before_changes"),
    (
        "crypto_store_key_delete",
        "system_settings",
        "destructive",
        "full_machine_access_session",
    ),
    ("verification_request", "messages", "mutate", "ask_before_changes"),
    ("verification_cancel", "messages", "mutate", "ask_before_changes"),
    ("verification_confirm", "messages", "mutate", "ask_before_changes"),
    ("device_revoke", "system_settings", "destructive", "full_machine_access_session"),
    ("cross_signing_bootstrap", "messages", "mutate", "ask_before_changes"),
    ("backup_status_read", "messages", "read", "read_only"),
    ("backup_configure", "messages", "mutate", "ask_before_changes"),
    ("backup_rotate", "messages", "mutate", "ask_before_changes"),
    ("recovery_restore", "system_settings", "mutate", "ask_before_changes"),
    ("identity_reset", "system_settings", "destructive", "full_machine_access_session"),
    ("local_backup_create", "system_settings", "mutate", "ask_before_changes"),
    ("local_backup_restore", "system_settings", "mutate", "ask_before_changes"),
    (
        "local_backup_delete",
        "system_settings",
        "destructive",
        "full_machine_access_session",
    ),
    (
        "local_backup_expiry_reconcile",
        "system_settings",
        "destructive",
        "full_machine_access_session",
    ),
)
MATRIX_CRYPTO_EXACT_AUTHORITY_BINDINGS = tuple(
    (
        domain,
        capability,
        "session",
        mode,
        f"authority-lane-ref:matrix-crypto-{operation.replace('_', '-')}",
        f"authority-capability-ref:matrix-crypto-{operation.replace('_', '-')}-v1",
        f"authority-adapter-ref:matrix-crypto-{operation.replace('_', '-')}-v1",
        f"tool-ref:matrix-crypto-{operation.replace('_', '-')}-v1",
    )
    for operation, domain, capability, mode in _MATRIX_CRYPTO_BINDING_SPECS
)

_MATRIX_MESSAGING_CAPABILITIES = {
    "redaction": ("messages", "destructive", "full_machine_access_session"),
    "outbox_discard": (
        "messages",
        "destructive",
        "full_machine_access_session",
    ),
    "draft_read": ("messages", "read", "ask_before_changes"),
    "outbox_read": ("messages", "read", "ask_before_changes"),
    "desktop_notify": ("apps", "execute", "ask_before_changes"),
}
MATRIX_MESSAGING_EXACT_AUTHORITY_BINDINGS = tuple(
    (
        *_MATRIX_MESSAGING_CAPABILITIES.get(
            operation,
            (
                "messages",
                "send"
                if operation
                in {
                    "send",
                    "reply",
                    "thread",
                    "reaction",
                    "edit",
                    "typing",
                    "read_receipt",
                }
                else "mutate",
                "ask_before_changes",
            ),
        )[:2],
        "session",
        _MATRIX_MESSAGING_CAPABILITIES.get(
            operation,
            ("messages", "mutate", "ask_before_changes"),
        )[2],
        f"authority-lane-ref:matrix-messaging-{operation.replace('_', '-')}",
        f"authority-capability-ref:matrix-messaging-{operation.replace('_', '-')}-v1",
        f"authority-adapter-ref:matrix-messaging-{operation.replace('_', '-')}-v1",
        f"tool-ref:matrix-messaging-{operation.replace('_', '-')}-v1",
    )
    for operation in MATRIX_MESSAGING_OPERATIONS
)

MATRIX_ROOMS_MEDIA_EXACT_AUTHORITY_BINDINGS = tuple(
    (
        domain,
        capability,
        "session",
        mode,
        f"authority-lane-ref:matrix-rooms-media-{operation.replace('_', '-')}",
        f"authority-capability-ref:matrix-rooms-media-{operation.replace('_', '-')}-v1",
        f"authority-adapter-ref:matrix-rooms-media-{operation.replace('_', '-')}-v1",
        f"tool-ref:matrix-rooms-media-{operation.replace('_', '-')}-v1",
    )
    for operation, domain, capability, mode in MATRIX_ROOMS_MEDIA_BINDING_SPECS
)

# Composite transfers are the only MSG-MX-009 bindings permitted to request
# two authority domains. The catalog validator compares this entire map, so an
# extra or substituted domain still fails closed.
MATRIX_ROOMS_MEDIA_COMPOSITE_REQUESTED_DOMAINS = {
    "media_upload": {"messages": ("upload",), "files": ("read",)},
    "media_download_quarantine": {
        "messages": ("download",),
        "files": ("write",),
    },
}
