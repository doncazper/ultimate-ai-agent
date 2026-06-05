import SwiftUI

@main
struct UltimateAIAgentCCCApp: App {
    var body: some Scene {
        WindowGroup {
            ReadOnlyDashboardView(
                snapshot: SkeletonFixtures.demoSnapshot,
                connectionSnapshot: LocalReadOnlyConnectionFixtures.demoSnapshot,
                reviewReceiptSnapshot: ReviewReceiptReadOnlyFixtures.demoSnapshot
            )
        }
    }
}
