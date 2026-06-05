import Foundation

struct SkeletonStatusItem: Identifiable {
    let id: String
    let label: String
    let value: String
}

struct SkeletonSnapshot {
    let title: String
    let statusItems: [SkeletonStatusItem]
    let reviewPreview: String
    let receiptPreview: String
    let authorityBoundary: String
}

enum SkeletonFixtures {
    static let demoSnapshot = SkeletonSnapshot(
        title: "Ultimate AI Agent CCC",
        statusItems: [
            SkeletonStatusItem(
                id: "mode",
                label: "Mode",
                value: "Mock non-authoritative"
            ),
            SkeletonStatusItem(
                id: "surface",
                label: "Surface",
                value: "Read-only iOS skeleton"
            ),
            SkeletonStatusItem(
                id: "authority",
                label: "Authority",
                value: "Python Agent Core only"
            )
        ],
        reviewPreview: "Redacted review packet preview placeholder.",
        receiptPreview: "Redacted receipt preview placeholder.",
        authorityBoundary: "This iOS skeleton cannot approve, execute, inject, store, or mutate."
    )
}
