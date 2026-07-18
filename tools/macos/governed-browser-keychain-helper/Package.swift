// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "UAAGovernedBrowserKeychainHelper",
    platforms: [.macOS(.v13)],
    products: [
        .executable(
            name: "uaa-governed-browser-keychain-helper",
            targets: ["UAAGovernedBrowserKeychainHelper"]
        )
    ],
    targets: [
        .executableTarget(
            name: "UAAGovernedBrowserKeychainHelper",
            linkerSettings: [
                .linkedFramework("Security")
            ]
        )
    ]
)
