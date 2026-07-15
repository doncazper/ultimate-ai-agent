// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "UAAMatrixProtectedCacheHelper",
    platforms: [.macOS(.v13)],
    products: [
        .executable(
            name: "uaa-matrix-protected-cache-helper",
            targets: ["UAAMatrixProtectedCacheHelper"]
        ),
    ],
    targets: [
        .executableTarget(name: "UAAMatrixProtectedCacheHelper"),
    ]
)
