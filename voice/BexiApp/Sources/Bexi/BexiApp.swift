import SwiftUI

@main
struct BexiApp: App {
    @StateObject private var app = AppState()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(app)
                #if os(macOS)
                .frame(minWidth: 380, minHeight: 560)
                #endif
        }
        #if os(macOS)
        .windowResizability(.contentMinSize)
        #endif
    }
}
