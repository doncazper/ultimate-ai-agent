from ultimate_ai_agent.core.planning.contracts import TaskPlanningManifest


def build_task_planning_manifest(baseline_version: str = "0.33.0") -> TaskPlanningManifest:
    return TaskPlanningManifest(baseline_version=baseline_version)
