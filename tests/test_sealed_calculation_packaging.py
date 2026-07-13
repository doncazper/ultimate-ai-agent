from __future__ import annotations

import json
from pathlib import Path

from scripts import build_sealed_calculation_image


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "packaging" / "sealed-calculation"


def test_image_build_is_digest_pinned_and_runtime_has_no_shell_or_package_manager() -> (
    None
):
    dockerfile = (PACKAGE / "Dockerfile").read_text(encoding="utf-8")

    assert build_sealed_calculation_image.BASE_IMAGE.startswith("python@sha256:")
    assert build_sealed_calculation_image.BASE_IMAGE in dockerfile
    assert "FROM scratch" in dockerfile
    assert (
        "rm -rf /bin /sbin /usr/bin /usr/sbin /lib/apk /etc/apk /root /home"
        in dockerfile
    )
    assert "USER 65532:65532" in dockerfile
    assert 'ENTRYPOINT ["/usr/local/bin/python3.13", "-I", "-S"' in dockerfile
    assert "! -name python3.13 -delete" in dockerfile
    assert "/usr/local/lib/python3.13/ensurepip" in dockerfile
    assert "/usr/local/lib/python3.13/site-packages/pip*" in dockerfile
    assert "com.ultimate-ai-agent.sealed-calculation.runner-sha256" in dockerfile
    assert "com.ultimate-ai-agent.sealed-calculation.probe-sha256" in dockerfile


def test_seccomp_is_default_deny_and_omits_escape_syscalls() -> None:
    profile = json.loads((PACKAGE / "seccomp.json").read_text(encoding="utf-8"))
    allowed = {
        name
        for group in profile["syscalls"]
        if group["action"] == "SCMP_ACT_ALLOW"
        for name in group["names"]
    }

    assert profile["defaultAction"] == "SCMP_ACT_ERRNO"
    assert {"read", "write", "exit", "exit_group"}.issubset(allowed)
    assert not {
        "socket",
        "connect",
        "clone",
        "clone3",
        "fork",
        "vfork",
        "mount",
        "umount2",
        "ptrace",
        "bpf",
        "keyctl",
        "unshare",
        "setns",
    }.intersection(allowed)


def test_runtime_invocation_disables_pulls_network_mounts_and_privilege() -> None:
    backend = (
        ROOT
        / "src"
        / "ultimate_ai_agent"
        / "core"
        / "sandbox_calculation"
        / "backend.py"
    ).read_text(encoding="utf-8")

    for marker in (
        '"--pull",',
        '"never",',
        '"--network",',
        '"none",',
        '"--read-only",',
        '"--cap-drop",',
        '"ALL",',
        '"no-new-privileges:true",',
        '"--pids-limit",',
        '"--memory",',
        '"--memory-swap",',
        '"--user",',
        '"65532:65532",',
    ):
        assert marker in backend
    assert '"--volume"' not in backend
    assert '"--mount"' not in backend
    assert "shell=True" not in backend
    assert "os.system(" not in backend
