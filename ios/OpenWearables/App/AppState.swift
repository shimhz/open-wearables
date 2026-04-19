import Foundation

@Observable
final class AppState {
    let auth: AuthService
    let api: APIClient

    init() {
        let auth = AuthService()
        self.auth = auth
        self.api = APIClient(auth: auth)
    }
}
