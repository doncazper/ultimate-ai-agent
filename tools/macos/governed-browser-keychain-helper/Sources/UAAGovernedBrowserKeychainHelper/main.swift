import CryptoKit
import Foundation
import LocalAuthentication
import Security

private let helperVersion = "1.0.0"
private let helperVersionRef = "helper-version-ref:governed-browser-keychain:v1"
private let adapterRef = "adapter-ref:governed-browser-keychain:macos:v1"
private let keychainService = "com.ultimate-ai-agent.governed-browser-credentials.v1"
private let maximumInputBytes = 16 * 1024
private let minimumCredentialBytes = 16
private let maximumCredentialBytes = 4 * 1024
private let safeRefPattern = try! NSRegularExpression(
    pattern: #"^[A-Za-z0-9][A-Za-z0-9._:/-]{2,255}$"#
)

private enum Operation: String, Codable {
    case version
    case store
    case probe
    case delete
}

private struct HelperRequest: Decodable {
    let schemaVersion: String
    let operation: Operation
    let originRef: String?
    let credentialHandleRef: String?
    let credentialGenerationRef: String?
    let keychainItemRef: String?
    let requestRef: String?
    let credentialMaterialBase64url: String?

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case operation
        case originRef = "origin_ref"
        case credentialHandleRef = "credential_handle_ref"
        case credentialGenerationRef = "credential_generation_ref"
        case keychainItemRef = "keychain_item_ref"
        case requestRef = "request_ref"
        case credentialMaterialBase64url = "credential_material_base64url"
    }
}

private struct HelperResponse: Encodable {
    let schemaVersion = "uaa-governed-browser-keychain-helper-response.v1"
    let ok: Bool
    let operation: String
    let adapterRef: String
    let helperVersion: String
    let helperVersionRef: String
    let originRef: String?
    let credentialHandleRef: String?
    let credentialGenerationRef: String?
    let keychainItemRef: String?
    let helperReceiptRef: String
    let created: Bool?
    let present: Bool?
    let deletedOrAbsent: Bool?
    let credentialMaterialIncluded = false
    let credentialMaterialReturned = false
    let browserSessionStarted = false
    let authenticationPerformed = false
    let cookiesUsed = false
    let networkCallPerformed = false
    let externalMutationPerformed = false
    let executionAuthorityGranted = false
    let errorCode: String?

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case ok, operation
        case adapterRef = "adapter_ref"
        case helperVersion = "helper_version"
        case helperVersionRef = "helper_version_ref"
        case originRef = "origin_ref"
        case credentialHandleRef = "credential_handle_ref"
        case credentialGenerationRef = "credential_generation_ref"
        case keychainItemRef = "keychain_item_ref"
        case helperReceiptRef = "helper_receipt_ref"
        case created, present
        case deletedOrAbsent = "deleted_or_absent"
        case credentialMaterialIncluded = "credential_material_included"
        case credentialMaterialReturned = "credential_material_returned"
        case browserSessionStarted = "browser_session_started"
        case authenticationPerformed = "authentication_performed"
        case cookiesUsed = "cookies_used"
        case networkCallPerformed = "network_call_performed"
        case externalMutationPerformed = "external_mutation_performed"
        case executionAuthorityGranted = "execution_authority_granted"
        case errorCode = "error_code"
    }
}

private enum HelperFailure: Error {
    case invalidRequest
    case invalidRef
    case invalidCredential
    case bindingMismatch
    case credentialAlreadyExists
    case keychainLocked
    case keyNotFound
    case keychainStatus(OSStatus)

    var code: String {
        switch self {
        case .invalidRequest: return "HELPER_REQUEST_INVALID"
        case .invalidRef: return "HELPER_REF_INVALID"
        case .invalidCredential: return "HELPER_CREDENTIAL_INVALID"
        case .bindingMismatch: return "HELPER_BINDING_MISMATCH"
        case .credentialAlreadyExists: return "HELPER_CREDENTIAL_ALREADY_EXISTS"
        case .keychainLocked: return "HELPER_KEYCHAIN_LOCKED"
        case .keyNotFound: return "HELPER_KEY_NOT_FOUND"
        case .keychainStatus(let status):
            if status == errSecAuthFailed || status == errSecInteractionNotAllowed {
                return "HELPER_KEYCHAIN_LOCKED"
            }
            return "HELPER_KEYCHAIN_STATUS_\(status)"
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

private func hexDigest(_ data: Data) -> String {
    SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
}

private func expectedKeychainItemRef(
    originRef: String,
    credentialHandleRef: String,
    credentialGenerationRef: String
) -> String {
    let scope = Data(
        "\(originRef)\u{0}\(credentialHandleRef)\u{0}\(credentialGenerationRef)".utf8
    )
    return "keychain-item-ref:governed-browser:sha256:\(hexDigest(scope))"
}

private func accountRef(
    originRef: String,
    credentialHandleRef: String,
    credentialGenerationRef: String
) -> String {
    let scope = Data(
        "\(originRef)\u{0}\(credentialHandleRef)\u{0}\(credentialGenerationRef)".utf8
    )
    return hexDigest(scope)
}

private func helperReceiptRef(operation: Operation, requestRef: String?) -> String {
    let request = requestRef ?? "request-ref:governed-browser-keychain:version"
    return "helper-receipt-ref:governed-browser-keychain:sha256:" +
        hexDigest(Data("\(operation.rawValue)\u{0}\(request)\u{0}\(helperVersionRef)".utf8))
}

private func decodeBase64url(_ value: String) throws -> Data {
    guard value.range(of: #"^[A-Za-z0-9_-]+$"#, options: .regularExpression) != nil else {
        throw HelperFailure.invalidCredential
    }
    var standard = value.replacingOccurrences(of: "-", with: "+")
        .replacingOccurrences(of: "_", with: "/")
    standard += String(repeating: "=", count: (4 - standard.count % 4) % 4)
    guard let data = Data(base64Encoded: standard),
          data.count >= minimumCredentialBytes,
          data.count <= maximumCredentialBytes else {
        throw HelperFailure.invalidCredential
    }
    return data
}

private func baseQuery(
    originRef: String,
    credentialHandleRef: String,
    credentialGenerationRef: String
) -> [String: Any] {
    let context = LAContext()
    context.interactionNotAllowed = true
    return [
        kSecClass as String: kSecClassGenericPassword,
        kSecAttrService as String: keychainService,
        kSecAttrAccount as String: accountRef(
            originRef: originRef,
            credentialHandleRef: credentialHandleRef,
            credentialGenerationRef: credentialGenerationRef
        ),
        kSecAttrSynchronizable as String: kCFBooleanFalse as Any,
        kSecUseAuthenticationContext as String: context,
    ]
}

private func itemPresent(
    originRef: String,
    credentialHandleRef: String,
    credentialGenerationRef: String
) throws -> Bool {
    var query = baseQuery(
        originRef: originRef,
        credentialHandleRef: credentialHandleRef,
        credentialGenerationRef: credentialGenerationRef
    )
    query[kSecReturnAttributes as String] = kCFBooleanTrue
    query[kSecMatchLimit as String] = kSecMatchLimitOne
    var item: CFTypeRef?
    let status = SecItemCopyMatching(query as CFDictionary, &item)
    if status == errSecItemNotFound { return false }
    if status == errSecAuthFailed || status == errSecInteractionNotAllowed {
        throw HelperFailure.keychainLocked
    }
    guard status == errSecSuccess, item is [String: Any] else {
        throw HelperFailure.keychainStatus(status)
    }
    return true
}

private func storeItem(
    originRef: String,
    credentialHandleRef: String,
    credentialGenerationRef: String,
    material: Data
) throws -> Bool {
    if try itemPresent(
        originRef: originRef,
        credentialHandleRef: credentialHandleRef,
        credentialGenerationRef: credentialGenerationRef
    ) {
        throw HelperFailure.credentialAlreadyExists
    }
    var query = baseQuery(
        originRef: originRef,
        credentialHandleRef: credentialHandleRef,
        credentialGenerationRef: credentialGenerationRef
    )
    query[kSecAttrAccessible as String] = kSecAttrAccessibleWhenUnlockedThisDeviceOnly
    query[kSecAttrLabel as String] = "UAA governed browser credential handle"
    query[kSecValueData as String] = material
    let status = SecItemAdd(query as CFDictionary, nil)
    if status == errSecDuplicateItem {
        throw HelperFailure.credentialAlreadyExists
    }
    guard status == errSecSuccess else { throw HelperFailure.keychainStatus(status) }
    return true
}

private func deleteItem(
    originRef: String,
    credentialHandleRef: String,
    credentialGenerationRef: String
) throws {
    let status = SecItemDelete(
        baseQuery(
            originRef: originRef,
            credentialHandleRef: credentialHandleRef,
            credentialGenerationRef: credentialGenerationRef
        ) as CFDictionary
    )
    guard status == errSecSuccess || status == errSecItemNotFound else {
        throw HelperFailure.keychainStatus(status)
    }
}

private struct ExactScope {
    let originRef: String
    let credentialHandleRef: String
    let credentialGenerationRef: String
    let keychainItemRef: String
    let requestRef: String
}

private func exactScope(_ request: HelperRequest) throws -> ExactScope {
    let originRef = try safeRef(request.originRef)
    let credentialHandleRef = try safeRef(request.credentialHandleRef)
    let credentialGenerationRef = try safeRef(request.credentialGenerationRef)
    let keychainItemRef = try safeRef(request.keychainItemRef)
    let requestRef = try safeRef(request.requestRef)
    guard keychainItemRef == expectedKeychainItemRef(
        originRef: originRef,
        credentialHandleRef: credentialHandleRef,
        credentialGenerationRef: credentialGenerationRef
    ) else {
        throw HelperFailure.bindingMismatch
    }
    return ExactScope(
        originRef: originRef,
        credentialHandleRef: credentialHandleRef,
        credentialGenerationRef: credentialGenerationRef,
        keychainItemRef: keychainItemRef,
        requestRef: requestRef
    )
}

private func success(
    operation: Operation,
    scope: ExactScope,
    created: Bool? = nil,
    present: Bool? = nil,
    deletedOrAbsent: Bool? = nil
) -> HelperResponse {
    HelperResponse(
        ok: true,
        operation: operation.rawValue,
        adapterRef: adapterRef,
        helperVersion: helperVersion,
        helperVersionRef: helperVersionRef,
        originRef: scope.originRef,
        credentialHandleRef: scope.credentialHandleRef,
        credentialGenerationRef: scope.credentialGenerationRef,
        keychainItemRef: scope.keychainItemRef,
        helperReceiptRef: helperReceiptRef(
            operation: operation,
            requestRef: scope.requestRef
        ),
        created: created,
        present: present,
        deletedOrAbsent: deletedOrAbsent,
        errorCode: nil
    )
}

private func run(_ request: HelperRequest) throws -> HelperResponse {
    guard request.schemaVersion == "uaa-governed-browser-keychain-helper-request.v1" else {
        throw HelperFailure.invalidRequest
    }
    if request.operation == .version {
        guard request.originRef == nil,
              request.credentialHandleRef == nil,
              request.credentialGenerationRef == nil,
              request.keychainItemRef == nil,
              request.requestRef == nil,
              request.credentialMaterialBase64url == nil else {
            throw HelperFailure.invalidRequest
        }
        return HelperResponse(
            ok: true,
            operation: request.operation.rawValue,
            adapterRef: adapterRef,
            helperVersion: helperVersion,
            helperVersionRef: helperVersionRef,
            originRef: nil,
            credentialHandleRef: nil,
            credentialGenerationRef: nil,
            keychainItemRef: nil,
            helperReceiptRef: helperReceiptRef(operation: .version, requestRef: nil),
            created: nil,
            present: nil,
            deletedOrAbsent: nil,
            errorCode: nil
        )
    }
    let scope = try exactScope(request)
    switch request.operation {
    case .store:
        guard let encoded = request.credentialMaterialBase64url else {
            throw HelperFailure.invalidCredential
        }
        let created = try storeItem(
            originRef: scope.originRef,
            credentialHandleRef: scope.credentialHandleRef,
            credentialGenerationRef: scope.credentialGenerationRef,
            material: try decodeBase64url(encoded)
        )
        return success(
            operation: .store,
            scope: scope,
            created: created,
            present: true
        )
    case .probe:
        guard request.credentialMaterialBase64url == nil else {
            throw HelperFailure.invalidRequest
        }
        guard try itemPresent(
            originRef: scope.originRef,
            credentialHandleRef: scope.credentialHandleRef,
            credentialGenerationRef: scope.credentialGenerationRef
        ) else {
            throw HelperFailure.keyNotFound
        }
        return success(operation: .probe, scope: scope, present: true)
    case .delete:
        guard request.credentialMaterialBase64url == nil else {
            throw HelperFailure.invalidRequest
        }
        try deleteItem(
            originRef: scope.originRef,
            credentialHandleRef: scope.credentialHandleRef,
            credentialGenerationRef: scope.credentialGenerationRef
        )
        return success(
            operation: .delete,
            scope: scope,
            present: false,
            deletedOrAbsent: true
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
        "schema_version",
        "operation",
        "origin_ref",
        "credential_handle_ref",
        "credential_generation_ref",
        "keychain_item_ref",
        "request_ref",
        "credential_material_base64url",
    ])
    guard Set(dictionary.keys).isSubset(of: allowed) else {
        throw HelperFailure.invalidRequest
    }
    return try JSONDecoder().decode(HelperRequest.self, from: data)
}

private func failureResponse(operation: String, code: String) -> HelperResponse {
    HelperResponse(
        ok: false,
        operation: operation,
        adapterRef: adapterRef,
        helperVersion: helperVersion,
        helperVersionRef: helperVersionRef,
        originRef: nil,
        credentialHandleRef: nil,
        credentialGenerationRef: nil,
        keychainItemRef: nil,
        helperReceiptRef: helperReceiptRef(operation: .version, requestRef: nil),
        created: nil,
        present: nil,
        deletedOrAbsent: nil,
        errorCode: code
    )
}

private func readBoundedStandardInput() throws -> Data {
    var input = Data()
    while input.count <= maximumInputBytes {
        let remaining = maximumInputBytes + 1 - input.count
        guard let chunk = try FileHandle.standardInput.read(upToCount: remaining),
              !chunk.isEmpty else {
            return input
        }
        input.append(chunk)
        if input.count > maximumInputBytes {
            throw HelperFailure.invalidRequest
        }
    }
    throw HelperFailure.invalidRequest
}

let encoder = JSONEncoder()
encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
private let response: HelperResponse
do {
    let input = try readBoundedStandardInput()
    let request = try decodeStrictRequest(input)
    response = try run(request)
} catch let failure as HelperFailure {
    response = failureResponse(operation: "unknown", code: failure.code)
} catch {
    response = failureResponse(
        operation: "unknown",
        code: HelperFailure.invalidRequest.code
    )
}
if let output = try? encoder.encode(response) {
    FileHandle.standardOutput.write(output)
    FileHandle.standardOutput.write(Data([0x0A]))
}
exit(response.ok ? EXIT_SUCCESS : EXIT_FAILURE)
