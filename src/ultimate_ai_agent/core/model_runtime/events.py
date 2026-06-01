from typing import Any, Dict

from ultimate_ai_agent.core.model_runtime.requests import ModelRuntimeRequest
from ultimate_ai_agent.core.model_runtime.responses import ModelRuntimeResponse


def runtime_event_metadata(request: ModelRuntimeRequest, response: ModelRuntimeResponse) -> Dict[str, Any]:
    return {
        "event_name": "model.runtime.simulated",
        "runtime_request_id": request.runtime_request_id,
        "runtime_response_id": response.runtime_response_id,
        "run_id": request.run_id,
        "model_profile_id": request.model_profile_id,
        "adapter_id": request.adapter_id,
        "simulated": True,
        "truth_authority": False,
    }
