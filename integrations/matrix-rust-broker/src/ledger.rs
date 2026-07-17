use std::{
    fs::{File, OpenOptions},
    io::{BufRead, BufReader, Write},
    os::unix::fs::{MetadataExt, OpenOptionsExt, PermissionsExt},
    path::{Path, PathBuf},
};

use fs2::FileExt;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::protocol::BrokerRequest;

const MAX_LEDGER_BYTES: u64 = 4 * 1024 * 1024;

pub struct ScopeGuard {
    pub root: PathBuf,
    _lock: File,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct LedgerRecord {
    pub request_fingerprint_ref: String,
    pub idempotency_ref: String,
    pub transaction_ref: Option<String>,
    pub event_ref: Option<String>,
    pub receipt_ref: String,
    pub outcome: String,
}

impl ScopeGuard {
    pub fn acquire(state_root: &Path, request: &BrokerRequest) -> Result<Self, &'static str> {
        if !state_root.is_absolute() {
            return Err("MATRIX_BROKER_STATE_ROOT_INVALID");
        }
        std::fs::create_dir_all(state_root).map_err(|_| "MATRIX_BROKER_STATE_ROOT_UNAVAILABLE")?;
        std::fs::set_permissions(state_root, std::fs::Permissions::from_mode(0o700))
            .map_err(|_| "MATRIX_BROKER_STATE_ROOT_PERMISSIONS_FAILED")?;
        validate_private_directory(state_root)?;
        let mut digest = Sha256::new();
        digest.update(request.account_ref.as_bytes());
        digest.update([0]);
        digest.update(request.homeserver_ref.as_bytes());
        digest.update([0]);
        digest.update(request.device_ref.as_bytes());
        let scope_name = hex::encode(digest.finalize());
        let root = state_root.join(&scope_name[..32]);
        std::fs::create_dir_all(&root).map_err(|_| "MATRIX_BROKER_SCOPE_ROOT_UNAVAILABLE")?;
        std::fs::set_permissions(&root, std::fs::Permissions::from_mode(0o700))
            .map_err(|_| "MATRIX_BROKER_SCOPE_PERMISSIONS_FAILED")?;
        validate_private_directory(&root)?;
        let lock_path = root.join("broker.lock");
        validate_private_file_if_present(&lock_path)?;
        let lock = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .truncate(false)
            .mode(0o600)
            .open(lock_path)
            .map_err(|_| "MATRIX_BROKER_SINGLETON_LOCK_UNAVAILABLE")?;
        validate_open_private_file(&lock)?;
        lock.try_lock_exclusive()
            .map_err(|_| "MATRIX_BROKER_SINGLETON_ALREADY_ACTIVE")?;
        Ok(Self { root, _lock: lock })
    }

    pub fn consume_nonce(&self, nonce: &str) -> Result<(), &'static str> {
        let path = self.root.join("nonce-ledger.jsonl");
        if bounded_contains_line(&path, nonce)? {
            return Err("MATRIX_BROKER_NONCE_REPLAYED");
        }
        append_line(&path, nonce)
    }

    pub fn replay(&self, request: &BrokerRequest) -> Result<Option<LedgerRecord>, &'static str> {
        let path = self.root.join("execution-ledger.jsonl");
        if !path.exists() {
            return Ok(None);
        }
        validate_private_file_if_present(&path)?;
        let metadata = path
            .metadata()
            .map_err(|_| "MATRIX_BROKER_LEDGER_UNAVAILABLE")?;
        if metadata.len() > MAX_LEDGER_BYTES {
            return Err("MATRIX_BROKER_LEDGER_OVERSIZE");
        }
        let file = File::open(path).map_err(|_| "MATRIX_BROKER_LEDGER_UNAVAILABLE")?;
        validate_open_private_file(&file)?;
        let reader = BufReader::new(file);
        for line in reader.lines() {
            let line = line.map_err(|_| "MATRIX_BROKER_LEDGER_INVALID")?;
            let record: LedgerRecord =
                serde_json::from_str(&line).map_err(|_| "MATRIX_BROKER_LEDGER_INVALID")?;
            if record.idempotency_ref == request.idempotency_ref {
                if record.request_fingerprint_ref != request.request_fingerprint_ref
                    || record.transaction_ref != request.transaction_ref
                {
                    return Err("MATRIX_BROKER_IDEMPOTENCY_CONFLICT");
                }
                return Ok(Some(record));
            }
        }
        Ok(None)
    }

    pub fn record(&self, record: &LedgerRecord) -> Result<(), &'static str> {
        let payload = serde_json::to_string(record).map_err(|_| "MATRIX_BROKER_LEDGER_INVALID")?;
        append_line(&self.root.join("execution-ledger.jsonl"), &payload)
    }
}

fn bounded_contains_line(path: &Path, expected: &str) -> Result<bool, &'static str> {
    if !path.exists() {
        return Ok(false);
    }
    validate_private_file_if_present(path)?;
    if path
        .metadata()
        .map_err(|_| "MATRIX_BROKER_LEDGER_UNAVAILABLE")?
        .len()
        > MAX_LEDGER_BYTES
    {
        return Err("MATRIX_BROKER_LEDGER_OVERSIZE");
    }
    let file = File::open(path).map_err(|_| "MATRIX_BROKER_LEDGER_UNAVAILABLE")?;
    validate_open_private_file(&file)?;
    let reader = BufReader::new(file);
    for line in reader.lines() {
        if line.map_err(|_| "MATRIX_BROKER_LEDGER_INVALID")? == expected {
            return Ok(true);
        }
    }
    Ok(false)
}

fn append_line(path: &Path, value: &str) -> Result<(), &'static str> {
    if value.contains(['\n', '\r']) {
        return Err("MATRIX_BROKER_LEDGER_VALUE_INVALID");
    }
    validate_private_file_if_present(path)?;
    if path.exists()
        && path
            .metadata()
            .map_err(|_| "MATRIX_BROKER_LEDGER_UNAVAILABLE")?
            .len()
            > MAX_LEDGER_BYTES
    {
        return Err("MATRIX_BROKER_LEDGER_OVERSIZE");
    }
    let mut file = OpenOptions::new()
        .append(true)
        .create(true)
        .mode(0o600)
        .open(path)
        .map_err(|_| "MATRIX_BROKER_LEDGER_UNAVAILABLE")?;
    validate_open_private_file(&file)?;
    writeln!(file, "{value}").map_err(|_| "MATRIX_BROKER_LEDGER_WRITE_FAILED")?;
    file.sync_data()
        .map_err(|_| "MATRIX_BROKER_LEDGER_WRITE_FAILED")
}

fn validate_private_directory(path: &Path) -> Result<(), &'static str> {
    let metadata =
        std::fs::symlink_metadata(path).map_err(|_| "MATRIX_BROKER_STATE_ROOT_UNAVAILABLE")?;
    if !metadata.file_type().is_dir()
        || metadata.file_type().is_symlink()
        || metadata.mode() & 0o077 != 0
    {
        return Err("MATRIX_BROKER_STATE_ROOT_UNTRUSTED");
    }
    Ok(())
}

fn validate_private_file_if_present(path: &Path) -> Result<(), &'static str> {
    match std::fs::symlink_metadata(path) {
        Ok(metadata)
            if metadata.file_type().is_file()
                && !metadata.file_type().is_symlink()
                && metadata.nlink() == 1
                && metadata.mode() & 0o077 == 0 =>
        {
            Ok(())
        }
        Ok(_) => Err("MATRIX_BROKER_LEDGER_FILE_UNTRUSTED"),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(()),
        Err(_) => Err("MATRIX_BROKER_LEDGER_UNAVAILABLE"),
    }
}

fn validate_open_private_file(file: &File) -> Result<(), &'static str> {
    let metadata = file
        .metadata()
        .map_err(|_| "MATRIX_BROKER_LEDGER_UNAVAILABLE")?;
    if !metadata.file_type().is_file() || metadata.nlink() != 1 || metadata.mode() & 0o077 != 0 {
        return Err("MATRIX_BROKER_LEDGER_FILE_UNTRUSTED");
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::protocol::{BrokerOperation, BrokerRequest};
    use std::os::unix::fs::symlink;

    fn fixture_request() -> BrokerRequest {
        BrokerRequest {
            protocol_version: "uaa-matrix-rust-broker.v1".to_owned(),
            request_ref: "request-ref:matrix-broker:test".to_owned(),
            request_fingerprint_ref: "request-fingerprint-ref:matrix-broker:test".to_owned(),
            nonce: "a".repeat(64),
            issued_at_ms: 1,
            deadline_ms: 2,
            operation: BrokerOperation::ProtocolProbe,
            account_ref: "account-ref:matrix:test".to_owned(),
            homeserver_ref: "homeserver-ref:matrix:test".to_owned(),
            device_ref: "device-ref:matrix:test".to_owned(),
            room_ref: None,
            event_ref: None,
            transaction_ref: None,
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
        }
    }

    #[test]
    fn append_rejects_multiline_values() {
        let root = tempfile::tempdir().unwrap();
        assert_eq!(
            append_line(&root.path().join("ledger"), "value\nsecond"),
            Err("MATRIX_BROKER_LEDGER_VALUE_INVALID")
        );
    }

    #[test]
    fn private_file_validation_rejects_symlink() {
        let root = tempfile::tempdir().unwrap();
        let target = root.path().join("target");
        std::fs::write(&target, b"safe").unwrap();
        let linked = root.path().join("ledger");
        symlink(&target, &linked).unwrap();
        assert_eq!(
            validate_private_file_if_present(&linked),
            Err("MATRIX_BROKER_LEDGER_FILE_UNTRUSTED")
        );
    }

    #[test]
    fn nonce_and_idempotency_replay_fail_closed() {
        let root = tempfile::tempdir().unwrap();
        let state_root = root.path().join("state");
        let request = fixture_request();
        let guard = ScopeGuard::acquire(&state_root, &request).unwrap();
        assert!(guard.consume_nonce(&request.nonce).is_ok());
        assert_eq!(
            guard.consume_nonce(&request.nonce),
            Err("MATRIX_BROKER_NONCE_REPLAYED")
        );
        let record = LedgerRecord {
            request_fingerprint_ref: request.request_fingerprint_ref.clone(),
            idempotency_ref: request.idempotency_ref.clone(),
            transaction_ref: None,
            event_ref: None,
            receipt_ref: "receipt-ref:matrix-broker:test".to_owned(),
            outcome: "ready".to_owned(),
        };
        guard.record(&record).unwrap();
        assert!(guard.replay(&request).unwrap().is_some());
        let mut changed = fixture_request();
        changed.request_fingerprint_ref =
            "request-fingerprint-ref:matrix-broker:changed".to_owned();
        assert!(matches!(
            guard.replay(&changed),
            Err("MATRIX_BROKER_IDEMPOTENCY_CONFLICT")
        ));
    }
}
