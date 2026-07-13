import CryptoKit
import Foundation
import Security

private let helperVersion = "1.0.0"
private let helperVersionRef = "helper-version-ref:portable-evidence-keychain:v1"
private let adapterRef = "adapter-ref:portable-evidence-signing:macos-keychain:v1"
private let keychainService = "com.ultimate-ai-agent.portable-evidence-signing.v1"
private let maximumInputBytes = 8 * 1024 * 1024
private let signingDomain = Data("uaa:portable-mission-evidence:ed25519:v1\0".utf8)
private let safeRefPattern = try! NSRegularExpression(
    pattern: #"^[A-Za-z0-9][A-Za-z0-9._:/-]{2,255}$"#
)

private enum Operation: String, Codable {
    case version
    case create
    case probe
    case sign
    case delete
}

private struct HelperRequest: Decodable {
    let schemaVersion: String
    let operation: Operation
    let keyRef: String?
    let keyVersionRef: String?
    let requestRef: String?
    let payloadBase64url: String?

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case operation
        case keyRef = "key_ref"
        case keyVersionRef = "key_version_ref"
        case requestRef = "request_ref"
        case payloadBase64url = "payload_base64url"
    }
}

private struct HelperResponse: Encodable {
    let schemaVersion = "uaa-portable-evidence-keychain-helper-response.v1"
    let ok: Bool
    let operation: String
    let adapterRef: String
    let helperVersion: String
    let helperVersionRef: String
    let keyRef: String?
    let keyVersionRef: String?
    let publicKeyBase64url: String?
    let publicKeyFingerprintRef: String?
    let signatureBase64url: String?
    let signatureRef: String?
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
        case keyRef = "key_ref"
        case keyVersionRef = "key_version_ref"
        case publicKeyBase64url = "public_key_base64url"
        case publicKeyFingerprintRef = "public_key_fingerprint_ref"
        case signatureBase64url = "signature_base64url"
        case signatureRef = "signature_ref"
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
    case keychainFailure
    case keychainStatus(OSStatus)
    case cryptoFailure

    var code: String {
        switch self {
        case .invalidRequest: return "HELPER_REQUEST_INVALID"
        case .invalidRef: return "HELPER_REF_INVALID"
        case .invalidPayload: return "HELPER_PAYLOAD_INVALID"
        case .keychainLocked: return "HELPER_KEYCHAIN_LOCKED"
        case .keyNotFound: return "HELPER_KEY_NOT_FOUND"
        case .keychainFailure: return "HELPER_KEYCHAIN_FAILURE"
        case .keychainStatus(let status):
            if status == errSecAuthFailed || status == errSecInteractionNotAllowed {
                return "HELPER_KEYCHAIN_LOCKED"
            }
            return "HELPER_KEYCHAIN_STATUS_\(status)"
        case .cryptoFailure: return "HELPER_CRYPTO_FAILURE"
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

private func decodeBase64url(_ value: String) throws -> Data {
    guard value.range(of: #"^[A-Za-z0-9_-]+$"#, options: .regularExpression) != nil else {
        throw HelperFailure.invalidPayload
    }
    var standard = value.replacingOccurrences(of: "-", with: "+")
        .replacingOccurrences(of: "_", with: "/")
    standard += String(repeating: "=", count: (4 - standard.count % 4) % 4)
    guard let data = Data(base64Encoded: standard), base64url(data) == value else {
        throw HelperFailure.invalidPayload
    }
    return data
}

private func sha256Ref(_ prefix: String, _ data: Data) -> String {
    let digest = SHA256.hash(data: data)
    return "\(prefix):sha256:\(digest.map { String(format: "%02x", $0) }.joined())"
}

private func stableStringRef(_ prefix: String, _ value: String) -> String {
    let data = try! JSONSerialization.data(withJSONObject: value, options: [.fragmentsAllowed])
    return sha256Ref(prefix, data)
}

private func accountRef(keyRef: String, keyVersionRef: String) -> String {
    sha256Ref("keychain-account-ref", Data("\(keyRef)\u{0}\(keyVersionRef)".utf8))
}

private func receiptRef(operation: Operation, requestRef: String?) -> String {
    let request = requestRef ?? "request-ref:portable-evidence-helper:version"
    return sha256Ref(
        "helper-receipt-ref",
        Data("\(operation.rawValue)\u{0}\(request)\u{0}\(helperVersionRef)".utf8)
    )
}

private func baseQuery(keyRef: String, keyVersionRef: String) -> [String: Any] {
    [
        kSecClass as String: kSecClassGenericPassword,
        kSecAttrService as String: keychainService,
        kSecAttrAccount as String: accountRef(keyRef: keyRef, keyVersionRef: keyVersionRef),
    ]
}

private func readSeed(keyRef: String, keyVersionRef: String) throws -> Data {
    var query = baseQuery(keyRef: keyRef, keyVersionRef: keyVersionRef)
    query[kSecReturnData as String] = kCFBooleanTrue
    query[kSecMatchLimit as String] = kSecMatchLimitOne
    var item: CFTypeRef?
    let status = SecItemCopyMatching(query as CFDictionary, &item)
    if status == errSecItemNotFound { throw HelperFailure.keyNotFound }
    if status == errSecAuthFailed || status == errSecInteractionNotAllowed {
        throw HelperFailure.keychainLocked
    }
    guard status == errSecSuccess, let seed = item as? Data, seed.count == 32 else {
        throw HelperFailure.keychainStatus(status)
    }
    return seed
}

private func createKey(keyRef: String, keyVersionRef: String) throws -> (Data, Bool) {
    do {
        let existing = try readSeed(keyRef: keyRef, keyVersionRef: keyVersionRef)
        let key = try Curve25519.Signing.PrivateKey(rawRepresentation: existing)
        return (key.publicKey.rawRepresentation, false)
    } catch HelperFailure.keyNotFound {
        // Continue with an idempotent create.
    }
    let key = Curve25519.Signing.PrivateKey()
    var query = baseQuery(keyRef: keyRef, keyVersionRef: keyVersionRef)
    query[kSecAttrAccessible as String] = kSecAttrAccessibleWhenUnlockedThisDeviceOnly
    query[kSecValueData as String] = key.rawRepresentation
    query[kSecAttrLabel as String] = "UAA portable evidence signing key"
    let status = SecItemAdd(query as CFDictionary, nil)
    if status == errSecDuplicateItem {
        let existing = try readSeed(keyRef: keyRef, keyVersionRef: keyVersionRef)
        let existingKey = try Curve25519.Signing.PrivateKey(rawRepresentation: existing)
        return (existingKey.publicKey.rawRepresentation, false)
    }
    guard status == errSecSuccess else { throw HelperFailure.keychainStatus(status) }
    return (key.publicKey.rawRepresentation, true)
}

private func sign(keyRef: String, keyVersionRef: String, payload: Data) throws -> Data {
    guard payload.count <= maximumInputBytes else { throw HelperFailure.invalidPayload }
    guard payload.starts(with: signingDomain) else { throw HelperFailure.invalidPayload }
    let seed = try readSeed(keyRef: keyRef, keyVersionRef: keyVersionRef)
    do {
        let key = try Curve25519.Signing.PrivateKey(rawRepresentation: seed)
        return try key.signature(for: payload)
    } catch {
        throw HelperFailure.cryptoFailure
    }
}

private func deleteKey(keyRef: String, keyVersionRef: String) throws {
    let status = SecItemDelete(baseQuery(keyRef: keyRef, keyVersionRef: keyVersionRef) as CFDictionary)
    guard status == errSecSuccess || status == errSecItemNotFound else {
        throw HelperFailure.keychainStatus(status)
    }
}

private func run(_ request: HelperRequest) throws -> HelperResponse {
    guard request.schemaVersion == "uaa-portable-evidence-keychain-helper-request.v1" else {
        throw HelperFailure.invalidRequest
    }
    if request.operation == .version {
        guard request.keyRef == nil, request.keyVersionRef == nil,
              request.requestRef == nil, request.payloadBase64url == nil else {
            throw HelperFailure.invalidRequest
        }
        return HelperResponse(
            ok: true, operation: request.operation.rawValue, adapterRef: adapterRef,
            helperVersion: helperVersion, helperVersionRef: helperVersionRef,
            keyRef: nil, keyVersionRef: nil, publicKeyBase64url: nil,
            publicKeyFingerprintRef: nil, signatureBase64url: nil, signatureRef: nil,
            helperReceiptRef: receiptRef(operation: .version, requestRef: nil),
            created: nil, deletedOrAbsent: nil, errorCode: nil
        )
    }
    let keyRef = try safeRef(request.keyRef)
    let keyVersionRef = try safeRef(request.keyVersionRef)
    let requestRef = try safeRef(request.requestRef)
    switch request.operation {
    case .create:
        guard request.payloadBase64url == nil else { throw HelperFailure.invalidRequest }
        let (publicKey, created) = try createKey(keyRef: keyRef, keyVersionRef: keyVersionRef)
        return HelperResponse(
            ok: true, operation: request.operation.rawValue, adapterRef: adapterRef,
            helperVersion: helperVersion, helperVersionRef: helperVersionRef,
            keyRef: keyRef, keyVersionRef: keyVersionRef,
            publicKeyBase64url: base64url(publicKey),
            publicKeyFingerprintRef: sha256Ref("portable-evidence-public-key-fingerprint-ref", publicKey),
            signatureBase64url: nil, signatureRef: nil,
            helperReceiptRef: receiptRef(operation: .create, requestRef: requestRef),
            created: created, deletedOrAbsent: nil, errorCode: nil
        )
    case .probe:
        guard request.payloadBase64url == nil else { throw HelperFailure.invalidRequest }
        let seed = try readSeed(keyRef: keyRef, keyVersionRef: keyVersionRef)
        let key = try Curve25519.Signing.PrivateKey(rawRepresentation: seed)
        let publicKey = key.publicKey.rawRepresentation
        return HelperResponse(
            ok: true, operation: request.operation.rawValue, adapterRef: adapterRef,
            helperVersion: helperVersion, helperVersionRef: helperVersionRef,
            keyRef: keyRef, keyVersionRef: keyVersionRef,
            publicKeyBase64url: base64url(publicKey),
            publicKeyFingerprintRef: sha256Ref("portable-evidence-public-key-fingerprint-ref", publicKey),
            signatureBase64url: nil, signatureRef: nil,
            helperReceiptRef: receiptRef(operation: .probe, requestRef: requestRef),
            created: false, deletedOrAbsent: nil, errorCode: nil
        )
    case .sign:
        guard let encoded = request.payloadBase64url else { throw HelperFailure.invalidPayload }
        let signature = try sign(
            keyRef: keyRef, keyVersionRef: keyVersionRef,
            payload: try decodeBase64url(encoded)
        )
        return HelperResponse(
            ok: true, operation: request.operation.rawValue, adapterRef: adapterRef,
            helperVersion: helperVersion, helperVersionRef: helperVersionRef,
            keyRef: keyRef, keyVersionRef: keyVersionRef, publicKeyBase64url: nil,
            publicKeyFingerprintRef: nil, signatureBase64url: base64url(signature),
            signatureRef: stableStringRef(
                "portable-evidence-signature-ref",
                signature.map { String(format: "%02x", $0) }.joined()
            ),
            helperReceiptRef: receiptRef(operation: .sign, requestRef: requestRef),
            created: nil, deletedOrAbsent: nil, errorCode: nil
        )
    case .delete:
        guard request.payloadBase64url == nil else { throw HelperFailure.invalidRequest }
        try deleteKey(keyRef: keyRef, keyVersionRef: keyVersionRef)
        return HelperResponse(
            ok: true, operation: request.operation.rawValue, adapterRef: adapterRef,
            helperVersion: helperVersion, helperVersionRef: helperVersionRef,
            keyRef: keyRef, keyVersionRef: keyVersionRef, publicKeyBase64url: nil,
            publicKeyFingerprintRef: nil, signatureBase64url: nil, signatureRef: nil,
            helperReceiptRef: receiptRef(operation: .delete, requestRef: requestRef),
            created: nil, deletedOrAbsent: true, errorCode: nil
        )
    case .version:
        throw HelperFailure.invalidRequest
    }
}

private func decodeStrictRequest(_ data: Data) throws -> HelperRequest {
    let object = try JSONSerialization.jsonObject(with: data)
    guard let dictionary = object as? [String: Any] else {
        throw HelperFailure.invalidRequest
    }
    let allowed = Set([
        "schema_version", "operation", "key_ref", "key_version_ref",
        "request_ref", "payload_base64url",
    ])
    guard Set(dictionary.keys).isSubset(of: allowed) else {
        throw HelperFailure.invalidRequest
    }
    return try JSONDecoder().decode(HelperRequest.self, from: data)
}

private func failureResponse(operation: String, code: String) -> HelperResponse {
    HelperResponse(
        ok: false, operation: operation, adapterRef: adapterRef,
        helperVersion: helperVersion, helperVersionRef: helperVersionRef,
        keyRef: nil, keyVersionRef: nil, publicKeyBase64url: nil,
        publicKeyFingerprintRef: nil, signatureBase64url: nil, signatureRef: nil,
        helperReceiptRef: receiptRef(operation: .version, requestRef: nil),
        created: nil, deletedOrAbsent: nil, errorCode: code
    )
}

let input = FileHandle.standardInput.readDataToEndOfFile()
let encoder = JSONEncoder()
encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
private let response: HelperResponse
if input.count > maximumInputBytes {
    response = failureResponse(operation: "unknown", code: HelperFailure.invalidRequest.code)
} else {
    do {
        let request = try decodeStrictRequest(input)
        response = try run(request)
    } catch let failure as HelperFailure {
        response = failureResponse(operation: "unknown", code: failure.code)
    } catch {
        response = failureResponse(operation: "unknown", code: HelperFailure.invalidRequest.code)
    }
}
if let output = try? encoder.encode(response) {
    FileHandle.standardOutput.write(output)
    FileHandle.standardOutput.write(Data([0x0A]))
}
exit(response.ok ? EXIT_SUCCESS : EXIT_FAILURE)
