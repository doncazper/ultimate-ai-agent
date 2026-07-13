// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "UAAPortableEvidenceKeychainHelper",
    platforms: [.macOS(.v13)],
    products: [
        .executable(
            name: "uaa-portable-evidence-keychain-helper",
            targets: ["UAAPortableEvidenceKeychainHelper"]
        )
    ],
    targets: [
        .executableTarget(
            name: "UAAPortableEvidenceKeychainHelper",
            linkerSettings: [
                .linkedFramework("Security")
            ]
        )
    ]
)
