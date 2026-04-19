import Foundation

@Observable
final class AuthService {
    private(set) var isAuthenticated = false
    private(set) var userId: UUID?

    private let keychain: KeychainStore
    private let baseURL: URL

    init(keychain: KeychainStore = KeychainStore(), baseURL: URL? = nil) {
        self.keychain = keychain
        self.baseURL = baseURL ?? Self.resolvedBaseURL()
        if let stored = keychain.get("user_id"), let uid = UUID(uuidString: stored),
           keychain.get("access_token") != nil {
            self.userId = uid
            self.isAuthenticated = true
        }
    }

    var accessToken: String? { keychain.get("access_token") }
    var refreshToken: String? { keychain.get("refresh_token") }

    func redeemCode(_ code: String) async throws {
        let endpoint = Endpoints.redeemCode(code.uppercased())
        let request = try endpoint.urlRequest(baseURL: baseURL, token: nil)
        let (data, response) = try await URLSession.shared.data(for: request)
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0
        guard (200..<300).contains(status) else {
            let detail = try? JSONDecoder().decode([String: String].self, from: data)
            throw APIError.server(statusCode: status, detail: detail?["detail"])
        }
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let result = try decoder.decode(InvitationRedeemResponse.self, from: data)
        storeTokens(access: result.accessToken, refresh: result.refreshToken, userId: result.userId)
    }

    func refresh() async throws {
        guard let rt = refreshToken else { throw APIError.unauthorized }
        let endpoint = Endpoints.refreshToken(rt)
        let request = try endpoint.urlRequest(baseURL: baseURL, token: nil)
        let (data, response) = try await URLSession.shared.data(for: request)
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0
        guard (200..<300).contains(status) else {
            signOut()
            throw APIError.unauthorized
        }
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let result = try decoder.decode(TokenResponse.self, from: data)
        keychain.set(result.accessToken, for: "access_token")
        if let newRt = result.refreshToken {
            keychain.set(newRt, for: "refresh_token")
        }
    }

    func signOut() {
        keychain.deleteAll()
        isAuthenticated = false
        userId = nil
    }

    private func storeTokens(access: String, refresh: String?, userId: UUID) {
        keychain.set(access, for: "access_token")
        if let refresh { keychain.set(refresh, for: "refresh_token") }
        keychain.set(userId.uuidString, for: "user_id")
        self.userId = userId
        self.isAuthenticated = true
    }

    private static func resolvedBaseURL() -> URL {
        let urlString = Bundle.main.object(forInfoDictionaryKey: "API_BASE_URL") as? String ?? "http://localhost:8000"
        return URL(string: urlString)!
    }
}
