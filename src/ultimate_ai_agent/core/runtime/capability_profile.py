from pydantic import BaseModel

class RuntimeOptimizationProfile(BaseModel):
    supports_prefix_caching: bool = False
    supports_cuda_graphs: bool = False
    supports_speculative_decoding: bool = False
    supports_fp8_kv_cache: bool = False
    supports_tensor_parallelism: bool = False

class PrivacyRoutingPolicy(BaseModel):
    policy_id: str
    allowed_modes: list[str] = ["local_only"]  # local_only, hybrid_redacted, cloud_allowed
    force_redaction: bool = True
