import CryptoKit
import Foundation
import Security

private let helperVersion = "1.0.0"
private let helperVersionRef = "helper-version-ref:matrix-protected-cache:v1"
private let adapterRef = "adapter-ref:matrix-protected-cache:macos-keychain:v1"
private let keychainService = "com.ultimate-ai-agent.matrix-protected-cache.v1"
private let maximumInputBytes = 24 * 1024 * 1024
private let maximumPayloadBytes = 17 * 1024 * 1024
private let maximumAADBytes = 16 * 1024
private let safeRefPattern = try! NSRegularExpression(
    pattern: #"^[A-Za-z0-9][A-Za-z0-9._:/-]{2,255}$"#
)

private enum Operation: String, Codable {
    case version
    case create
    case probe
    case encrypt
    case decrypt
    case delete
}

private struct HelperRequest: Decodable {
    let schemaVersion: String
    let operation: Operation
    let keyItemRef: String?
    let keyVersionRef: String?
    let requestRef: String?
    let payloadBase64url: String?
    let aadBase64url: String?

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case operation
        case keyItemRef = "key_item_ref"
        case keyVersionRef = "key_version_ref"
        case requestRef = "request_ref"
        case payloadBase64url = "payload_base64url"
        case aadBase64url = "aad_base64url"
    }
}

private struct HelperResponse: Encodable {
    let schemaVersion = "uaa-matrix-protected-cache-helper-response.v1"
    let ok: Bool
    let operation: String
    let adapterRef: String
    let helperVersion: String
    let helperVersionRef: String
    let keyItemRef: String?
    let keyVersionRef: String?
    let payloadBase64url: String?
    let payloadFingerprintRef: String?
    let helperReceiptRef: String
    let created: Bool?
    let deletedOrAbsent: Bool?
    let errorCode: String?

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case ok, operation
        case adapterRef = "adapter_ref"
        case helperVersion = "helper_version"
        case helperVersionRef = "helper_version_ref"
        case keyItemRef = "key_item_ref"
        case keyVersionRef = "key_version_ref"
        case payloadBase64url = "payload_base64url"
        case payloadFingerprintRef = "payload_fingerprint_ref"
        case helperReceiptRef = "helper_receipt_ref"
        case created
        case deletedOrAbsent = "deleted_or_absent"
        case errorCode = "error_code"
    }
}

private enum HelperFailure: Error {
    case invalidRequest
    case invalidRef
    case invalidPayload
    case keychainLocked
    case keyNotFound
    case keychainStatus(OSStatus)
    case cryptoFailure

    var code: String {
        switch self {
        case .invalidRequest: return "MATRIX_CACHE_HELPER_REQUEST_INVALID"
        case .invalidRef: return "MATRIX_CACHE_HELPER_REF_INVALID"
        case .invalidPayload: return "MATRIX_CACHE_HELPER_PAYLOAD_INVALID"
        case .keychainLocked: return "MATRIX_CACHE_HELPER_KEYCHAIN_LOCKED"
        case .keyNotFound: return "MATRIX_CACHE_HELPER_KEY_NOT_FOUND"
        case .keychainStatus(let status):
            if status == errSecAuthFailed || status == errSecInteractionNotAllowed {
                return "MATRIX_CACHE_HELPER_KEYCHAIN_LOCKED"
            }
            return "MATRIX_CACHE_HELPER_KEYCHAIN_STATUS_\(status)"
        case .cryptoFailure: return "MATRIX_CACHE_HELPER_CRYPTO_FAILURE"
        }
    }
}

private func safeRef(_ value: String?) throws -> String {
    guard let value, !value.isEmpty else { throw HelperFailure.invalidRef }
    let range = NSRange(location: 0, length: value.utf16.count)
    guard safeRefPattern.firstMatch(in: value, range: range)?.range == range else {
        throw HelperFailure.invalidRef
    }
    return value
}

private func base64url(_ data: Data) -> String {
    data.base64EncodedString()
        .replacingOccurrences(of: "+", with: "-")
        .replacingOccurrences(of: "/", with: "_")
        .replacingOccurrences(of: "=", with: "")
}

private func decodeBase64url(_ value: String, maximumBytes: Int) throws -> Data {
    guard value.range(of: #"^[A-Za-z0-9_-]+$"#, options: .regularExpression) != nil else {
        throw HelperFailure.invalidPayload
    }
    var standard = value.replacingOccurrences(of: "-", with: "+")
        .replacingOccurrences(of: "_", with: "/")
    standard += String(repeating: "=", count: (4 - standard.count % 4) % 4)
    guard let data = Data(base64Encoded: standard), data.count <= maximumBytes,
          base64url(data) == value else {
        throw HelperFailure.invalidPayload
    }
    return data
}

private func sha256Ref(_ prefix: String, _ data: Data) -> String {
    let digest = SHA256.hash(data: data)
    return "\(prefix):sha256:\(digest.map { String(format: "%02x", $0) }.joined())"
}

private func accountRef(keyItemRef: String, keyVersionRef: String) -> String {
    sha256Ref("keychain-account-ref", Data("\(keyItemRef)\u{0}\(keyVersionRef)".utf8))
}

private func receiptRef(operation: Operation, requestRef: String?) -> String {
    sha256Ref(
        "helper-receipt-ref:matrix-protected-cache",
        Data("\(operation.rawValue)\u{0}\(requestRef ?? "request-ref:matrix-cache-helper:version")\u{0}\(helperVersionRef)".utf8)
    )
}

private func baseQuery(keyItemRef: String, keyVersionRef: String) -> [String: Any] {
    [
        kSecClass as String: kSecClassGenericPassword,
        kSecAttrService as String: keychainService,
        kSecAttrAccount as String: accountRef(keyItemRef: keyItemRef, keyVersionRef: keyVersionRef),
    ]
}

private func readKey(keyItemRef: String, keyVersionRef: String) throws -> SymmetricKey {
    var query = baseQuery(keyItemRef: keyItemRef, keyVersionRef: keyVersionRef)
    query[kSecReturnData as String] = kCFBooleanTrue
    query[kSecMatchLimit as String] = kSecMatchLimitOne
    var item: CFTypeRef?
    let status = SecItemCopyMatching(query as CFDictionary, &item)
    if status == errSecItemNotFound { throw HelperFailure.keyNotFound }
    if status == errSecAuthFailed || status == errSecInteractionNotAllowed {
        throw HelperFailure.keychainLocked
    }
    guard status == errSecSuccess, let material = item as? Data, material.count == 32 else {
        throw HelperFailure.keychainStatus(status)
    }
    return SymmetricKey(data: material)
}

private func createKey(keyItemRef: String, keyVersionRef: String) throws -> Bool {
    do {
        _ = try readKey(keyItemRef: keyItemRef, keyVersionRef: keyVersionRef)
        return false
    } catch HelperFailure.keyNotFound {
        // Continue with idempotent creation.
    }
    let material = Data(SymmetricKey(size: .bits256).withUnsafeBytes { Data($0) })
    var query = baseQuery(keyItemRef: keyItemRef, keyVersionRef: keyVersionRef)
    query[kSecAttrAccessible as String] = kSecAttrAccessibleWhenUnlockedThisDeviceOnly
    query[kSecValueData as String] = material
    query[kSecAttrLabel as String] = "UAA Matrix protected cache key"
    let status = SecItemAdd(query as CFDictionary, nil)
    if status == errSecDuplicateItem { return false }
    guard status == errSecSuccess else { throw HelperFailure.keychainStatus(status) }
    return true
}

private func deleteKey(keyItemRef: String, keyVersionRef: String) throws {
    let status = SecItemDelete(
        baseQuery(keyItemRef: keyItemRef, keyVersionRef: keyVersionRef) as CFDictionary
    )
    guard status == errSecSuccess || status == errSecItemNotFound else {
        throw HelperFailure.keychainStatus(status)
    }
}

private func run(_ request: HelperRequest) throws -> HelperResponse {
    guard request.schemaVersion == "uaa-matrix-protected-cache-helper-request.v1" else {
        throw HelperFailure.invalidRequest
    }
    if request.operation == .version {
        guard request.keyItemRef == nil, request.keyVersionRef == nil,
              request.requestRef == nil, request.payloadBase64url == nil,
              request.aadBase64url == nil else { throw HelperFailure.invalidRequest }
        return HelperResponse(
            ok: true, operation: request.operation.rawValue, adapterRef: adapterRef,
            helperVersion: helperVersion, helperVersionRef: helperVersionRef,
            keyItemRef: nil, keyVersionRef: nil, payloadBase64url: nil,
            payloadFingerprintRef: nil,
            helperReceiptRef: receiptRef(operation: .version, requestRef: nil),
            created: nil, deletedOrAbsent: nil, errorCode: nil
        )
    }
    let keyItemRef = try safeRef(request.keyItemRef)
    let keyVersionRef = try safeRef(request.keyVersionRef)
    let requestRef = try safeRef(request.requestRef)
    switch request.operation {
    case .create:
        guard request.payloadBase64url == nil, request.aadBase64url == nil else {
            throw HelperFailure.invalidRequest
        }
        let created = try createKey(keyItemRef: keyItemRef, keyVersionRef: keyVersionRef)
        return HelperResponse(
            ok: true, operation: request.operation.rawValue, adapterRef: adapterRef,
            helperVersion: helperVersion, helperVersionRef: helperVersionRef,
            keyItemRef: keyItemRef, keyVersionRef: keyVersionRef,
            payloadBase64url: nil, payloadFingerprintRef: nil,
            helperReceiptRef: receiptRef(operation: .create, requestRef: requestRef),
            created: created, deletedOrAbsent: nil, errorCode: nil
        )
    case .probe:
        guard request.payloadBase64url == nil, request.aadBase64url == nil else {
            throw HelperFailure.invalidRequest
        }
        _ = try readKey(keyItemRef: keyItemRef, keyVersionRef: keyVersionRef)
        return HelperResponse(
            ok: true, operation: request.operation.rawValue, adapterRef: adapterRef,
            helperVersion: helperVersion, helperVersionRef: helperVersionRef,
            keyItemRef: keyItemRef, keyVersionRef: keyVersionRef,
            payloadBase64url: nil, payloadFingerprintRef: nil,
            helperReceiptRef: receiptRef(operation: .probe, requestRef: requestRef),
            created: false, deletedOrAbsent: nil, errorCode: nil
        )
    case .encrypt, .decrypt:
        guard let payloadValue = request.payloadBase64url,
              let aadValue = request.aadBase64url else { throw HelperFailure.invalidRequest }
        let payload = try decodeBase64url(payloadValue, maximumBytes: maximumPayloadBytes)
        let aad = try decodeBase64url(aadValue, maximumBytes: maximumAADBytes)
        let key = try readKey(keyItemRef: keyItemRef, keyVersionRef: keyVersionRef)
        let output: Data
        do {
            if request.operation == .encrypt {
                let sealed = try AES.GCM.seal(payload, using: key, authenticating: aad)
                guard let combined = sealed.combined else { throw HelperFailure.cryptoFailure }
                output = combined
            } else {
                let sealed = try AES.GCM.SealedBox(combined: payload)
                output = try AES.GCM.open(sealed, using: key, authenticating: aad)
            }
        } catch {
            throw HelperFailure.cryptoFailure
        }
        return HelperResponse(
            ok: true, operation: request.operation.rawValue, adapterRef: adapterRef,
            helperVersion: helperVersion, helperVersionRef: helperVersionRef,
            keyItemRef: keyItemRef, keyVersionRef: keyVersionRef,
            payloadBase64url: base64url(output),
            payloadFingerprintRef: sha256Ref("matrix-cache-helper-payload-fingerprint-ref", output),
            helperReceiptRef: receiptRef(operation: request.operation, requestRef: requestRef),
            created: nil, deletedOrAbsent: nil, errorCode: nil
        )
    case .delete:
        guard request.payloadBase64url == nil, request.aadBase64url == nil else {
            throw HelperFailure.invalidRequest
        }
        try deleteKey(keyItemRef: keyItemRef, keyVersionRef: keyVersionRef)
        return HelperResponse(
            ok: true, operation: request.operation.rawValue, adapterRef: adapterRef,
            helperVersion: helperVersion, helperVersionRef: helperVersionRef,
            keyItemRef: keyItemRef, keyVersionRef: keyVersionRef,
            payloadBase64url: nil, payloadFingerprintRef: nil,
            helperReceiptRef: receiptRef(operation: .delete, requestRef: requestRef),
            created: nil, deletedOrAbsent: true, errorCode: nil
        )
    case .version:
        throw HelperFailure.invalidRequest
    }
}

private func failureResponse(operation: String, code: String) -> HelperResponse {
    HelperResponse(
        ok: false, operation: operation, adapterRef: adapterRef,
        helperVersion: helperVersion, helperVersionRef: helperVersionRef,
        keyItemRef: nil, keyVersionRef: nil, payloadBase64url: nil,
        payloadFingerprintRef: nil,
        helperReceiptRef: receiptRef(operation: .version, requestRef: nil),
        created: nil, deletedOrAbsent: nil, errorCode: code
    )
}

private func emit(_ response: HelperResponse) {
    guard let encoded = try? JSONEncoder().encode(response) else { exit(2) }
    FileHandle.standardOutput.write(encoded)
}

let input = FileHandle.standardInput.readDataToEndOfFile()
guard input.count <= maximumInputBytes else {
    emit(failureResponse(operation: "unknown", code: "MATRIX_CACHE_HELPER_REQUEST_TOO_LARGE"))
    exit(2)
}
do {
    let request = try JSONDecoder().decode(HelperRequest.self, from: input)
    emit(try run(request))
} catch let failure as HelperFailure {
    let operation = (try? JSONDecoder().decode(HelperRequest.self, from: input).operation.rawValue)
        ?? "unknown"
    emit(failureResponse(operation: operation, code: failure.code))
    exit(2)
} catch {
    emit(failureResponse(operation: "unknown", code: "MATRIX_CACHE_HELPER_REQUEST_INVALID"))
    exit(2)
}
