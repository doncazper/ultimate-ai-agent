use std::time::{SystemTime, UNIX_EPOCH};

use base64::{Engine as _, engine::general_purpose::STANDARD as BASE64};
use hmac::{Hmac, Mac};
use serde::{Deserialize, Deserializer, Serialize};
use sha2::Sha256;
use zeroize::Zeroize;

pub const PROTOCOL_VERSION: &str = "uaa-matrix-rust-broker.v1";
pub const RESPONSE_VERSION: &str = "uaa-matrix-rust-broker-response.v1";
pub const MAX_FRAME_BYTES: usize = 64 * 1024;
pub const AUTH_KEY_BYTES: usize = 32;

type HmacSha256 = Hmac<Sha256>;

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WireEnvelope {
    pub payload_b64: String,
    pub auth_tag: String,
}

#[derive(Debug, Serialize)]
pub struct WireResponseEnvelope {
    pub payload_b64: String,
    pub auth_tag: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct BrokerRequest {
    pub protocol_version: String,
    pub request_ref: String,
    pub request_fingerprint_ref: String,
    pub nonce: String,
    pub issued_at_ms: u64,
    pub deadline_ms: u64,
    pub operation: BrokerOperation,
    pub account_ref: String,
    pub homeserver_ref: String,
    pub device_ref: String,
    pub room_ref: Option<String>,
    pub event_ref: Option<String>,
    pub transaction_ref: Option<String>,
    pub member_ref: Option<String>,
    pub space_ref: Option<String>,
    pub media_ref: Option<String>,
    pub quarantine_ref: Option<String>,
    pub approval_ref: String,
    pub lease_ref: String,
    pub idempotency_ref: String,
    pub adapter_ref: String,
    pub budget_ref: String,
    pub readiness_ref: String,
    pub safe_disable_ref: String,
    pub kill_switch_ref: String,
    pub secret_kind: Option<SecretKind>,
    pub homeserver_url: Option<SecretString>,
    pub username: Option<SecretString>,
    pub password: Option<SecretString>,
    pub room_id: Option<SecretString>,
    pub event_id: Option<SecretString>,
    pub transaction_id: Option<SecretString>,
    pub body: Option<SecretString>,
    pub formatted_body: Option<SecretString>,
    pub mention_user_ids: Option<Vec<SecretString>>,
    pub relation_event_id: Option<SecretString>,
    pub reaction_key: Option<SecretString>,
    pub typing_active: Option<bool>,
    pub member_id: Option<SecretString>,
    pub space_id: Option<SecretString>,
    pub room_name: Option<SecretString>,
    pub desired_state: Option<SecretString>,
    pub prior_state: Option<SecretString>,
    pub media_uri: Option<SecretString>,
    pub media_type: Option<SecretString>,
    pub media_b64: Option<SecretString>,
}

pub struct SecretString(String);

impl SecretString {
    pub fn as_str(&self) -> &str {
        self.0.as_str()
    }
}

impl<'de> Deserialize<'de> for SecretString {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        String::deserialize(deserializer).map(Self)
    }
}

impl Drop for SecretString {
    fn drop(&mut self) {
        self.0.zeroize();
    }
}

#[derive(Clone, Copy, Debug, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum SecretKind {
    Session,
    CryptoStore,
    Outbox,
}

#[derive(Clone, Copy, Debug, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum BrokerOperation {
    ProtocolProbe,
    KeychainCreate,
    KeychainProbe,
    KeychainRotate,
    KeychainDelete,
    SessionLogin,
    SessionRestore,
    SessionLogout,
    Send,
    Reply,
    Thread,
    Reaction,
    Edit,
    Redaction,
    Typing,
    ReadReceipt,
    DmCreate,
    RoomCreate,
    RoomJoin,
    RoomLeave,
    InviteSend,
    InviteAccept,
    InviteReject,
    InviteWithdraw,
    RoomPowerRoleWrite,
    SpaceMappingWrite,
    NotificationSettingsWrite,
    HistoryVisibilityWrite,
    PinWrite,
    AccountRoomPreferenceWrite,
    MediaUpload,
    MediaDownloadQuarantine,
}

impl BrokerOperation {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::ProtocolProbe => "protocol_probe",
            Self::KeychainCreate => "keychain_create",
            Self::KeychainProbe => "keychain_probe",
            Self::KeychainRotate => "keychain_rotate",
            Self::KeychainDelete => "keychain_delete",
            Self::SessionLogin => "session_login",
            Self::SessionRestore => "session_restore",
            Self::SessionLogout => "session_logout",
            Self::Send => "send",
            Self::Reply => "reply",
            Self::Thread => "thread",
            Self::Reaction => "reaction",
            Self::Edit => "edit",
            Self::Redaction => "redaction",
            Self::Typing => "typing",
            Self::ReadReceipt => "read_receipt",
            Self::DmCreate => "dm_create",
            Self::RoomCreate => "room_create",
            Self::RoomJoin => "room_join",
            Self::RoomLeave => "room_leave",
            Self::InviteSend => "invite_send",
            Self::InviteAccept => "invite_accept",
            Self::InviteReject => "invite_reject",
            Self::InviteWithdraw => "invite_withdraw",
            Self::RoomPowerRoleWrite => "room_power_role_write",
            Self::SpaceMappingWrite => "space_mapping_write",
            Self::NotificationSettingsWrite => "notification_settings_write",
            Self::HistoryVisibilityWrite => "history_visibility_write",
            Self::PinWrite => "pin_write",
            Self::AccountRoomPreferenceWrite => "account_room_preference_write",
            Self::MediaUpload => "media_upload",
            Self::MediaDownloadQuarantine => "media_download_quarantine",
        }
    }

    pub fn is_network_mutation(self) -> bool {
        matches!(
            self,
            Self::SessionLogin
                | Self::SessionLogout
                | Self::Send
                | Self::Reply
                | Self::Thread
                | Self::Reaction
                | Self::Edit
                | Self::Redaction
                | Self::Typing
                | Self::ReadReceipt
                | Self::DmCreate
                | Self::RoomCreate
                | Self::RoomJoin
                | Self::RoomLeave
                | Self::InviteSend
                | Self::InviteAccept
                | Self::InviteReject
                | Self::InviteWithdraw
                | Self::RoomPowerRoleWrite
                | Self::SpaceMappingWrite
                | Self::NotificationSettingsWrite
                | Self::HistoryVisibilityWrite
                | Self::PinWrite
                | Self::AccountRoomPreferenceWrite
                | Self::MediaUpload
                | Self::MediaDownloadQuarantine
        )
    }
}

#[derive(Debug, Serialize)]
pub struct BrokerResponse {
    pub protocol_version: &'static str,
    pub ok: bool,
    pub operation: &'static str,
    pub request_ref: String,
    pub request_fingerprint_ref: String,
    pub receipt_ref: String,
    pub outcome: &'static str,
    pub event_ref: Option<String>,
    pub transaction_ref: Option<String>,
    pub quarantine_ref: Option<String>,
    pub byte_count: Option<usize>,
    pub replayed: bool,
    pub credential_material_included: bool,
    pub content_included: bool,
    pub raw_identifiers_included: bool,
    pub error_code: Option<&'static str>,
}

#[derive(Debug, Serialize)]
pub struct ReadinessRecord {
    pub protocol_version: &'static str,
    pub adapter_ref: &'static str,
    pub bind_ref: &'static str,
    pub port: u16,
    pub maximum_frame_bytes: usize,
    pub one_request_only: bool,
    pub credential_material_included: bool,
}

pub fn decode_authenticated_request(
    frame: &[u8],
    auth_key: &[u8],
) -> Result<BrokerRequest, &'static str> {
    if frame.is_empty() || frame.len() > MAX_FRAME_BYTES || auth_key.len() != AUTH_KEY_BYTES {
        return Err("MATRIX_BROKER_FRAME_INVALID");
    }
    let envelope: WireEnvelope =
        serde_json::from_slice(frame).map_err(|_| "MATRIX_BROKER_ENVELOPE_INVALID")?;
    let payload = BASE64
        .decode(envelope.payload_b64.as_bytes())
        .map_err(|_| "MATRIX_BROKER_PAYLOAD_ENCODING_INVALID")?;
    if payload.is_empty() || payload.len() > MAX_FRAME_BYTES {
        return Err("MATRIX_BROKER_PAYLOAD_INVALID");
    }
    let supplied_tag =
        hex::decode(envelope.auth_tag).map_err(|_| "MATRIX_BROKER_AUTH_TAG_INVALID")?;
    let mut mac =
        HmacSha256::new_from_slice(auth_key).map_err(|_| "MATRIX_BROKER_AUTH_KEY_INVALID")?;
    mac.update(&payload);
    mac.verify_slice(&supplied_tag)
        .map_err(|_| "MATRIX_BROKER_AUTHENTICATION_FAILED")?;
    let request: BrokerRequest =
        serde_json::from_slice(&payload).map_err(|_| "MATRIX_BROKER_REQUEST_INVALID")?;
    validate_request(&request)?;
    Ok(request)
}

pub fn encode_authenticated_response(
    response: &BrokerResponse,
    auth_key: &[u8],
) -> Result<Vec<u8>, &'static str> {
    if auth_key.len() != AUTH_KEY_BYTES {
        return Err("MATRIX_BROKER_AUTH_KEY_INVALID");
    }
    let payload = serde_json::to_vec(response).map_err(|_| "MATRIX_BROKER_RESPONSE_INVALID")?;
    let mut mac =
        HmacSha256::new_from_slice(auth_key).map_err(|_| "MATRIX_BROKER_AUTH_KEY_INVALID")?;
    mac.update(&payload);
    let envelope = WireResponseEnvelope {
        payload_b64: BASE64.encode(payload),
        auth_tag: hex::encode(mac.finalize().into_bytes()),
    };
    serde_json::to_vec(&envelope).map_err(|_| "MATRIX_BROKER_RESPONSE_INVALID")
}

fn validate_request(request: &BrokerRequest) -> Result<(), &'static str> {
    if request.protocol_version != PROTOCOL_VERSION {
        return Err("MATRIX_BROKER_PROTOCOL_VERSION_UNSUPPORTED");
    }
    let now = now_ms()?;
    if request.deadline_ms <= now || request.deadline_ms <= request.issued_at_ms {
        return Err("MATRIX_BROKER_DEADLINE_EXPIRED");
    }
    if request.issued_at_ms > now.saturating_add(5_000)
        || request.deadline_ms.saturating_sub(request.issued_at_ms) > 300_000
    {
        return Err("MATRIX_BROKER_DEADLINE_INVALID");
    }
    if request.nonce.len() < 32
        || request.nonce.len() > 128
        || !request
            .nonce
            .bytes()
            .all(|value| value.is_ascii_alphanumeric())
    {
        return Err("MATRIX_BROKER_NONCE_INVALID");
    }
    for value in [
        &request.request_ref,
        &request.request_fingerprint_ref,
        &request.account_ref,
        &request.homeserver_ref,
        &request.device_ref,
        &request.approval_ref,
        &request.lease_ref,
        &request.idempotency_ref,
        &request.adapter_ref,
        &request.budget_ref,
        &request.readiness_ref,
        &request.safe_disable_ref,
        &request.kill_switch_ref,
    ] {
        if !safe_ref(value) {
            return Err("MATRIX_BROKER_EXACT_BINDING_INVALID");
        }
    }
    for value in [
        request.room_ref.as_ref(),
        request.event_ref.as_ref(),
        request.transaction_ref.as_ref(),
        request.member_ref.as_ref(),
        request.space_ref.as_ref(),
        request.media_ref.as_ref(),
        request.quarantine_ref.as_ref(),
    ]
    .into_iter()
    .flatten()
    {
        if !safe_ref(value) {
            return Err("MATRIX_BROKER_EXACT_BINDING_INVALID");
        }
    }
    if request.adapter_ref != "adapter-ref:matrix-rust-broker:v1"
        || request.safe_disable_ref != "safe-disable-ref:matrix-messenger:enabled"
        || request.kill_switch_ref != "kill-switch-ref:matrix-messenger:clear"
    {
        return Err("MATRIX_BROKER_AUTHORITY_POSTURE_INVALID");
    }
    validate_operation_scope(request)?;
    Ok(())
}

fn validate_operation_scope(request: &BrokerRequest) -> Result<(), &'static str> {
    let no_safe_target = request.room_ref.is_none()
        && request.event_ref.is_none()
        && request.transaction_ref.is_none()
        && request.member_ref.is_none()
        && request.space_ref.is_none()
        && request.media_ref.is_none()
        && request.quarantine_ref.is_none();
    let no_runtime_secret = request.homeserver_url.is_none()
        && request.username.is_none()
        && request.password.is_none()
        && request.room_id.is_none()
        && request.event_id.is_none()
        && request.transaction_id.is_none()
        && request.body.is_none()
        && request.formatted_body.is_none()
        && request.mention_user_ids.is_none()
        && request.relation_event_id.is_none()
        && request.reaction_key.is_none()
        && request.typing_active.is_none();
    let no_rooms_media_secret = request.member_id.is_none()
        && request.space_id.is_none()
        && request.room_name.is_none()
        && request.desired_state.is_none()
        && request.prior_state.is_none()
        && request.media_uri.is_none()
        && request.media_type.is_none()
        && request.media_b64.is_none();
    let no_identity_secret = request.username.is_none() && request.password.is_none();
    let no_message_content = request.body.is_none()
        && request.formatted_body.is_none()
        && request.mention_user_ids.is_none()
        && request.relation_event_id.is_none()
        && request.reaction_key.is_none();
    let exact_relation = request.event_id.as_ref().map(SecretString::as_str)
        == request.relation_event_id.as_ref().map(SecretString::as_str);
    let valid = match request.operation {
        BrokerOperation::ProtocolProbe => {
            no_safe_target
                && request.secret_kind.is_none()
                && no_runtime_secret
                && no_rooms_media_secret
        }
        BrokerOperation::KeychainCreate
        | BrokerOperation::KeychainProbe
        | BrokerOperation::KeychainRotate
        | BrokerOperation::KeychainDelete => {
            no_safe_target
                && request.secret_kind.is_some()
                && no_runtime_secret
                && no_rooms_media_secret
        }
        BrokerOperation::SessionLogin => {
            no_safe_target
                && request.secret_kind.is_none()
                && request.homeserver_url.is_some()
                && request.username.is_some()
                && request.password.is_some()
                && request.room_id.is_none()
                && request.event_id.is_none()
                && request.transaction_id.is_none()
                && no_message_content
                && request.typing_active.is_none()
                && no_rooms_media_secret
        }
        BrokerOperation::SessionRestore | BrokerOperation::SessionLogout => {
            no_safe_target
                && request.secret_kind.is_none()
                && request.homeserver_url.is_some()
                && no_identity_secret
                && request.room_id.is_none()
                && request.event_id.is_none()
                && request.transaction_id.is_none()
                && no_message_content
                && request.typing_active.is_none()
                && no_rooms_media_secret
        }
        BrokerOperation::Send => {
            exact_safe_scope(request, true, false, true, false, false, false, false)
                && request.secret_kind.is_none()
                && request.homeserver_url.is_some()
                && no_identity_secret
                && request.room_id.is_some()
                && request.event_id.is_none()
                && request.transaction_id.is_some()
                && request.body.is_some()
                && request.relation_event_id.is_none()
                && request.reaction_key.is_none()
                && request.typing_active.is_none()
                && no_rooms_media_secret
        }
        BrokerOperation::Reply | BrokerOperation::Thread | BrokerOperation::Edit => {
            exact_safe_scope(request, true, true, true, false, false, false, false)
                && request.secret_kind.is_none()
                && request.homeserver_url.is_some()
                && no_identity_secret
                && request.room_id.is_some()
                && request.event_id.is_some()
                && request.transaction_id.is_some()
                && request.body.is_some()
                && request.relation_event_id.is_some()
                && exact_relation
                && request.reaction_key.is_none()
                && request.typing_active.is_none()
                && no_rooms_media_secret
        }
        BrokerOperation::Reaction => {
            exact_safe_scope(request, true, true, true, false, false, false, false)
                && request.secret_kind.is_none()
                && request.homeserver_url.is_some()
                && no_identity_secret
                && request.room_id.is_some()
                && request.event_id.is_some()
                && request.transaction_id.is_some()
                && request.body.is_none()
                && request.formatted_body.is_none()
                && request.mention_user_ids.is_none()
                && request.relation_event_id.is_some()
                && exact_relation
                && request.reaction_key.is_some()
                && request.typing_active.is_none()
                && no_rooms_media_secret
        }
        BrokerOperation::Redaction => {
            exact_safe_scope(request, true, true, true, false, false, false, false)
                && request.secret_kind.is_none()
                && request.homeserver_url.is_some()
                && no_identity_secret
                && request.room_id.is_some()
                && request.event_id.is_some()
                && request.transaction_id.is_some()
                && no_message_content
                && request.typing_active.is_none()
                && no_rooms_media_secret
        }
        BrokerOperation::Typing => {
            exact_safe_scope(request, true, false, false, false, false, false, false)
                && request.secret_kind.is_none()
                && request.homeserver_url.is_some()
                && no_identity_secret
                && request.room_id.is_some()
                && request.event_id.is_none()
                && request.transaction_id.is_none()
                && no_message_content
                && request.typing_active.is_some()
                && no_rooms_media_secret
        }
        BrokerOperation::ReadReceipt => {
            exact_safe_scope(request, true, true, false, false, false, false, false)
                && request.secret_kind.is_none()
                && request.homeserver_url.is_some()
                && no_identity_secret
                && request.room_id.is_some()
                && request.event_id.is_some()
                && request.transaction_id.is_none()
                && no_message_content
                && request.typing_active.is_none()
                && no_rooms_media_secret
        }
        BrokerOperation::DmCreate => {
            exact_safe_scope(request, false, false, true, true, false, false, false)
                && request.member_id.is_some()
                && request.transaction_id.is_some()
                && request.homeserver_url.is_some()
                && request.secret_kind.is_none()
                && no_identity_secret
                && no_message_content
                && request.room_id.is_none()
                && request.event_id.is_none()
                && request.typing_active.is_none()
                && request.space_id.is_none()
                && request.room_name.is_none()
                && request.desired_state.is_none()
                && request.prior_state.is_none()
                && request.media_uri.is_none()
                && request.media_type.is_none()
                && request.media_b64.is_none()
        }
        BrokerOperation::RoomCreate => {
            exact_safe_scope(request, false, false, true, false, false, false, false)
                && request.transaction_id.is_some()
                && request.homeserver_url.is_some()
                && request.secret_kind.is_none()
                && no_identity_secret
                && no_message_content
                && request.room_id.is_none()
                && request.event_id.is_none()
                && request.typing_active.is_none()
                && request.room_name.is_some()
                && request.member_id.is_none()
                && request.space_id.is_none()
                && request.desired_state.is_none()
                && request.prior_state.is_none()
                && request.media_uri.is_none()
                && request.media_type.is_none()
                && request.media_b64.is_none()
        }
        BrokerOperation::RoomJoin
        | BrokerOperation::InviteAccept
        | BrokerOperation::InviteReject => {
            exact_room_transaction_scope(request)
                && exact_safe_scope(request, true, false, true, false, false, false, false)
                && request.member_id.is_none()
                && request.member_ref.is_none()
                && request.event_id.is_none()
                && request.event_ref.is_none()
                && request.space_id.is_none()
                && request.space_ref.is_none()
                && request.desired_state.is_none()
                && request.prior_state.is_some()
                && request.media_uri.is_none()
                && request.media_type.is_none()
                && request.media_b64.is_none()
        }
        BrokerOperation::RoomLeave => {
            exact_room_transaction_scope(request)
                && exact_safe_scope(request, true, false, true, false, false, false, false)
                && request.member_id.is_none()
                && request.event_id.is_none()
                && request.space_id.is_none()
                && request.desired_state.is_none()
                && request.prior_state.is_some()
                && request.media_uri.is_none()
                && request.media_type.is_none()
                && request.media_b64.is_none()
        }
        BrokerOperation::InviteSend => {
            exact_room_transaction_scope(request)
                && exact_safe_scope(request, true, false, true, true, false, false, false)
                && request.member_ref.is_some()
                && request.member_id.is_some()
                && request.event_id.is_none()
                && request.event_ref.is_none()
                && request.space_id.is_none()
                && request.space_ref.is_none()
                && request.desired_state.is_none()
                && request.prior_state.is_some()
                && request.media_uri.is_none()
                && request.media_type.is_none()
                && request.media_b64.is_none()
        }
        BrokerOperation::InviteWithdraw => {
            exact_room_transaction_scope(request)
                && exact_safe_scope(request, true, false, true, true, false, false, false)
                && request.member_id.is_some()
                && request.event_id.is_none()
                && request.space_id.is_none()
                && request.desired_state.is_none()
                && request.prior_state.is_some()
                && request.media_uri.is_none()
                && request.media_type.is_none()
                && request.media_b64.is_none()
        }
        BrokerOperation::RoomPowerRoleWrite => {
            exact_room_transaction_scope(request)
                && exact_safe_scope(request, true, false, true, true, false, false, false)
                && request.member_ref.is_some()
                && request.member_id.is_some()
                && request.event_id.is_none()
                && request.event_ref.is_none()
                && request.space_id.is_none()
                && request.space_ref.is_none()
                && request.desired_state.is_some()
                && request.prior_state.is_some()
                && request.media_uri.is_none()
                && request.media_type.is_none()
                && request.media_b64.is_none()
        }
        BrokerOperation::SpaceMappingWrite => {
            exact_room_transaction_scope(request)
                && exact_safe_scope(request, true, false, true, false, true, false, false)
                && request.space_ref.is_some()
                && request.space_id.is_some()
                && request.desired_state.is_some()
                && request.prior_state.is_some()
                && request.member_id.is_none()
                && request.member_ref.is_none()
                && request.event_id.is_none()
                && request.event_ref.is_none()
                && request.media_uri.is_none()
                && request.media_type.is_none()
                && request.media_b64.is_none()
        }
        BrokerOperation::NotificationSettingsWrite
        | BrokerOperation::HistoryVisibilityWrite
        | BrokerOperation::AccountRoomPreferenceWrite => {
            exact_room_transaction_scope(request)
                && exact_safe_scope(request, true, false, true, false, false, false, false)
                && request.desired_state.is_some()
                && request.member_id.is_none()
                && request.member_ref.is_none()
                && request.event_id.is_none()
                && request.event_ref.is_none()
                && request.space_id.is_none()
                && request.space_ref.is_none()
                && request.prior_state.is_some()
                && request.media_uri.is_none()
                && request.media_type.is_none()
                && request.media_b64.is_none()
        }
        BrokerOperation::PinWrite => {
            exact_room_transaction_scope(request)
                && exact_safe_scope(request, true, true, true, false, false, false, false)
                && request.event_ref.is_some()
                && request.event_id.is_some()
                && request.desired_state.is_some()
                && request.member_id.is_none()
                && request.member_ref.is_none()
                && request.space_id.is_none()
                && request.space_ref.is_none()
                && request.prior_state.is_some()
                && request.media_uri.is_none()
                && request.media_type.is_none()
                && request.media_b64.is_none()
        }
        BrokerOperation::MediaUpload => {
            exact_room_transaction_scope(request)
                && exact_safe_scope(request, true, false, true, false, false, true, false)
                && request.media_type.is_some()
                && request.media_b64.is_some()
                && request.media_uri.is_none()
                && request.member_id.is_none()
                && request.member_ref.is_none()
                && request.event_id.is_none()
                && request.event_ref.is_none()
                && request.space_id.is_none()
                && request.space_ref.is_none()
                && request.desired_state.is_none()
                && request.prior_state.is_none()
        }
        BrokerOperation::MediaDownloadQuarantine => {
            exact_room_transaction_scope(request)
                && exact_safe_scope(request, true, true, true, false, false, true, true)
                && request.media_uri.is_some()
                && request.media_type.is_some()
                && request.media_b64.is_none()
                && request.member_id.is_none()
                && request.member_ref.is_none()
                && request.event_id.is_some()
                && request.event_ref.is_some()
                && request.space_id.is_none()
                && request.space_ref.is_none()
                && request.desired_state.is_none()
                && request.prior_state.is_none()
        }
    };
    if !valid {
        return Err("MATRIX_BROKER_OPERATION_SCOPE_INVALID");
    }
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn exact_safe_scope(
    request: &BrokerRequest,
    room: bool,
    event: bool,
    transaction: bool,
    member: bool,
    space: bool,
    media: bool,
    quarantine: bool,
) -> bool {
    request.room_ref.is_some() == room
        && request.event_ref.is_some() == event
        && request.transaction_ref.is_some() == transaction
        && request.member_ref.is_some() == member
        && request.space_ref.is_some() == space
        && request.media_ref.is_some() == media
        && request.quarantine_ref.is_some() == quarantine
}

fn exact_room_transaction_scope(request: &BrokerRequest) -> bool {
    request.room_ref.is_some()
        && request.transaction_ref.is_some()
        && request.homeserver_url.is_some()
        && request.room_id.is_some()
        && request.transaction_id.is_some()
        && request.secret_kind.is_none()
        && request.username.is_none()
        && request.password.is_none()
        && request.body.is_none()
        && request.formatted_body.is_none()
        && request.mention_user_ids.is_none()
        && request.relation_event_id.is_none()
        && request.reaction_key.is_none()
        && request.typing_active.is_none()
        && request.room_name.is_none()
}

fn safe_ref(value: &str) -> bool {
    (8..=256).contains(&value.len())
        && value.is_ascii()
        && value.bytes().all(|item| {
            item.is_ascii_alphanumeric() || matches!(item, b':' | b'-' | b'_' | b'.' | b'/')
        })
        && value.contains(':')
}

fn now_ms() -> Result<u64, &'static str> {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|_| "MATRIX_BROKER_CLOCK_INVALID")?
        .as_millis()
        .try_into()
        .map_err(|_| "MATRIX_BROKER_CLOCK_INVALID")
}

#[cfg(test)]
mod tests {
    use super::*;

    fn request(operation: BrokerOperation) -> BrokerRequest {
        let now = now_ms().unwrap();
        BrokerRequest {
            protocol_version: PROTOCOL_VERSION.to_owned(),
            request_ref: "request-ref:matrix-broker:test".to_owned(),
            request_fingerprint_ref: "request-fingerprint-ref:matrix-broker:test".to_owned(),
            nonce: "a".repeat(64),
            issued_at_ms: now.saturating_sub(1),
            deadline_ms: now + 30_000,
            operation,
            account_ref: "account-ref:matrix:test".to_owned(),
            homeserver_ref: "homeserver-ref:matrix:test".to_owned(),
            device_ref: "device-ref:matrix:test".to_owned(),
            room_ref: None,
            event_ref: None,
            transaction_ref: None,
            member_ref: None,
            space_ref: None,
            media_ref: None,
            quarantine_ref: None,
            approval_ref: "approval-ref:matrix:test".to_owned(),
            lease_ref: "authority-lease-ref:matrix:test".to_owned(),
            idempotency_ref: "idempotency-ref:matrix:test".to_owned(),
            adapter_ref: "adapter-ref:matrix-rust-broker:v1".to_owned(),
            budget_ref: "budget-ref:matrix:test".to_owned(),
            readiness_ref: "readiness-ref:matrix:test".to_owned(),
            safe_disable_ref: "safe-disable-ref:matrix-messenger:enabled".to_owned(),
            kill_switch_ref: "kill-switch-ref:matrix-messenger:clear".to_owned(),
            secret_kind: None,
            homeserver_url: None,
            username: None,
            password: None,
            room_id: None,
            event_id: None,
            transaction_id: None,
            body: None,
            formatted_body: None,
            mention_user_ids: None,
            relation_event_id: None,
            reaction_key: None,
            typing_active: None,
            member_id: None,
            space_id: None,
            room_name: None,
            desired_state: None,
            prior_state: None,
            media_uri: None,
            media_type: None,
            media_b64: None,
        }
    }

    #[test]
    fn safe_refs_reject_content_and_spaces() {
        assert!(safe_ref("account-ref:matrix:0123456789"));
        assert!(!safe_ref("raw message body"));
        assert!(!safe_ref("short"));
    }

    #[test]
    fn operation_classifies_network_mutations() {
        assert!(BrokerOperation::Send.is_network_mutation());
        assert!(BrokerOperation::DmCreate.is_network_mutation());
        assert!(BrokerOperation::MediaDownloadQuarantine.is_network_mutation());
        assert!(!BrokerOperation::KeychainProbe.is_network_mutation());
        assert!(!BrokerOperation::SessionRestore.is_network_mutation());
    }

    #[test]
    fn operation_scope_rejects_secret_smuggling() {
        let mut probe = request(BrokerOperation::ProtocolProbe);
        assert!(validate_operation_scope(&probe).is_ok());
        probe.username = Some(SecretString("smuggled".to_owned()));
        assert_eq!(
            validate_operation_scope(&probe),
            Err("MATRIX_BROKER_OPERATION_SCOPE_INVALID")
        );
    }

    #[test]
    fn send_scope_binds_safe_and_raw_targets() {
        let mut send = request(BrokerOperation::Send);
        send.room_ref = Some("room-ref:matrix:test".to_owned());
        send.transaction_ref = Some("transaction-ref:matrix:test".to_owned());
        send.homeserver_url = Some(SecretString("http://127.0.0.1:18008".to_owned()));
        send.room_id = Some(SecretString("!room:localhost".to_owned()));
        send.transaction_id = Some(SecretString("transaction-test".to_owned()));
        send.body = Some(SecretString("transient body".to_owned()));
        assert!(validate_operation_scope(&send).is_ok());
        send.room_ref = None;
        assert_eq!(
            validate_operation_scope(&send),
            Err("MATRIX_BROKER_OPERATION_SCOPE_INVALID")
        );
    }

    #[test]
    fn receipt_scope_requires_raw_room_and_event() {
        let mut receipt = request(BrokerOperation::ReadReceipt);
        receipt.room_ref = Some("room-ref:matrix:test".to_owned());
        receipt.event_ref = Some("event-ref:matrix:test".to_owned());
        receipt.homeserver_url = Some(SecretString("http://127.0.0.1:18008".to_owned()));
        receipt.room_id = Some(SecretString("!room:localhost".to_owned()));
        receipt.event_id = Some(SecretString("$event:localhost".to_owned()));
        assert!(validate_operation_scope(&receipt).is_ok());
        receipt.room_id = None;
        assert_eq!(
            validate_operation_scope(&receipt),
            Err("MATRIX_BROKER_OPERATION_SCOPE_INVALID")
        );
    }

    #[test]
    fn room_create_scope_rejects_safe_and_transient_smuggling() {
        let mut create = request(BrokerOperation::RoomCreate);
        create.transaction_ref = Some("transaction-ref:matrix:test".to_owned());
        create.homeserver_url = Some(SecretString("http://127.0.0.1:18008".to_owned()));
        create.transaction_id = Some(SecretString("transaction-test".to_owned()));
        create.room_name = Some(SecretString("Exact room".to_owned()));
        assert!(validate_operation_scope(&create).is_ok());
        create.desired_state = Some(SecretString("smuggled".to_owned()));
        assert_eq!(
            validate_operation_scope(&create),
            Err("MATRIX_BROKER_OPERATION_SCOPE_INVALID")
        );
        create.desired_state = None;
        create.room_ref = Some("room-ref:matrix:smuggled".to_owned());
        assert_eq!(
            validate_operation_scope(&create),
            Err("MATRIX_BROKER_OPERATION_SCOPE_INVALID")
        );
    }

    #[test]
    fn media_download_scope_rejects_unrelated_member_binding() {
        let mut download = request(BrokerOperation::MediaDownloadQuarantine);
        download.room_ref = Some("room-ref:matrix:test".to_owned());
        download.event_ref = Some("event-ref:matrix:test".to_owned());
        download.transaction_ref = Some("transaction-ref:matrix:test".to_owned());
        download.media_ref = Some("media-ref:matrix:test".to_owned());
        download.quarantine_ref = Some("quarantine-ref:matrix:test".to_owned());
        download.homeserver_url = Some(SecretString("http://127.0.0.1:18008".to_owned()));
        download.room_id = Some(SecretString("!room:localhost".to_owned()));
        download.event_id = Some(SecretString("$event:localhost".to_owned()));
        download.transaction_id = Some(SecretString("transaction-test".to_owned()));
        download.media_uri = Some(SecretString("mxc://localhost/media".to_owned()));
        download.media_type = Some(SecretString("image/png".to_owned()));
        assert!(validate_operation_scope(&download).is_ok());
        download.member_ref = Some("member-ref:matrix:smuggled".to_owned());
        assert_eq!(
            validate_operation_scope(&download),
            Err("MATRIX_BROKER_OPERATION_SCOPE_INVALID")
        );
    }
}
