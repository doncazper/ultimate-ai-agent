# Mobile Sensor Permission Manifest Schema TODO

Status: Future planning placeholder only, v0.14.4

This is not a JSON schema and is not a runtime contract. It records future schema intent for a later reviewed milestone.

Future schema concepts:

```text
MobileSensorCaptureRequest
MobileSensorCaptureResult
```

Future request fields:

```text
request_id
device_id
capability_id
purpose
scope
duration
data_classification
approval_ref
consent_ref
event_ref
```

Future result fields:

```text
capture_id
status
source_refs
redactions_applied
evidence_refs
retention_policy
safe_summary
no_raw_secret_fields
```

Non-goals for v0.14.4:

```text
no sensor API
no OS permission integration
no capture runtime
no automatic memory write
no external send
no background collection
```
