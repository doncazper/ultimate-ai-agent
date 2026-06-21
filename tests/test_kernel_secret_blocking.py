from pathlib import Path
from tests.test_kernel_minimum_lovable_happy_path import request

from ultimate_ai_agent.core.kernel import KernelTaskStatus, MinimumKernelRunner


def test_kernel_blocks_secret_like_content_before_events_or_write(tmp_path: Path) -> None:
    payload = request(tmp_path).model_dump()
    payload["new_content"] = "api_key='abcdefghijklmnop'"

    result = MinimumKernelRunner().run_payload(payload)

    assert result.success is False
    assert result.status == KernelTaskStatus.blocked
    assert "SECRET_CONTENT_BLOCKED" in result.errors
    assert "abcdefghijklmnop" not in result.model_dump_json()
    assert not (tmp_path / "notes/m5.md").exists()
