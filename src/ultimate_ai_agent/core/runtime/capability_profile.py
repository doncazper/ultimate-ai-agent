from pydantic import BaseModel

class RuntimeOptimizationProfile(BaseModel):
    supports_prefix_caching: bool = False
    supports_continuous_batching: bool = False
    supports_chunked_prefill: bool = False
    supports_disaggregated_prefill: bool = False
    supports_cuda_graphs: bool = False
    supports_speculative_decoding: bool = False
    supports_fp8_kv_cache: bool = False
    supports_tensor_parallelism: bool = False
    p95_time_to_first_token_ms: float | None = None
    p99_time_to_first_token_ms: float | None = None
    warmup_required: bool = False

class PrivacyRoutingPolicy(BaseModel):
    policy_id: str
    allowed_modes: list[str] = ["local_only"]  # local_only, hybrid_redacted, cloud_allowed
    force_redaction: bool = True
