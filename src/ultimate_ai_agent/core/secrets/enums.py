from enum import Enum


class CredentialAuthType(str, Enum):
    none = "none"
    api_key = "api_key"
    oauth = "oauth"
    bearer_token = "bearer_token"
    basic_auth = "basic_auth"
    service_account = "service_account"
    local_keychain_ref = "local_keychain_ref"
    vault_ref = "vault_ref"


class CredentialStatus(str, Enum):
    active = "active"
    disabled = "disabled"
    revoked = "revoked"
    expired = "expired"
    pending = "pending"


class CredentialScope(str, Enum):
    user = "user"
    project = "project"
    workspace = "workspace"
    organization = "organization"
    provider = "provider"
    tool = "tool"
    system = "system"


class SecretSensitivity(str, Enum):
    credential_secret = "credential_secret"
    token_secret = "token_secret"
    private_key = "private_key"
    oauth_refresh_token = "oauth_refresh_token"
    webhook_secret = "webhook_secret"
    low_risk_placeholder = "low_risk_placeholder"
