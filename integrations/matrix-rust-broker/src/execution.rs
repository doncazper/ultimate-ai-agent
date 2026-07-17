use std::path::Path;

use matrix_sdk::{
    Client,
    authentication::matrix::MatrixSession,
    config::SyncSettings,
    ruma::{
        OwnedEventId, OwnedRoomId, OwnedTransactionId,
        api::client::receipt::create_receipt::v3::ReceiptType,
        events::{reaction::ReactionEventContent, receipt::ReceiptThread, relation::Annotation},
    },
};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use url::Url;
use zeroize::{Zeroize, Zeroizing};

use crate::{
    keychain::{self, SecretKind as KeychainSecretKind},
    protocol::{BrokerOperation, BrokerRequest, SecretKind, SecretString},
};

pub struct ExecutionResult {
    pub outcome: &'static str,
    pub event_ref: Option<String>,
}

#[derive(Debug)]
pub struct ExecutionError {
    pub code: &'static str,
    pub uncertain: bool,
}

impl ExecutionError {
    fn safe(code: &'static str) -> Self {
        Self {
            code,
            uncertain: false,
        }
    }

    fn uncertain(code: &'static str) -> Self {
        Self {
            code,
            uncertain: true,
        }
    }
}

pub async fn execute(
    request: &BrokerRequest,
    scope_root: &Path,
) -> Result<ExecutionResult, ExecutionError> {
    match request.operation {
        BrokerOperation::ProtocolProbe => Ok(success("ready", None)),
        BrokerOperation::KeychainCreate => {
            keychain::create_random(&scope_ref(request), secret_kind(request)?)
                .map_err(ExecutionError::safe)?;
            Ok(success("created", None))
        }
        BrokerOperation::KeychainProbe => {
            keychain::probe(&scope_ref(request), secret_kind(request)?)
                .map_err(ExecutionError::safe)?;
            Ok(success("available", None))
        }
        BrokerOperation::KeychainRotate => {
            let kind = secret_kind(request)?;
            if matches!(
                kind,
                KeychainSecretKind::Session | KeychainSecretKind::CryptoStore
            ) {
                return Err(ExecutionError::safe(
                    "MATRIX_KEYCHAIN_ROTATION_MIGRATION_REQUIRED",
                ));
            }
            keychain::rotate(&scope_ref(request), kind).map_err(ExecutionError::safe)?;
            Ok(success("rotated", None))
        }
        BrokerOperation::KeychainDelete => {
            keychain::delete(&scope_ref(request), secret_kind(request)?)
                .map_err(ExecutionError::safe)?;
            Ok(success("deleted", None))
        }
        BrokerOperation::SessionLogin => login(request, scope_root).await,
        BrokerOperation::SessionRestore => {
            let _client = restore_client(request, scope_root).await?;
            Ok(success("restored", None))
        }
        BrokerOperation::SessionLogout => logout(request, scope_root).await,
        operation => mutate(request, scope_root, operation).await,
    }
}

fn secret_kind(request: &BrokerRequest) -> Result<KeychainSecretKind, ExecutionError> {
    match request.secret_kind {
        Some(SecretKind::Session) => Ok(KeychainSecretKind::Session),
        Some(SecretKind::CryptoStore) => Ok(KeychainSecretKind::CryptoStore),
        Some(SecretKind::Outbox) => Ok(KeychainSecretKind::Outbox),
        None => Err(ExecutionError::safe("MATRIX_KEYCHAIN_SECRET_KIND_REQUIRED")),
    }
}

async fn login(
    request: &BrokerRequest,
    scope_root: &Path,
) -> Result<ExecutionResult, ExecutionError> {
    let username = required_secret(&request.username, "MATRIX_SESSION_USERNAME_REQUIRED")?;
    let password = required_secret(&request.password, "MATRIX_SESSION_PASSWORD_REQUIRED")?;
    ensure_crypto_store_key(request)?;
    let client = build_client(request, scope_root).await?;
    client
        .matrix_auth()
        .login_username(username, password)
        .initial_device_display_name("UAA Messenger")
        .await
        .map_err(|_| ExecutionError::safe("MATRIX_SESSION_LOGIN_FAILED"))?;
    let session = client
        .matrix_auth()
        .session()
        .ok_or_else(|| ExecutionError::safe("MATRIX_SESSION_RESULT_MISSING"))?;
    let mut serialized = Zeroizing::new(
        serde_json::to_vec(&session)
            .map_err(|_| ExecutionError::safe("MATRIX_SESSION_SERIALIZATION_FAILED"))?,
    );
    keychain::set(
        &scope_ref(request),
        KeychainSecretKind::Session,
        &serialized,
    )
    .map_err(ExecutionError::safe)?;
    serialized.zeroize();
    Ok(success("authenticated", None))
}

async fn logout(
    request: &BrokerRequest,
    scope_root: &Path,
) -> Result<ExecutionResult, ExecutionError> {
    let client = restore_client(request, scope_root).await?;
    client
        .logout()
        .await
        .map_err(|_| ExecutionError::uncertain("MATRIX_SESSION_LOGOUT_OUTCOME_UNCERTAIN"))?;
    keychain::delete(&scope_ref(request), KeychainSecretKind::Session)
        .map_err(ExecutionError::safe)?;
    Ok(success("logged_out", None))
}

async fn mutate(
    request: &BrokerRequest,
    scope_root: &Path,
    operation: BrokerOperation,
) -> Result<ExecutionResult, ExecutionError> {
    let client = restore_client(request, scope_root).await?;
    client
        .sync_once(SyncSettings::default())
        .await
        .map_err(|_| ExecutionError::safe("MATRIX_SYNC_BEFORE_MUTATION_FAILED"))?;
    let room_id = required_secret(&request.room_id, "MATRIX_ROOM_ID_REQUIRED")?;
    let room_id = OwnedRoomId::try_from(room_id)
        .map_err(|_| ExecutionError::safe("MATRIX_ROOM_ID_INVALID"))?;
    let room = client
        .get_room(&room_id)
        .ok_or_else(|| ExecutionError::safe("MATRIX_ROOM_NOT_FOUND"))?;

    match operation {
        BrokerOperation::Send
        | BrokerOperation::Reply
        | BrokerOperation::Thread
        | BrokerOperation::Edit => {
            let transaction_id =
                required_secret(&request.transaction_id, "MATRIX_TRANSACTION_ID_REQUIRED")?;
            if transaction_id.len() > 128 || transaction_id.is_empty() {
                return Err(ExecutionError::safe("MATRIX_TRANSACTION_ID_INVALID"));
            }
            let transaction_id = OwnedTransactionId::from(transaction_id.to_owned());
            let (event_type, content) = event_content(request, operation)?;
            let result = room
                .send_raw(event_type, content)
                .with_transaction_id(&transaction_id)
                .await
                .map_err(|_| ExecutionError::uncertain("MATRIX_SEND_OUTCOME_UNCERTAIN"))?;
            Ok(success(
                "server_acknowledged",
                Some(private_event_ref(result.response.event_id.as_str())),
            ))
        }
        BrokerOperation::Reaction => {
            let event_id = parse_event_id(request)?;
            let key = required_secret(&request.reaction_key, "MATRIX_REACTION_KEY_REQUIRED")?;
            if key.chars().count() > 16 || key.contains(['\n', '\r', '\0']) {
                return Err(ExecutionError::safe("MATRIX_REACTION_KEY_INVALID"));
            }
            let transaction_id =
                required_secret(&request.transaction_id, "MATRIX_TRANSACTION_ID_REQUIRED")?;
            if transaction_id.len() > 128 || transaction_id.is_empty() {
                return Err(ExecutionError::safe("MATRIX_TRANSACTION_ID_INVALID"));
            }
            let transaction_id = OwnedTransactionId::from(transaction_id.to_owned());
            let content = ReactionEventContent::new(Annotation::new(event_id, key.to_owned()));
            let result = room
                .send(content)
                .with_transaction_id(transaction_id)
                .await
                .map_err(|_| ExecutionError::uncertain("MATRIX_SEND_OUTCOME_UNCERTAIN"))?;
            Ok(success(
                "server_acknowledged",
                Some(private_event_ref(result.response.event_id.as_str())),
            ))
        }
        BrokerOperation::Redaction => {
            let event_id = parse_event_id(request)?;
            let transaction_id =
                required_secret(&request.transaction_id, "MATRIX_TRANSACTION_ID_REQUIRED")?;
            let transaction_id = OwnedTransactionId::from(transaction_id.to_owned());
            let result = room
                .redact(&event_id, None, Some(transaction_id))
                .await
                .map_err(|_| ExecutionError::uncertain("MATRIX_REDACTION_OUTCOME_UNCERTAIN"))?;
            Ok(success(
                "server_acknowledged",
                Some(private_event_ref(result.event_id.as_str())),
            ))
        }
        BrokerOperation::Typing => {
            let active = request
                .typing_active
                .ok_or_else(|| ExecutionError::safe("MATRIX_TYPING_STATE_REQUIRED"))?;
            room.typing_notice(active)
                .await
                .map_err(|_| ExecutionError::uncertain("MATRIX_TYPING_OUTCOME_UNCERTAIN"))?;
            Ok(success("server_acknowledged", None))
        }
        BrokerOperation::ReadReceipt => {
            let event_id = parse_event_id(request)?;
            room.send_single_receipt(ReceiptType::Read, ReceiptThread::Unthreaded, event_id)
                .await
                .map_err(|_| ExecutionError::uncertain("MATRIX_RECEIPT_OUTCOME_UNCERTAIN"))?;
            Ok(success("server_acknowledged", None))
        }
        _ => Err(ExecutionError::safe("MATRIX_BROKER_OPERATION_UNSUPPORTED")),
    }
}

fn event_content(
    request: &BrokerRequest,
    operation: BrokerOperation,
) -> Result<(&'static str, Value), ExecutionError> {
    let body = required_secret(&request.body, "MATRIX_MESSAGE_BODY_REQUIRED")?;
    if body.is_empty() || body.len() > 16 * 1024 || body.contains('\0') {
        return Err(ExecutionError::safe("MATRIX_MESSAGE_BODY_INVALID"));
    }
    let mut content = json!({"msgtype": "m.text", "body": body});
    if let Some(formatted) = request.formatted_body.as_ref().map(SecretString::as_str) {
        if formatted.is_empty() || formatted.len() > 24 * 1024 || formatted.contains('\0') {
            return Err(ExecutionError::safe("MATRIX_FORMATTED_BODY_INVALID"));
        }
        content["format"] = json!("org.matrix.custom.html");
        content["formatted_body"] = json!(formatted);
    }
    if let Some(users) = request.mention_user_ids.as_ref() {
        if users.len() > 32
            || users.iter().map(SecretString::as_str).any(|user| {
                user.len() > 255 || !user.starts_with('@') || user.contains(char::is_whitespace)
            })
        {
            return Err(ExecutionError::safe("MATRIX_MENTION_SET_INVALID"));
        }
        let user_ids: Vec<&str> = users.iter().map(SecretString::as_str).collect();
        content["m.mentions"] = json!({"user_ids": user_ids});
    }
    match operation {
        BrokerOperation::Send => {}
        BrokerOperation::Reply => {
            let event_id = required_secret(
                &request.relation_event_id,
                "MATRIX_RELATION_EVENT_ID_REQUIRED",
            )?;
            content["m.relates_to"] = json!({"m.in_reply_to": {"event_id": event_id}});
        }
        BrokerOperation::Thread => {
            let event_id = required_secret(
                &request.relation_event_id,
                "MATRIX_RELATION_EVENT_ID_REQUIRED",
            )?;
            content["m.relates_to"] = json!({
                "rel_type": "m.thread",
                "event_id": event_id,
                "is_falling_back": true,
                "m.in_reply_to": {"event_id": event_id},
            });
        }
        BrokerOperation::Edit => {
            let event_id = required_secret(
                &request.relation_event_id,
                "MATRIX_RELATION_EVENT_ID_REQUIRED",
            )?;
            let new_content = content.clone();
            content["body"] = json!(format!("* {body}"));
            content["m.new_content"] = new_content;
            content["m.relates_to"] = json!({
                "rel_type": "m.replace",
                "event_id": event_id,
            });
        }
        _ => {
            return Err(ExecutionError::safe(
                "MATRIX_EVENT_CONTENT_OPERATION_INVALID",
            ));
        }
    }
    Ok(("m.room.message", content))
}

async fn restore_client(
    request: &BrokerRequest,
    scope_root: &Path,
) -> Result<Client, ExecutionError> {
    let client = build_client(request, scope_root).await?;
    let serialized = keychain::get(&scope_ref(request), KeychainSecretKind::Session)
        .map_err(ExecutionError::safe)?;
    let session: MatrixSession = serde_json::from_slice(&serialized)
        .map_err(|_| ExecutionError::safe("MATRIX_SESSION_KEYCHAIN_VALUE_CORRUPT"))?;
    client
        .restore_session(session)
        .await
        .map_err(|_| ExecutionError::safe("MATRIX_SESSION_RESTORE_FAILED"))?;
    Ok(client)
}

async fn build_client(
    request: &BrokerRequest,
    scope_root: &Path,
) -> Result<Client, ExecutionError> {
    let homeserver = required_secret(&request.homeserver_url, "MATRIX_HOMESERVER_URL_REQUIRED")?;
    validate_loopback_homeserver(homeserver)?;
    let store_key = keychain::get(&scope_ref(request), KeychainSecretKind::CryptoStore)
        .map_err(ExecutionError::safe)?;
    let passphrase = Zeroizing::new(hex::encode(&*store_key));
    let store_path = scope_root.join("sdk-store");
    Client::builder()
        .homeserver_url(homeserver)
        .sqlite_store(store_path, Some(&passphrase))
        .build()
        .await
        .map_err(|_| ExecutionError::safe("MATRIX_CLIENT_BUILD_FAILED"))
}

fn ensure_crypto_store_key(request: &BrokerRequest) -> Result<(), ExecutionError> {
    match keychain::probe(&scope_ref(request), KeychainSecretKind::CryptoStore) {
        Ok(()) => Ok(()),
        Err("MATRIX_KEYCHAIN_ITEM_MISSING") => {
            keychain::create_random(&scope_ref(request), KeychainSecretKind::CryptoStore)
                .map_err(ExecutionError::safe)
        }
        Err(code) => Err(ExecutionError::safe(code)),
    }
}

fn validate_loopback_homeserver(value: &str) -> Result<(), ExecutionError> {
    let url =
        Url::parse(value).map_err(|_| ExecutionError::safe("MATRIX_HOMESERVER_URL_INVALID"))?;
    if !matches!(url.scheme(), "http" | "https")
        || !matches!(url.host_str(), Some("localhost" | "127.0.0.1" | "::1"))
        || !url.username().is_empty()
        || url.password().is_some()
        || url.query().is_some()
        || url.fragment().is_some()
    {
        return Err(ExecutionError::safe("MATRIX_HOMESERVER_LOOPBACK_REQUIRED"));
    }
    Ok(())
}

fn parse_event_id(request: &BrokerRequest) -> Result<OwnedEventId, ExecutionError> {
    let value = required_secret(&request.event_id, "MATRIX_EVENT_ID_REQUIRED")?;
    OwnedEventId::try_from(value).map_err(|_| ExecutionError::safe("MATRIX_EVENT_ID_INVALID"))
}

fn required_secret<'a>(
    value: &'a Option<SecretString>,
    code: &'static str,
) -> Result<&'a str, ExecutionError> {
    value
        .as_ref()
        .map(SecretString::as_str)
        .ok_or_else(|| ExecutionError::safe(code))
}

fn scope_ref(request: &BrokerRequest) -> String {
    let mut digest = Sha256::new();
    digest.update(request.account_ref.as_bytes());
    digest.update([0]);
    digest.update(request.homeserver_ref.as_bytes());
    digest.update([0]);
    digest.update(request.device_ref.as_bytes());
    format!("matrix-scope-ref:sha256:{}", hex::encode(digest.finalize()))
}

fn private_event_ref(event_id: &str) -> String {
    format!(
        "event-ref:matrix:sha256:{}",
        hex::encode(Sha256::digest(event_id.as_bytes()))
    )
}

fn success(outcome: &'static str, event_ref: Option<String>) -> ExecutionResult {
    ExecutionResult { outcome, event_ref }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn remote_homeservers_fail_closed() {
        assert_eq!(
            validate_loopback_homeserver("https://matrix.example.org")
                .unwrap_err()
                .code,
            "MATRIX_HOMESERVER_LOOPBACK_REQUIRED"
        );
        assert!(validate_loopback_homeserver("http://127.0.0.1:8008").is_ok());
    }

    #[test]
    fn private_event_refs_do_not_expose_identifiers() {
        let value = private_event_ref("$opaque:localhost");
        assert!(value.starts_with("event-ref:matrix:sha256:"));
        assert!(!value.contains("opaque"));
        assert!(!value.contains("localhost"));
    }
}
