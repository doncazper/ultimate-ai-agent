import Foundation

struct LocalReadOnlyConnectionStatus: Identifiable {
    let id: String
    let label: String
    let value: String
}

struct LocalReadOnlyConnectionSnapshot {
    let title: String
    let statusItems: [LocalReadOnlyConnectionStatus]
    let authorityBoundary: String
}

enum LocalReadOnlyConnectionFixtures {
    static let demoSnapshot = LocalReadOnlyConnectionSnapshot(
        title: "Local Read-Only Connection",
        statusItems: [
            LocalReadOnlyConnectionStatus(
                id: "scope",
                label: "Scope",
                value: "Loopback-only contract"
            ),
            LocalReadOnlyConnectionStatus(
                id: "mode",
                label: "Mode",
                value: "Read-only, non-authoritative"
            ),
            LocalReadOnlyConnectionStatus(
                id: "runtime",
                label: "Runtime",
                value: "No runtime network call"
            )
        ],
        authorityBoundary: "This local read-only connection view cannot approve, execute, inject context, write memory, collect in the background, or access sensors."
    )
}
