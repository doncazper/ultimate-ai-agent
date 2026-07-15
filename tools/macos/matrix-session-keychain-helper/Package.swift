// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "UAAMatrixSessionKeychainHelper",
    platforms: [.macOS(.v13)],
    products: [
        .executable(
            name: "uaa-matrix-session-keychain-helper",
            targets: ["UAAMatrixSessionKeychainHelper"]
        ),
    ],
    targets: [
        .executableTarget(name: "UAAMatrixSessionKeychainHelper"),
    ]
)
