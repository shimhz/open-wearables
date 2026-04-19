import Foundation

actor APIClient {
    private let auth: AuthService
    private let baseURL: URL
    private var isRefreshing = false

    init(auth: AuthService, baseURL: URL? = nil) {
        self.auth = auth
        let urlString = Bundle.main.object(forInfoDictionaryKey: "API_BASE_URL") as? String ?? "http://localhost:8000"
        self.baseURL = baseURL ?? URL(string: urlString)!
    }

    func send<T: Decodable>(_ endpoint: Endpoint) async throws -> T {
        let request = try endpoint.urlRequest(baseURL: baseURL, token: auth.accessToken)
        let (data, response) = try await URLSession.shared.data(for: request)
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0

        if status == 401 {
            try await refreshOnce()
            let retryRequest = try endpoint.urlRequest(baseURL: baseURL, token: auth.accessToken)
            let (retryData, retryResponse) = try await URLSession.shared.data(for: retryRequest)
            return try decode(retryData, retryResponse)
        }

        return try decode(data, response)
    }

    private func refreshOnce() async throws {
        guard !isRefreshing else { return }
        isRefreshing = true
        defer { isRefreshing = false }
        try await auth.refresh()
    }

    private func decode<T: Decodable>(_ data: Data, _ response: URLResponse) throws -> T {
        let status = (response as? HTTPURLResponse)?.statusCode ?? 0
        guard (200..<300).contains(status) else {
            let detail = try? JSONDecoder().decode([String: String].self, from: data)
            switch status {
            case 401: throw APIError.unauthorized
            case 403: throw APIError.forbidden(detail?["detail"] ?? "forbidden")
            case 404: throw APIError.notFound
            default: throw APIError.server(statusCode: status, detail: detail?["detail"])
            }
        }
        do {
            let decoder = JSONDecoder()
            decoder.keyDecodingStrategy = .convertFromSnakeCase
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decoding(error)
        }
    }
}
