# M161 Local System Capability Probe

M161 implements a local system capability probe for model-fit metadata. It is
core-only, stdlib-only, local read-only, redacted, and bucketed-only.

Allowed in M161:

- OS and architecture bucket.
- CPU core bucket.
- RAM bucket.
- VRAM bucket when safely available, otherwise `vram:unknown`.
- Backend/device family bucket.
- Disk budget bucket for the default volume.
- Power/thermal hint when safely available, otherwise unknown.

Denied in M161:

- No serials.
- No hostname export.
- No usernames.
- No raw paths.
- No environment dump.
- No broad scans.
- No subprocess.
- No shell command.
- No network access.
- No downloads.
- No model file read.
- No model/provider call.
- No llama.cpp import.
- No llama.cpp server.
- No backend route.
- No Control Center control.
- No dependency.
- No memory write.
- No context injection.
- No production authority.

The probe uses small stdlib calls only: OS family, architecture family, CPU
count, portable memory buckets when `os.sysconf` is available, and free-space
bucket for the default volume. It must never expose raw host identifiers,
serial numbers, account names, local filesystem paths, environment variables, or
raw probe logs.
