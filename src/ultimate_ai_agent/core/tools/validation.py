from ultimate_ai_agent.core.tools.manifests import ToolManifest

def validate_tool_manifest(manifest: ToolManifest) -> bool:
    """Validate that the tool manifest is consistent and matches schemas.

    Raises ValueError if invalid, returns True if valid.
    """
    if not manifest.tool_id:
        raise ValueError("Tool Manifest tool_id cannot be empty.")
        
    if not manifest.display_name:
        raise ValueError("Tool Manifest display_name cannot be empty.")
        
    if not manifest.capability_flag:
        raise ValueError("Tool Manifest capability_flag cannot be empty.")

    if manifest.permissions_required and not manifest.permission_manifest:
        raise ValueError("Tool Manifest must include permission_manifest details if permissions_required is specified.")

    # Validate permission manifest links if it exists
    if manifest.permission_manifest:
        # Permission manifest must match list of required permissions
        required = set(manifest.permissions_required)
        declared = set(manifest.permission_manifest.required_permissions)
        if required != declared:
            raise ValueError(f"Required permissions mismatch: permissions_required has {required}, but permission_manifest has {declared}.")

    return True
