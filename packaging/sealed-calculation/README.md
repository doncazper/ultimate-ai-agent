# Sealed Calculation Image

This directory builds the exact macOS Docker Desktop backend for
`calculation.sandbox.arithmetic.exact_lease`. The image accepts one bounded
arithmetic expression over stdin and never evaluates Python source. Invocation
uses an exact image ID with pulls disabled, no host mounts, no network namespace,
a read-only root, non-root UID, a one-process cgroup, bounded resources, and the
reviewed seccomp profile. Only the fixed Python launcher remains in the general
command directory; pip, ensurepip, setuptools, shells, and package managers are
removed.

Build locally with:

```bash
PYTHONPATH=src .venv/bin/python scripts/build_sealed_calculation_image.py
```

The printed image ID is safe configuration metadata. Tags are never accepted by
the runtime adapter after discovery. Building may fetch the pinned public Python
base image if it is not already present; invocation never pulls.

The isolation probe is test-only and is not reachable through the calculation
adapter. Broad shell, package installation, arbitrary Python, host filesystem
mounts, host environment inheritance, browser work, connector work, and network
access remain denied.
