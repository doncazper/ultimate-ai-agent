from tests.test_kernel_minimum_lovable_happy_path import request

from ultimate_ai_agent.core.kernel import KernelTaskStatus, MinimumKernelRunner


def test_kernel_denies_actual_apply_without_valid_approval(tmp_path):
    kernel_request = request(tmp_path).model_copy(update={"approval_ref": None})

    result = MinimumKernelRunner().run_task(kernel_request)

    assert result.success is False
    assert result.status == KernelTaskStatus.approval_required
    assert "APPROVAL_REQUIRED" in result.errors
    assert not (tmp_path / "notes/m5.md").exists()


def test_kernel_rejects_arbitrary_approval_ref(tmp_path):
    kernel_request = request(tmp_path).model_copy(update={"approval_ref": "approval_prod_unsafe"})

    result = MinimumKernelRunner().run_task(kernel_request)

    assert result.success is False
    assert result.status == KernelTaskStatus.approval_required
    assert "APPROVAL_REF_UNVALIDATED" in result.errors
    assert not (tmp_path / "notes/m5.md").exists()


def test_kernel_rejects_test_prefixed_approval_without_authority(tmp_path):
    kernel_request = request(tmp_path).model_copy(update={"approval_ref": "approval_test_create"})

    result = MinimumKernelRunner().run_task(kernel_request)

    assert result.success is False
    assert result.status == KernelTaskStatus.approval_required
    assert "APPROVAL_REF_UNVALIDATED" in result.errors
    assert not (tmp_path / "notes/m5.md").exists()
