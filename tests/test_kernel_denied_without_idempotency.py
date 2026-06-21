from pathlib import Path
import pytest
from pydantic import ValidationError

from tests.test_kernel_minimum_lovable_happy_path import request


def test_kernel_denies_missing_idempotency_at_boundary(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="idempotency"):
        request(tmp_path).model_copy(update={"idempotency_key": None}, deep=True).model_validate(
            request(tmp_path).model_dump() | {"idempotency_key": None}
        )
