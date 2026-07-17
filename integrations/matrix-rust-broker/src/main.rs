mod execution;
mod keychain;
mod ledger;
mod protocol;

use std::{
    env,
    fs::File,
    io::{Read, Write},
    net::{IpAddr, Ipv4Addr, SocketAddr},
    path::{Path, PathBuf},
    time::Duration,
};

use ledger::{LedgerRecord, ScopeGuard};
use protocol::{
    AUTH_KEY_BYTES, BrokerRequest, BrokerResponse, MAX_FRAME_BYTES, PROTOCOL_VERSION,
    RESPONSE_VERSION, ReadinessRecord, decode_authenticated_request, encode_authenticated_response,
};
use sha2::{Digest, Sha256};
use tokio::{
    io::{AsyncReadExt, AsyncWriteExt},
    net::TcpListener,
    time::timeout,
};
use zeroize::{Zeroize, Zeroizing};

const ADAPTER_REF: &str = "adapter-ref:matrix-rust-broker:v1";

#[tokio::main]
async fn main() {
    if run().await.is_err() {
        std::process::exit(2);
    }
}

async fn run() -> Result<(), &'static str> {
    let (auth_fd, state_root_fd) = parse_args()?;
    let mut auth_key = read_fd_bounded(auth_fd, AUTH_KEY_BYTES)?;
    if auth_key.len() != AUTH_KEY_BYTES {
        return Err("MATRIX_BROKER_AUTH_KEY_INVALID");
    }
    let state_root_bytes = Zeroizing::new(read_fd_bounded(state_root_fd, 2048)?);
    let state_root_text =
        std::str::from_utf8(&state_root_bytes).map_err(|_| "MATRIX_BROKER_STATE_ROOT_INVALID")?;
    if state_root_text.is_empty()
        || state_root_text.contains(['\n', '\r', '\0'])
        || !state_root_text.starts_with('/')
    {
        return Err("MATRIX_BROKER_STATE_ROOT_INVALID");
    }
    let state_root = PathBuf::from(state_root_text);

    let listener = TcpListener::bind(SocketAddr::new(IpAddr::V4(Ipv4Addr::LOCALHOST), 0))
        .await
        .map_err(|_| "MATRIX_BROKER_LOOPBACK_BIND_FAILED")?;
    let port = listener
        .local_addr()
        .map_err(|_| "MATRIX_BROKER_LOOPBACK_BIND_FAILED")?
        .port();
    emit_readiness(port)?;

    let (mut stream, peer) = timeout(Duration::from_secs(30), listener.accept())
        .await
        .map_err(|_| "MATRIX_BROKER_ACCEPT_TIMEOUT")?
        .map_err(|_| "MATRIX_BROKER_ACCEPT_FAILED")?;
    if !peer.ip().is_loopback() {
        return Err("MATRIX_BROKER_LOOPBACK_PEER_REQUIRED");
    }
    let frame_length = timeout(Duration::from_secs(5), stream.read_u32())
        .await
        .map_err(|_| "MATRIX_BROKER_READ_TIMEOUT")?
        .map_err(|_| "MATRIX_BROKER_READ_FAILED")? as usize;
    if frame_length == 0 || frame_length > MAX_FRAME_BYTES {
        return Err("MATRIX_BROKER_FRAME_INVALID");
    }
    let mut frame = Zeroizing::new(vec![0_u8; frame_length]);
    timeout(Duration::from_secs(5), stream.read_exact(&mut frame))
        .await
        .map_err(|_| "MATRIX_BROKER_READ_TIMEOUT")?
        .map_err(|_| "MATRIX_BROKER_READ_FAILED")?;
    let request = decode_authenticated_request(&frame, &auth_key)?;
    frame.zeroize();

    let response = dispatch(&request, &state_root).await;
    let payload = encode_authenticated_response(&response, &auth_key)?;
    if payload.len() > MAX_FRAME_BYTES {
        return Err("MATRIX_BROKER_RESPONSE_OVERSIZE");
    }
    timeout(
        Duration::from_secs(5),
        stream.write_u32(payload.len() as u32),
    )
    .await
    .map_err(|_| "MATRIX_BROKER_WRITE_TIMEOUT")?
    .map_err(|_| "MATRIX_BROKER_WRITE_FAILED")?;
    timeout(Duration::from_secs(5), stream.write_all(&payload))
        .await
        .map_err(|_| "MATRIX_BROKER_WRITE_TIMEOUT")?
        .map_err(|_| "MATRIX_BROKER_WRITE_FAILED")?;
    timeout(Duration::from_secs(5), stream.shutdown())
        .await
        .map_err(|_| "MATRIX_BROKER_WRITE_TIMEOUT")?
        .map_err(|_| "MATRIX_BROKER_WRITE_FAILED")?;
    auth_key.zeroize();
    Ok(())
}

async fn dispatch(request: &BrokerRequest, state_root: &Path) -> BrokerResponse {
    let guard = match ScopeGuard::acquire(state_root, request) {
        Ok(value) => value,
        Err(code) => return failure_response(request, code, false),
    };
    if let Err(code) = guard.consume_nonce(&request.nonce) {
        return failure_response(request, code, false);
    }
    match guard.replay(request) {
        Ok(Some(record)) => {
            let prior_uncertain = record.outcome == "outcome_uncertain";
            return BrokerResponse {
                protocol_version: RESPONSE_VERSION,
                ok: !prior_uncertain,
                operation: request.operation.as_str(),
                request_ref: request.request_ref.clone(),
                request_fingerprint_ref: request.request_fingerprint_ref.clone(),
                receipt_ref: record.receipt_ref,
                outcome: if prior_uncertain {
                    "outcome_uncertain"
                } else {
                    "replayed"
                },
                event_ref: record.event_ref,
                transaction_ref: record.transaction_ref,
                replayed: true,
                credential_material_included: false,
                content_included: false,
                raw_identifiers_included: false,
                error_code: if prior_uncertain {
                    Some("MATRIX_BROKER_PRIOR_OUTCOME_UNCERTAIN")
                } else {
                    None
                },
            };
        }
        Ok(None) => {}
        Err(code) => return failure_response(request, code, false),
    }

    match execution::execute(request, &guard.root).await {
        Ok(result) => {
            let receipt_ref = receipt_ref(request, result.outcome);
            let record = LedgerRecord {
                request_fingerprint_ref: request.request_fingerprint_ref.clone(),
                idempotency_ref: request.idempotency_ref.clone(),
                transaction_ref: request.transaction_ref.clone(),
                event_ref: result.event_ref.clone(),
                receipt_ref: receipt_ref.clone(),
                outcome: result.outcome.to_owned(),
            };
            if let Err(code) = guard.record(&record) {
                return failure_response(request, code, request.operation.is_network_mutation());
            }
            BrokerResponse {
                protocol_version: RESPONSE_VERSION,
                ok: true,
                operation: request.operation.as_str(),
                request_ref: request.request_ref.clone(),
                request_fingerprint_ref: request.request_fingerprint_ref.clone(),
                receipt_ref,
                outcome: result.outcome,
                event_ref: result.event_ref,
                transaction_ref: request.transaction_ref.clone(),
                replayed: false,
                credential_material_included: false,
                content_included: false,
                raw_identifiers_included: false,
                error_code: None,
            }
        }
        Err(error) => {
            if error.uncertain {
                let receipt_ref = receipt_ref(request, "outcome_uncertain");
                let record = LedgerRecord {
                    request_fingerprint_ref: request.request_fingerprint_ref.clone(),
                    idempotency_ref: request.idempotency_ref.clone(),
                    transaction_ref: request.transaction_ref.clone(),
                    event_ref: None,
                    receipt_ref,
                    outcome: "outcome_uncertain".to_owned(),
                };
                let _ = guard.record(&record);
            }
            failure_response(request, error.code, error.uncertain)
        }
    }
}

fn failure_response(
    request: &BrokerRequest,
    code: &'static str,
    uncertain: bool,
) -> BrokerResponse {
    let outcome = if uncertain {
        "outcome_uncertain"
    } else {
        "blocked"
    };
    BrokerResponse {
        protocol_version: RESPONSE_VERSION,
        ok: false,
        operation: request.operation.as_str(),
        request_ref: request.request_ref.clone(),
        request_fingerprint_ref: request.request_fingerprint_ref.clone(),
        receipt_ref: receipt_ref(request, outcome),
        outcome,
        event_ref: None,
        transaction_ref: request.transaction_ref.clone(),
        replayed: false,
        credential_material_included: false,
        content_included: false,
        raw_identifiers_included: false,
        error_code: Some(code),
    }
}

fn receipt_ref(request: &BrokerRequest, outcome: &str) -> String {
    let mut digest = Sha256::new();
    digest.update(request.request_fingerprint_ref.as_bytes());
    digest.update([0]);
    digest.update(request.operation.as_str().as_bytes());
    digest.update([0]);
    digest.update(outcome.as_bytes());
    format!(
        "receipt-ref:matrix-rust-broker:sha256:{}",
        hex::encode(digest.finalize())
    )
}

fn parse_args() -> Result<(u32, u32), &'static str> {
    let args: Vec<String> = env::args().skip(1).collect();
    if args.len() != 2 {
        return Err("MATRIX_BROKER_ARGUMENTS_INVALID");
    }
    let auth_fd = parse_fd_arg(&args[0], "--auth-fd=")?;
    let state_root_fd = parse_fd_arg(&args[1], "--state-root-fd=")?;
    if auth_fd == state_root_fd {
        return Err("MATRIX_BROKER_ARGUMENTS_INVALID");
    }
    Ok((auth_fd, state_root_fd))
}

fn parse_fd_arg(value: &str, prefix: &str) -> Result<u32, &'static str> {
    let fd = value
        .strip_prefix(prefix)
        .ok_or("MATRIX_BROKER_ARGUMENTS_INVALID")?
        .parse::<u32>()
        .map_err(|_| "MATRIX_BROKER_ARGUMENTS_INVALID")?;
    if !(3..=1024).contains(&fd) {
        return Err("MATRIX_BROKER_ARGUMENTS_INVALID");
    }
    Ok(fd)
}

fn read_fd_bounded(fd: u32, maximum: usize) -> Result<Vec<u8>, &'static str> {
    let file = File::open(format!("/dev/fd/{fd}"))
        .map_err(|_| "MATRIX_BROKER_INHERITED_FD_UNAVAILABLE")?;
    let mut value = Vec::with_capacity(maximum);
    file.take((maximum + 1) as u64)
        .read_to_end(&mut value)
        .map_err(|_| "MATRIX_BROKER_INHERITED_FD_READ_FAILED")?;
    if value.len() > maximum {
        value.zeroize();
        return Err("MATRIX_BROKER_INHERITED_FD_OVERSIZE");
    }
    Ok(value)
}

fn emit_readiness(port: u16) -> Result<(), &'static str> {
    let readiness = ReadinessRecord {
        protocol_version: PROTOCOL_VERSION,
        adapter_ref: ADAPTER_REF,
        bind_ref: "loopback-ref:ipv4:127.0.0.1",
        port,
        maximum_frame_bytes: MAX_FRAME_BYTES,
        one_request_only: true,
        credential_material_included: false,
    };
    let payload = serde_json::to_vec(&readiness).map_err(|_| "MATRIX_BROKER_READINESS_INVALID")?;
    let mut stdout = std::io::stdout().lock();
    stdout
        .write_all(&payload)
        .map_err(|_| "MATRIX_BROKER_READINESS_WRITE_FAILED")?;
    stdout
        .write_all(b"\n")
        .map_err(|_| "MATRIX_BROKER_READINESS_WRITE_FAILED")?;
    stdout
        .flush()
        .map_err(|_| "MATRIX_BROKER_READINESS_WRITE_FAILED")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fd_arguments_are_strict() {
        assert_eq!(parse_fd_arg("--auth-fd=3", "--auth-fd="), Ok(3));
        assert_eq!(
            parse_fd_arg("--auth-fd=2", "--auth-fd="),
            Err("MATRIX_BROKER_ARGUMENTS_INVALID")
        );
    }
}
