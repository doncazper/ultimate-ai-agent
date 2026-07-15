import Foundation

private let maximumInputBytes = 4 * 1024
private let schemaVersion = "uaa-matrix-session-keychain-helper-request.v1"

private struct HelperResponse: Encodable {
    let schemaVersion = "uaa-matrix-session-keychain-helper-response.v1"
    let ok: Bool
    let operation: String
    let adapterRef = "adapter-ref:matrix-session-keychain:macos:v1"
    let helperVersion = "1.0.0"
    let helperVersionRef = "helper-version-ref:matrix-session-keychain:v1"
    let helperReceiptRef: String
    let credentialMaterialIncluded = false
    let executionAuthorityGranted = false
    let errorCode: String?

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case ok, operation
        case adapterRef = "adapter_ref"
        case helperVersion = "helper_version"
        case helperVersionRef = "helper_version_ref"
        case helperReceiptRef = "helper_receipt_ref"
        case credentialMaterialIncluded = "credential_material_included"
        case executionAuthorityGranted = "execution_authority_granted"
        case errorCode = "error_code"
    }
}

private func response(ok: Bool, operation: String, errorCode: String? = nil) -> HelperResponse {
    HelperResponse(
        ok: ok,
        operation: operation,
        helperReceiptRef: ok
            ? "helper-receipt-ref:matrix-session-keychain:version-v1"
            : "helper-receipt-ref:matrix-session-keychain:blocked-v1",
        errorCode: errorCode
    )
}

private func emit(_ value: HelperResponse) {
    guard let data = try? JSONEncoder().encode(value) else { exit(2) }
    FileHandle.standardOutput.write(data)
}

let input = FileHandle.standardInput.readDataToEndOfFile()
guard input.count <= maximumInputBytes,
      let object = try? JSONSerialization.jsonObject(with: input),
      let request = object as? [String: Any],
      Set(request.keys) == Set(["schema_version", "operation"]),
      request["schema_version"] as? String == schemaVersion,
      let operation = request["operation"] as? String else {
    emit(response(ok: false, operation: "unknown", errorCode: "MATRIX_KEYCHAIN_REQUEST_INVALID"))
    exit(2)
}

guard operation == "version" else {
    emit(response(
        ok: false,
        operation: operation,
        errorCode: "MATRIX_KEYCHAIN_CALLER_AUTH_REQUIRED"
    ))
    exit(2)
}

emit(response(ok: true, operation: operation))
