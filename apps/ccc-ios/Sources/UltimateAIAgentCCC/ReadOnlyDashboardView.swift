import SwiftUI

struct ReadOnlyDashboardView: View {
    let snapshot: SkeletonSnapshot

    var body: some View {
        NavigationStack {
            List {
                Section("Status") {
                    ForEach(snapshot.statusItems) { item in
                        LabeledContent(item.label, value: item.value)
                    }
                }

                Section("Review Preview") {
                    Text(snapshot.reviewPreview)
                        .font(.body)
                        .accessibilityLabel("Mock redacted review packet preview")
                }

                Section("Receipt Preview") {
                    Text(snapshot.receiptPreview)
                        .font(.body)
                        .accessibilityLabel("Mock redacted receipt preview")
                }

                Section("Authority Boundary") {
                    Text(snapshot.authorityBoundary)
                        .font(.callout)
                        .foregroundStyle(.secondary)
                        .accessibilityLabel("No authority boundary")
                }
            }
            .navigationTitle(snapshot.title)
        }
    }
}

#Preview {
    ReadOnlyDashboardView(snapshot: SkeletonFixtures.demoSnapshot)
}
