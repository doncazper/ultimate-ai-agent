from pydantic import BaseModel

class LocalResourceBudget(BaseModel):
    max_ram_gb: float
    max_vram_gb: float
    max_cpu_percent: float = 100.0
    disk_quota_mb: float = 1024.0
