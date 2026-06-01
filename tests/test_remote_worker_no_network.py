from pathlib import Path


def test_remote_worker_source_has_no_live_network_or_execution_fragments():
    root = Path("src/ultimate_ai_agent/core/remote_workers")
    forbidden = [
        "socket",
        "subprocess",
        "Popen",
        "os.system",
        "threading",
        "Thread(",
        "asyncio",
        "serve",
        "funnel",
        "tailscale",
        "tailscaled",
        "urlopen",
        "requests.",
        "httpx",
        "execute_remote",
        "dispatch_job(",
        "launch_subagent(",
    ]

    for path in root.rglob("*.py"):
        source = path.read_text(encoding="utf-8").lower()
        for fragment in forbidden:
            assert fragment.lower() not in source, f"{fragment} found in {path}"
