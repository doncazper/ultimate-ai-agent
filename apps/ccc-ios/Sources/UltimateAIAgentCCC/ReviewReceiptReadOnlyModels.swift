import Foundation

struct ReviewReceiptReadOnlyItem: Identifiable {
    let id: String
    let label: String
    let value: String
}

struct ReviewReceiptReadOnlySnapshot {
    let title: String
    let items: [ReviewReceiptReadOnlyItem]
    let reviewPacketSummary: String
    let receiptSummary: String
    let authorityBoundary: String
}

enum ReviewReceiptReadOnlyFixtures {
    static let demoSnapshot = ReviewReceiptReadOnlySnapshot(
        title: "Review/Receipt Read-Only Surfaces",
        items: [
            ReviewReceiptReadOnlyItem(
                id: "mode",
                label: "Mode",
                value: "Mock non-authoritative"
            ),
            ReviewReceiptReadOnlyItem(
                id: "review-packet",
                label: "Review packet",
                value: "Redacted review packet summary"
            ),
            ReviewReceiptReadOnlyItem(
                id: "receipt",
                label: "Receipt",
                value: "Redacted receipt summary"
            ),
            ReviewReceiptReadOnlyItem(
                id: "runtime",
                label: "Runtime",
                value: "No runtime network call"
            )
        ],
        reviewPacketSummary: "Redacted review packet summary. Mock non-authoritative; no approval capture and no raw data.",
        receiptSummary: "Redacted receipt summary. Display-only; no raw data, no background collection, and no sensor access.",
        authorityBoundary: "These iOS review/receipt read-only surfaces cannot approve, execute, inject context, write memory, collect in the background, or access sensors."
    )
}
