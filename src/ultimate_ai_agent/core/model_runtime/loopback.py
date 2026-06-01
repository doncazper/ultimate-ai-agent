from typing import Any, Dict, List
from urllib.parse import parse_qsl, urlparse

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.model_runtime.enums import ModelRuntimeKind
from ultimate_ai_agent.core.model_runtime.redaction import assert_secret_clean


SECRET_QUERY_KEYS = {
    "api_" + "key",
    "apikey",
    "key",
    "token",
    "auth_" + "token",
    "password",
    "secret",
    "client_" + "secret",
}


class LoopbackRuntimeEndpoint(BaseModel):
    endpoint_id: str = Field(..., min_length=1)
    base_url: str = Field(..., min_length=1)
    allowed_hosts: List[str] = Field(default_factory=lambda: ["127.0.0.1", "localhost", "::1"])
    runtime_kind: ModelRuntimeKind
    model_id: str = Field(..., min_length=1)
    enabled: bool = True
    owner: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(use_enum_values=True, extra="forbid")

    @model_validator(mode="after")
    def endpoint_must_be_secret_clean(self):
        assert_secret_clean(self.model_dump(mode="json"), "Loopback runtime endpoint")
        return self

    @property
    def parsed_url(self):
        return urlparse(self.base_url)

    @property
    def host(self) -> str:
        return self.parsed_url.hostname or ""

    @property
    def query_keys(self) -> set[str]:
        return {key.lower().replace("-", "_") for key, _ in parse_qsl(self.parsed_url.query, keep_blank_values=True)}
