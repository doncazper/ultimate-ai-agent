use std::{fs::File, io::Write, os::unix::fs::MetadataExt, path::Path};

use base64::{Engine as _, engine::general_purpose::STANDARD as BASE64};

use matrix_sdk::{
    Client, RoomState,
    authentication::matrix::MatrixSession,
    config::SyncSettings,
    deserialized_responses::SyncOrStrippedState,
    media::{MediaFormat, MediaRequestParameters},
    notification_settings::RoomNotificationMode,
    ruma::{
        Int, OwnedEventId, OwnedMxcUri, OwnedRoomId, OwnedTransactionId, OwnedUserId,
        api::client::receipt::create_receipt::v3::ReceiptType,
        api::client::room::create_room,
        events::{
            SyncStateEvent,
            reaction::ReactionEventContent,
            receipt::ReceiptThread,
            relation::Annotation,
            room::{MediaSource, history_visibility::HistoryVisibility, member::MembershipState},
            space::child::SpaceChildEventContent,
        },
    },
};
use rustix::{
    fs::{AtFlags, Mode, OFlags, mkdirat, open, openat, unlinkat},
    io::Errno,
    process::geteuid,
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
    pub byte_count: Option<usize>,
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
    if matches!(operation, BrokerOperation::DmCreate) {
        let member_id = parse_user_id(request)?;
        let room = client
            .create_dm(&member_id)
            .await
            .map_err(|_| ExecutionError::uncertain("MATRIX_DM_CREATE_OUTCOME_UNCERTAIN"))?;
        return Ok(success(
            "server_acknowledged",
            Some(private_room_ref(room.room_id().as_str())),
        ));
    }
    if matches!(operation, BrokerOperation::RoomCreate) {
        let room_name = required_secret(&request.room_name, "MATRIX_ROOM_NAME_REQUIRED")?;
        if room_name.is_empty()
            || room_name.chars().count() > 128
            || room_name.contains(['\n', '\r', '\0'])
        {
            return Err(ExecutionError::safe("MATRIX_ROOM_NAME_INVALID"));
        }
        let mut create_request = create_room::v3::Request::new();
        create_request.name = Some(room_name.to_owned());
        let room = client
            .create_room(create_request)
            .await
            .map_err(|_| ExecutionError::uncertain("MATRIX_ROOM_CREATE_OUTCOME_UNCERTAIN"))?;
        return Ok(success(
            "server_acknowledged",
            Some(private_room_ref(room.room_id().as_str())),
        ));
    }
    let room_id = required_secret(&request.room_id, "MATRIX_ROOM_ID_REQUIRED")?;
    let room_id = OwnedRoomId::try_from(room_id)
        .map_err(|_| ExecutionError::safe("MATRIX_ROOM_ID_INVALID"))?;
    let room_server = room_id
        .server_name()
        .ok_or_else(|| ExecutionError::safe("MATRIX_PUBLIC_FEDERATION_TARGET_DENIED"))?;
    ensure_local_matrix_server(room_server.as_str())?;
    if matches!(
        operation,
        BrokerOperation::RoomJoin | BrokerOperation::InviteAccept
    ) {
        let current_room = client.get_room(&room_id);
        let current_state = match current_room.as_ref().map(|room| room.state()) {
            Some(RoomState::Joined) => "joined",
            Some(RoomState::Left) => "left",
            Some(RoomState::Invited) => "invited",
            Some(RoomState::Knocked) => "knocked",
            Some(RoomState::Banned) => "banned",
            None => "absent",
        };
        require_prior_state(request, current_state)?;
        if matches!(operation, BrokerOperation::InviteAccept) && current_state != "invited" {
            return Err(ExecutionError::safe(
                "MATRIX_INVITE_STATE_PRECONDITION_FAILED",
            ));
        }
        if matches!(current_state, "joined" | "banned") {
            return Err(ExecutionError::safe(
                "MATRIX_ROOM_STATE_PRECONDITION_FAILED",
            ));
        }
        let room = client
            .join_room_by_id(&room_id)
            .await
            .map_err(|_| ExecutionError::uncertain("MATRIX_ROOM_JOIN_OUTCOME_UNCERTAIN"))?;
        return Ok(success(
            "server_acknowledged",
            Some(private_room_ref(room.room_id().as_str())),
        ));
    }
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
        BrokerOperation::RoomLeave => {
            require_prior_state(request, "joined")?;
            if room.state() != RoomState::Joined {
                return Err(ExecutionError::safe(
                    "MATRIX_ROOM_STATE_PRECONDITION_FAILED",
                ));
            }
            room.leave()
                .await
                .map_err(|_| ExecutionError::uncertain("MATRIX_ROOM_LEAVE_OUTCOME_UNCERTAIN"))?;
            Ok(success("server_acknowledged", None))
        }
        BrokerOperation::InviteReject => {
            require_prior_state(request, "invited")?;
            if room.state() != RoomState::Invited {
                return Err(ExecutionError::safe(
                    "MATRIX_INVITE_STATE_PRECONDITION_FAILED",
                ));
            }
            room.leave()
                .await
                .map_err(|_| ExecutionError::uncertain("MATRIX_ROOM_LEAVE_OUTCOME_UNCERTAIN"))?;
            Ok(success("server_acknowledged", None))
        }
        BrokerOperation::InviteSend => {
            let member_id = parse_user_id(request)?;
            let current_member = room
                .get_member_no_sync(&member_id)
                .await
                .map_err(|_| ExecutionError::safe("MATRIX_MEMBER_STATE_UNAVAILABLE"))?;
            let current_membership = current_member
                .as_ref()
                .map(|member| member.membership().as_str())
                .unwrap_or("absent");
            require_prior_state(request, current_membership)?;
            if matches!(current_membership, "invite" | "join" | "ban") {
                return Err(ExecutionError::safe(
                    "MATRIX_INVITE_STATE_PRECONDITION_FAILED",
                ));
            }
            room.invite_user_by_id(&member_id)
                .await
                .map_err(|_| ExecutionError::uncertain("MATRIX_INVITE_OUTCOME_UNCERTAIN"))?;
            Ok(success("server_acknowledged", None))
        }
        BrokerOperation::InviteWithdraw => {
            let member_id = parse_user_id(request)?;
            require_prior_state(request, "invited")?;
            let member = room
                .get_member_no_sync(&member_id)
                .await
                .map_err(|_| ExecutionError::safe("MATRIX_INVITE_STATE_UNAVAILABLE"))?
                .ok_or_else(|| ExecutionError::safe("MATRIX_INVITE_STATE_UNAVAILABLE"))?;
            if member.membership() != &MembershipState::Invite {
                return Err(ExecutionError::safe(
                    "MATRIX_INVITE_STATE_PRECONDITION_FAILED",
                ));
            }
            room.kick_user(&member_id, None).await.map_err(|_| {
                ExecutionError::uncertain("MATRIX_INVITE_WITHDRAW_OUTCOME_UNCERTAIN")
            })?;
            Ok(success("server_acknowledged", None))
        }
        BrokerOperation::RoomPowerRoleWrite => {
            let member_id = parse_user_id(request)?;
            let own_id = client
                .user_id()
                .ok_or_else(|| ExecutionError::safe("MATRIX_SESSION_USER_ID_REQUIRED"))?;
            let levels = room
                .power_levels()
                .await
                .map_err(|_| ExecutionError::safe("MATRIX_POWER_LEVELS_UNAVAILABLE"))?;
            let own_level = levels
                .users
                .get(own_id)
                .copied()
                .unwrap_or(levels.users_default);
            let current_level = levels
                .users
                .get(&member_id)
                .copied()
                .unwrap_or(levels.users_default);
            let desired = validated_power_change(
                required_secret(&request.desired_state, "MATRIX_POWER_LEVEL_REQUIRED")?,
                required_secret(&request.prior_state, "MATRIX_POWER_PRIOR_STATE_REQUIRED")?,
                current_level,
                own_level,
            )?;
            let response = room
                .update_power_levels(vec![(&member_id, desired)])
                .await
                .map_err(|_| ExecutionError::uncertain("MATRIX_POWER_WRITE_OUTCOME_UNCERTAIN"))?;
            Ok(success(
                "server_acknowledged",
                Some(private_event_ref(response.event_id.as_str())),
            ))
        }
        BrokerOperation::SpaceMappingWrite => {
            let child_id = required_secret(&request.space_id, "MATRIX_SPACE_CHILD_ID_REQUIRED")?;
            let child_id = OwnedRoomId::try_from(child_id)
                .map_err(|_| ExecutionError::safe("MATRIX_SPACE_CHILD_ID_INVALID"))?;
            let child_server = child_id
                .server_name()
                .ok_or_else(|| ExecutionError::safe("MATRIX_PUBLIC_FEDERATION_TARGET_DENIED"))?;
            ensure_local_matrix_server(child_server.as_str())?;
            let desired = required_secret(
                &request.desired_state,
                "MATRIX_SPACE_MAPPING_STATE_REQUIRED",
            )?;
            let current = room
                .get_state_event_static_for_key::<SpaceChildEventContent, _>(&child_id)
                .await
                .map_err(|_| ExecutionError::safe("MATRIX_SPACE_MAPPING_STATE_UNAVAILABLE"))?;
            let present = match current.and_then(|event| event.deserialize().ok()) {
                Some(SyncOrStrippedState::Sync(SyncStateEvent::Original(event))) => {
                    !event.content.via.is_empty()
                }
                _ => false,
            };
            require_prior_state(request, if present { "present" } else { "absent" })?;
            let content = match desired {
                "add" => {
                    let server_name = child_id
                        .server_name()
                        .ok_or_else(|| ExecutionError::safe("MATRIX_SPACE_CHILD_ID_INVALID"))?;
                    json!({"via": [server_name.as_str()]})
                }
                "remove" => json!({"via": []}),
                _ => return Err(ExecutionError::safe("MATRIX_SPACE_MAPPING_STATE_INVALID")),
            };
            let response = room
                .send_state_event_raw("m.space.child", child_id.as_str(), content)
                .await
                .map_err(|_| ExecutionError::uncertain("MATRIX_SPACE_MAPPING_OUTCOME_UNCERTAIN"))?;
            Ok(success(
                "server_acknowledged",
                Some(private_event_ref(response.event_id.as_str())),
            ))
        }
        BrokerOperation::NotificationSettingsWrite => {
            let desired =
                required_secret(&request.desired_state, "MATRIX_NOTIFICATION_MODE_REQUIRED")?;
            let mode = match desired {
                "all_messages" => RoomNotificationMode::AllMessages,
                "mentions" => RoomNotificationMode::MentionsAndKeywordsOnly,
                "mute" => RoomNotificationMode::Mute,
                _ => return Err(ExecutionError::safe("MATRIX_NOTIFICATION_MODE_INVALID")),
            };
            let current = match room.user_defined_notification_mode().await {
                Some(RoomNotificationMode::AllMessages) => "all_messages",
                Some(RoomNotificationMode::MentionsAndKeywordsOnly) => "mentions",
                Some(RoomNotificationMode::Mute) => "mute",
                None => "default",
            };
            require_prior_state(request, current)?;
            client
                .notification_settings()
                .await
                .set_room_notification_mode(&room_id, mode)
                .await
                .map_err(|_| {
                    ExecutionError::uncertain("MATRIX_NOTIFICATION_WRITE_OUTCOME_UNCERTAIN")
                })?;
            Ok(success("server_acknowledged", None))
        }
        BrokerOperation::HistoryVisibilityWrite => {
            let desired =
                required_secret(&request.desired_state, "MATRIX_HISTORY_VISIBILITY_REQUIRED")?;
            let visibility = match desired {
                "invited" => HistoryVisibility::Invited,
                "joined" => HistoryVisibility::Joined,
                "shared" => HistoryVisibility::Shared,
                "world_readable" => HistoryVisibility::WorldReadable,
                _ => return Err(ExecutionError::safe("MATRIX_HISTORY_VISIBILITY_INVALID")),
            };
            let current = room
                .history_visibility()
                .map(|value| value.as_str().to_owned())
                .unwrap_or_else(|| "missing".to_owned());
            require_prior_state(request, &current)?;
            room.privacy_settings()
                .update_room_history_visibility(visibility)
                .await
                .map_err(|_| ExecutionError::uncertain("MATRIX_HISTORY_WRITE_OUTCOME_UNCERTAIN"))?;
            Ok(success("server_acknowledged", None))
        }
        BrokerOperation::PinWrite => {
            let event_id = parse_event_id(request)?;
            let desired = required_secret(&request.desired_state, "MATRIX_PIN_STATE_REQUIRED")?;
            let pinned = room
                .load_pinned_events()
                .await
                .map_err(|_| ExecutionError::safe("MATRIX_PIN_STATE_UNAVAILABLE"))?
                .unwrap_or_default()
                .contains(&event_id);
            require_prior_state(request, if pinned { "pinned" } else { "unpinned" })?;
            match desired {
                "pin" => {
                    room.pin_event(&event_id).await.map_err(|_| {
                        ExecutionError::uncertain("MATRIX_PIN_WRITE_OUTCOME_UNCERTAIN")
                    })?;
                }
                "unpin" => {
                    room.unpin_event(&event_id).await.map_err(|_| {
                        ExecutionError::uncertain("MATRIX_PIN_WRITE_OUTCOME_UNCERTAIN")
                    })?;
                }
                _ => return Err(ExecutionError::safe("MATRIX_PIN_STATE_INVALID")),
            }
            Ok(success("server_acknowledged", None))
        }
        BrokerOperation::AccountRoomPreferenceWrite => {
            let desired =
                required_secret(&request.desired_state, "MATRIX_ROOM_PREFERENCE_REQUIRED")?;
            let current = match desired {
                "favorite_on" | "favorite_off" => {
                    if room.is_favourite() {
                        "favorite_on"
                    } else {
                        "favorite_off"
                    }
                }
                "low_priority_on" | "low_priority_off" => {
                    if room.is_low_priority() {
                        "low_priority_on"
                    } else {
                        "low_priority_off"
                    }
                }
                _ => return Err(ExecutionError::safe("MATRIX_ROOM_PREFERENCE_INVALID")),
            };
            require_prior_state(request, current)?;
            match desired {
                "favorite_on" => room.set_is_favourite(true, None).await,
                "favorite_off" => room.set_is_favourite(false, None).await,
                "low_priority_on" => room.set_is_low_priority(true, None).await,
                "low_priority_off" => room.set_is_low_priority(false, None).await,
                _ => return Err(ExecutionError::safe("MATRIX_ROOM_PREFERENCE_INVALID")),
            }
            .map_err(|_| ExecutionError::uncertain("MATRIX_ROOM_PREFERENCE_OUTCOME_UNCERTAIN"))?;
            Ok(success("server_acknowledged", None))
        }
        BrokerOperation::MediaUpload => upload_media(request, &client).await,
        BrokerOperation::MediaDownloadQuarantine => {
            download_media(request, &client, scope_root).await
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

fn parse_user_id(request: &BrokerRequest) -> Result<OwnedUserId, ExecutionError> {
    let value = required_secret(&request.member_id, "MATRIX_MEMBER_ID_REQUIRED")?;
    let user_id = OwnedUserId::try_from(value)
        .map_err(|_| ExecutionError::safe("MATRIX_MEMBER_ID_INVALID"))?;
    ensure_local_matrix_server(user_id.server_name().as_str())?;
    Ok(user_id)
}

async fn upload_media(
    request: &BrokerRequest,
    client: &Client,
) -> Result<ExecutionResult, ExecutionError> {
    let media_type = allowed_media_type(request)?;
    let encoded = required_secret(&request.media_b64, "MATRIX_MEDIA_PAYLOAD_REQUIRED")?;
    if encoded.len() > 32 * 1024 + 1024 {
        return Err(ExecutionError::safe("MATRIX_MEDIA_PAYLOAD_OVERSIZE"));
    }
    let data = BASE64
        .decode(encoded)
        .map_err(|_| ExecutionError::safe("MATRIX_MEDIA_PAYLOAD_INVALID"))?;
    if data.is_empty() || data.len() > 24_576 {
        return Err(ExecutionError::safe("MATRIX_MEDIA_PAYLOAD_OVERSIZE"));
    }
    let response = client
        .media()
        .upload(&media_type, data, None)
        .await
        .map_err(|_| ExecutionError::uncertain("MATRIX_MEDIA_UPLOAD_OUTCOME_UNCERTAIN"))?;
    Ok(success(
        "server_acknowledged",
        Some(private_media_ref(response.content_uri.as_str())),
    ))
}

async fn download_media(
    request: &BrokerRequest,
    client: &Client,
    scope_root: &Path,
) -> Result<ExecutionResult, ExecutionError> {
    let _media_type = allowed_media_type(request)?;
    let uri = required_secret(&request.media_uri, "MATRIX_MEDIA_URI_REQUIRED")?;
    let uri =
        OwnedMxcUri::try_from(uri).map_err(|_| ExecutionError::safe("MATRIX_MEDIA_URI_INVALID"))?;
    let media_server = uri
        .server_name()
        .map_err(|_| ExecutionError::safe("MATRIX_MEDIA_URI_INVALID"))?;
    ensure_local_matrix_server(media_server.as_str())?;
    let parameters = MediaRequestParameters {
        source: MediaSource::Plain(uri),
        format: MediaFormat::File,
    };
    let data = client
        .media()
        .get_media_content(&parameters, false)
        .await
        .map_err(|_| ExecutionError::safe("MATRIX_MEDIA_DOWNLOAD_FAILED"))?;
    if data.is_empty() || data.len() > 24_576 {
        return Err(ExecutionError::safe("MATRIX_MEDIA_DOWNLOAD_SIZE_DENIED"));
    }
    let quarantine_ref = request
        .quarantine_ref
        .as_ref()
        .ok_or_else(|| ExecutionError::safe("MATRIX_MEDIA_QUARANTINE_REF_REQUIRED"))?;
    let scope_directory = open_private_directory(scope_root)?;
    let quarantine_directory = open_private_quarantine_directory(&scope_directory)?;
    let name = format!(
        "{}.quarantine",
        hex::encode(Sha256::digest(quarantine_ref.as_bytes()))
    );
    let file_descriptor = openat(
        &quarantine_directory,
        name.as_str(),
        OFlags::WRONLY | OFlags::CREATE | OFlags::EXCL | OFlags::NOFOLLOW | OFlags::CLOEXEC,
        Mode::from(0o600),
    )
    .map_err(|_| ExecutionError::safe("MATRIX_MEDIA_QUARANTINE_PATH_DENIED"))?;
    let mut file = File::from(file_descriptor);
    if let Err(error) = validate_private_regular_file(&file) {
        drop(file);
        unlinkat(&quarantine_directory, name.as_str(), AtFlags::empty())
            .map_err(|_| ExecutionError::safe("MATRIX_MEDIA_QUARANTINE_CLEANUP_FAILED"))?;
        quarantine_directory
            .sync_all()
            .map_err(|_| ExecutionError::safe("MATRIX_MEDIA_QUARANTINE_CLEANUP_FAILED"))?;
        return Err(error);
    }
    if file.write_all(&data).is_err() || file.sync_all().is_err() {
        drop(file);
        unlinkat(&quarantine_directory, name.as_str(), AtFlags::empty())
            .map_err(|_| ExecutionError::safe("MATRIX_MEDIA_QUARANTINE_CLEANUP_FAILED"))?;
        quarantine_directory
            .sync_all()
            .map_err(|_| ExecutionError::safe("MATRIX_MEDIA_QUARANTINE_CLEANUP_FAILED"))?;
        return Err(ExecutionError::safe("MATRIX_MEDIA_QUARANTINE_WRITE_FAILED"));
    }
    drop(file);
    if quarantine_directory.sync_all().is_err() {
        unlinkat(&quarantine_directory, name.as_str(), AtFlags::empty())
            .map_err(|_| ExecutionError::safe("MATRIX_MEDIA_QUARANTINE_CLEANUP_FAILED"))?;
        quarantine_directory
            .sync_all()
            .map_err(|_| ExecutionError::safe("MATRIX_MEDIA_QUARANTINE_CLEANUP_FAILED"))?;
        return Err(ExecutionError::safe("MATRIX_MEDIA_QUARANTINE_WRITE_FAILED"));
    }
    let byte_count = data.len();
    Ok(ExecutionResult {
        outcome: "server_acknowledged",
        event_ref: None,
        byte_count: Some(byte_count),
    })
}

fn allowed_media_type(request: &BrokerRequest) -> Result<mime::Mime, ExecutionError> {
    let value = required_secret(&request.media_type, "MATRIX_MEDIA_TYPE_REQUIRED")?;
    if !matches!(
        value,
        "image/png" | "image/jpeg" | "image/gif" | "text/plain"
    ) {
        return Err(ExecutionError::safe("MATRIX_MEDIA_TYPE_DENIED"));
    }
    value
        .parse()
        .map_err(|_| ExecutionError::safe("MATRIX_MEDIA_TYPE_INVALID"))
}

fn open_private_directory(path: &Path) -> Result<File, ExecutionError> {
    let descriptor = open(
        path,
        OFlags::RDONLY | OFlags::DIRECTORY | OFlags::NOFOLLOW | OFlags::CLOEXEC,
        Mode::empty(),
    )
    .map_err(|_| ExecutionError::safe("MATRIX_MEDIA_SCOPE_ROOT_DENIED"))?;
    let directory = File::from(descriptor);
    validate_private_directory(&directory, "MATRIX_MEDIA_SCOPE_ROOT_DENIED")?;
    Ok(directory)
}

fn open_private_quarantine_directory(parent: &File) -> Result<File, ExecutionError> {
    match mkdirat(parent, "media-quarantine", Mode::from(0o700)) {
        Ok(()) => parent
            .sync_all()
            .map_err(|_| ExecutionError::safe("MATRIX_MEDIA_QUARANTINE_ROOT_DENIED"))?,
        Err(Errno::EXIST) => {}
        Err(_) => return Err(ExecutionError::safe("MATRIX_MEDIA_QUARANTINE_ROOT_DENIED")),
    }
    let descriptor = openat(
        parent,
        "media-quarantine",
        OFlags::RDONLY | OFlags::DIRECTORY | OFlags::NOFOLLOW | OFlags::CLOEXEC,
        Mode::empty(),
    )
    .map_err(|_| ExecutionError::safe("MATRIX_MEDIA_QUARANTINE_ROOT_DENIED"))?;
    let directory = File::from(descriptor);
    validate_private_directory(&directory, "MATRIX_MEDIA_QUARANTINE_ROOT_DENIED")?;
    Ok(directory)
}

fn validate_private_directory(file: &File, code: &'static str) -> Result<(), ExecutionError> {
    let metadata = file.metadata().map_err(|_| ExecutionError::safe(code))?;
    if !metadata.file_type().is_dir()
        || metadata.uid() != geteuid().as_raw()
        || metadata.mode() & 0o077 != 0
    {
        return Err(ExecutionError::safe(code));
    }
    Ok(())
}

fn validate_private_regular_file(file: &File) -> Result<(), ExecutionError> {
    let metadata = file
        .metadata()
        .map_err(|_| ExecutionError::safe("MATRIX_MEDIA_QUARANTINE_PATH_DENIED"))?;
    if !metadata.file_type().is_file()
        || metadata.nlink() != 1
        || metadata.uid() != geteuid().as_raw()
        || metadata.mode() & 0o077 != 0
    {
        return Err(ExecutionError::safe("MATRIX_MEDIA_QUARANTINE_PATH_DENIED"));
    }
    Ok(())
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

fn require_prior_state(request: &BrokerRequest, current: &str) -> Result<(), ExecutionError> {
    let expected = required_secret(&request.prior_state, "MATRIX_PRIOR_STATE_REQUIRED")?;
    if expected != current {
        return Err(ExecutionError::safe("MATRIX_STATE_PRECONDITION_FAILED"));
    }
    Ok(())
}

fn ensure_local_matrix_server(value: &str) -> Result<(), ExecutionError> {
    if value == "localhost"
        || value.starts_with("localhost:")
        || value == "127.0.0.1"
        || value.starts_with("127.0.0.1:")
        || value == "[::1]"
        || value.starts_with("[::1]:")
        || value == "uaa-matrix-harness.invalid"
    {
        return Ok(());
    }
    Err(ExecutionError::safe(
        "MATRIX_PUBLIC_FEDERATION_TARGET_DENIED",
    ))
}

fn validated_power_change(
    desired: &str,
    prior: &str,
    current_level: Int,
    own_level: Int,
) -> Result<Int, ExecutionError> {
    if prior != current_level.to_string() {
        return Err(ExecutionError::safe(
            "MATRIX_POWER_STATE_PRECONDITION_FAILED",
        ));
    }
    let desired = desired
        .parse::<i64>()
        .map_err(|_| ExecutionError::safe("MATRIX_POWER_LEVEL_INVALID"))?;
    if !(-100..=100).contains(&desired) {
        return Err(ExecutionError::safe("MATRIX_POWER_LEVEL_INVALID"));
    }
    let desired =
        Int::try_from(desired).map_err(|_| ExecutionError::safe("MATRIX_POWER_LEVEL_INVALID"))?;
    if desired > own_level {
        return Err(ExecutionError::safe("MATRIX_POWER_ESCALATION_DENIED"));
    }
    Ok(desired)
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

fn private_room_ref(room_id: &str) -> String {
    format!(
        "room-ref:matrix:sha256:{}",
        hex::encode(Sha256::digest(room_id.as_bytes()))
    )
}

fn private_media_ref(media_uri: &str) -> String {
    format!(
        "media-ref:matrix:sha256:{}",
        hex::encode(Sha256::digest(media_uri.as_bytes()))
    )
}

fn success(outcome: &'static str, event_ref: Option<String>) -> ExecutionResult {
    ExecutionResult {
        outcome,
        event_ref,
        byte_count: None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::os::unix::fs::{PermissionsExt, symlink};

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

    #[test]
    fn power_change_rejects_stale_state_and_escalation() {
        let current = Int::try_from(25_i64).unwrap();
        let own = Int::try_from(50_i64).unwrap();
        assert_eq!(
            validated_power_change("30", "24", current, own)
                .unwrap_err()
                .code,
            "MATRIX_POWER_STATE_PRECONDITION_FAILED"
        );
        assert_eq!(
            validated_power_change("75", "25", current, own)
                .unwrap_err()
                .code,
            "MATRIX_POWER_ESCALATION_DENIED"
        );
        assert!(validated_power_change("30", "25", current, own).is_ok());
    }

    #[test]
    fn public_federation_targets_are_denied() {
        assert!(ensure_local_matrix_server("localhost").is_ok());
        assert!(ensure_local_matrix_server("localhost:8008").is_ok());
        assert!(ensure_local_matrix_server("127.0.0.1:8008").is_ok());
        assert!(ensure_local_matrix_server("[::1]:8008").is_ok());
        assert!(ensure_local_matrix_server("uaa-matrix-harness.invalid").is_ok());
        assert_eq!(
            ensure_local_matrix_server("example.org")
                .expect_err("remote target must fail")
                .code,
            "MATRIX_PUBLIC_FEDERATION_TARGET_DENIED"
        );
    }

    #[test]
    fn quarantine_directory_is_descriptor_relative_and_rejects_symlinks() {
        let temporary = tempfile::tempdir().unwrap();
        let scope_root = temporary.path().join("scope");
        let outside = temporary.path().join("outside");
        std::fs::create_dir(&scope_root).unwrap();
        std::fs::create_dir(&outside).unwrap();
        std::fs::set_permissions(&scope_root, std::fs::Permissions::from_mode(0o700)).unwrap();
        std::fs::set_permissions(&outside, std::fs::Permissions::from_mode(0o700)).unwrap();
        symlink(&outside, scope_root.join("media-quarantine")).unwrap();

        let scope_directory = open_private_directory(&scope_root).unwrap();
        assert_eq!(
            open_private_quarantine_directory(&scope_directory)
                .expect_err("symlinked quarantine must fail")
                .code,
            "MATRIX_MEDIA_QUARANTINE_ROOT_DENIED"
        );
        assert!(outside.read_dir().unwrap().next().is_none());
    }
}
