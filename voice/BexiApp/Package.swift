// swift-tools-version:5.9
// Bexi — Mac uygulaması (SwiftPM ile, tam Xcode gerektirmeden derlenir).
// iOS hedefi ayni Sources/Bexi kaynaklarini kullanir (bkz. project.yml —
// Xcode kurulunca xcodegen ile .xcodeproj uretilir).
import PackageDescription

let package = Package(
    name: "Bexi",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(
            name: "Bexi",
            path: "Sources/Bexi"
        )
    ]
)
