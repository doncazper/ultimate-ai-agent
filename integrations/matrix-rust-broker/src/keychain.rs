use rand::{RngCore, rngs::OsRng};
use zeroize::Zeroizing;

const KEYCHAIN_SERVICE: &str = "com.ultimate-ai-agent.matrix-messenger.v1";

#[derive(Clone, Copy, Debug)]
pub enum SecretKind {
    Session,
    CryptoStore,
    Outbox,
}

impl SecretKind {
    fn label(self) -> &'static str {
        match self {
            Self::Session => "Matrix session",
            Self::CryptoStore => "Matrix crypto store key",
            Self::Outbox => "Matrix outbox key",
        }
    }

    fn suffix(self) -> &'static str {
        match self {
            Self::Session => "session",
            Self::CryptoStore => "crypto-store",
            Self::Outbox => "outbox",
        }
    }
}

pub fn create_random(scope_ref: &str, kind: SecretKind) -> Result<(), &'static str> {
    let mut value = Zeroizing::new(vec![0_u8; 32]);
    OsRng.fill_bytes(&mut value);
    set(scope_ref, kind, &value)
}

pub fn set(scope_ref: &str, kind: SecretKind, value: &[u8]) -> Result<(), &'static str> {
    if value.is_empty() || value.len() > 16 * 1024 {
        return Err("MATRIX_KEYCHAIN_VALUE_INVALID");
    }
    platform::set(&account(scope_ref, kind), kind.label(), value)
}

pub fn get(scope_ref: &str, kind: SecretKind) -> Result<Zeroizing<Vec<u8>>, &'static str> {
    platform::get(&account(scope_ref, kind)).map(Zeroizing::new)
}

pub fn probe(scope_ref: &str, kind: SecretKind) -> Result<(), &'static str> {
    let value = get(scope_ref, kind)?;
    if value.is_empty() {
        return Err("MATRIX_KEYCHAIN_ITEM_CORRUPT");
    }
    Ok(())
}

pub fn rotate(scope_ref: &str, kind: SecretKind) -> Result<(), &'static str> {
    probe(scope_ref, kind)?;
    create_random(scope_ref, kind)
}

pub fn delete(scope_ref: &str, kind: SecretKind) -> Result<(), &'static str> {
    platform::delete(&account(scope_ref, kind))
}

fn account(scope_ref: &str, kind: SecretKind) -> String {
    format!("{scope_ref}:{}", kind.suffix())
}

#[cfg(target_os = "macos")]
mod platform {
    use security_framework::passwords::{
        PasswordOptions, delete_generic_password_options, generic_password,
        set_generic_password_options,
    };

    use super::KEYCHAIN_SERVICE;

    fn options(account: &str, label: Option<&str>) -> Result<PasswordOptions, &'static str> {
        let mut options = PasswordOptions::new_generic_password(KEYCHAIN_SERVICE, account);
        options.set_access_synchronized(Some(false));
        if let Some(label) = label {
            options.set_label(label);
            options.set_description("Ultimate AI Agent local Matrix secret");
        }
        Ok(options)
    }

    pub fn set(account: &str, label: &str, value: &[u8]) -> Result<(), &'static str> {
        set_generic_password_options(value, options(account, Some(label))?).map_err(map_error)
    }

    pub fn get(account: &str) -> Result<Vec<u8>, &'static str> {
        generic_password(options(account, None)?).map_err(map_error)
    }

    pub fn delete(account: &str) -> Result<(), &'static str> {
        delete_generic_password_options(options(account, None)?).map_err(map_error)
    }

    fn map_error(error: security_framework::base::Error) -> &'static str {
        match error.code() {
            -25300 => "MATRIX_KEYCHAIN_ITEM_MISSING",
            -25293 => "MATRIX_KEYCHAIN_AUTH_FAILED",
            -25308 => "MATRIX_KEYCHAIN_INTERACTION_NOT_ALLOWED",
            -34018 => "MATRIX_KEYCHAIN_ENTITLEMENT_MISSING",
            _ => "MATRIX_KEYCHAIN_OPERATION_FAILED",
        }
    }
}

#[cfg(not(target_os = "macos"))]
mod platform {
    pub fn set(_account: &str, _label: &str, _value: &[u8]) -> Result<(), &'static str> {
        Err("MATRIX_KEYCHAIN_MACOS_REQUIRED")
    }

    pub fn get(_account: &str) -> Result<Vec<u8>, &'static str> {
        Err("MATRIX_KEYCHAIN_MACOS_REQUIRED")
    }

    pub fn delete(_account: &str) -> Result<(), &'static str> {
        Err("MATRIX_KEYCHAIN_MACOS_REQUIRED")
    }
}
