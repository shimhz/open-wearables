import SwiftUI

@main
struct OpenWearablesApp: App {
    @State private var appState = AppState()

    var body: some Scene {
        WindowGroup {
            if appState.auth.isAuthenticated {
                DailyFrameView()
                    .environment(appState)
            } else {
                InvitationCodeView()
                    .environment(appState)
            }
        }
    }
}
