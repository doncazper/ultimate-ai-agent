# Device Capability Manifest Schema TODO

Status: Future planning placeholder only, v0.14.4

This is not a JSON schema and is not a runtime contract. It records future schema intent for a later reviewed milestone.

Future schema concept:

```text
MobileDeviceCapabilityManifest
```

Future fields:

```text
device_id
capability_id
capability_type
risk_level
requires_foreground
requires_user_gesture
requires_os_permission
allowed_purposes
denied_purposes
retention_policy
redaction_policy
event_logging_required
receipt_required
revocation_supported
```

Non-goals for v0.14.4:

```text
no runtime Device Capability Broker
no capability execution
no mobile app
no native mobile dependency
no network call
no background service
```
