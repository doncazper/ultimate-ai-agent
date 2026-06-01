# Route Inventory

The API route inventory is generated from FastAPI route metadata and exposed by `/api/manifest`.

Each route declares:

- `path`
- `method`
- `operation_id`
- `tags`
- `summary`
- `validation_only`
- `side_effect_class`
- `requires_auth_future`
- `blocked_from_production`

Allowed side-effect classes in v0.11.2 are:

- `none`
- `validation_only`
- `local_dev_workspace_only`

Production runtime side effects are not allowed in this milestone.
