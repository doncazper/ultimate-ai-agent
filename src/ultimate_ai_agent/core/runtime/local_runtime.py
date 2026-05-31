from typing import Optional
from pydantic import BaseModel

class LocalModelProfile(BaseModel):
    model_id: str
    model_family: Optional[str] = None
    context_window: int
    ram_required_gb: Optional[float] = None
    vram_required_gb: Optional[float] = None
    tokens_per_second_estimate: Optional[float] = None
    time_to_first_token_estimate: Optional[float] = None

class LocalRuntimeManifest(BaseModel):
    runtime_id: str
    runtime_type: str  # ollama, lm_studio, llama_cpp, vllm, sglang, openai_compatible_local, cloud_provider_placeholder
    base_url: Optional[str] = None
    model_profile: LocalModelProfile
    max_parallel_requests: int = 1
    privacy_mode: str = "local_only"  # local_only, hybrid_redacted, cloud_allowed
    runtime_health_status: str = "healthy"  # healthy, degraded, unhealthy
