import Foundation

struct Endpoint {
    let method: String
    let path: String
    let queryItems: [URLQueryItem]
    let body: Data?

    init(method: String = "GET", path: String, query: [URLQueryItem] = [], body: Data? = nil) {
        self.method = method
        self.path = path
        self.queryItems = query
        self.body = body
    }

    func urlRequest(baseURL: URL, token: String?) throws -> URLRequest {
        var components = URLComponents(url: baseURL.appendingPathComponent(path), resolvingAgainstBaseURL: false)!
        if !queryItems.isEmpty { components.queryItems = queryItems }
        guard let url = components.url else {
            throw URLError(.badURL)
        }
        var request = URLRequest(url: url)
        request.httpMethod = method
        if let body { request.httpBody = body; request.setValue("application/json", forHTTPHeaderField: "Content-Type") }
        if let token { request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization") }
        return request
    }
}

enum Endpoints {
    static func redeemCode(_ code: String) -> Endpoint {
        let body = try? JSONEncoder().encode(["code": code])
        return Endpoint(method: "POST", path: "/api/v1/invitation-code/redeem", body: body)
    }

    static func refreshToken(_ refreshToken: String) -> Endpoint {
        let body = try? JSONEncoder().encode(["refresh_token": refreshToken])
        return Endpoint(method: "POST", path: "/api/v1/token/refresh", body: body)
    }

    static func dailyFrame(userId: UUID, startDate: String, endDate: String, granularity: String = "day") -> Endpoint {
        Endpoint(
            path: "/api/v1/users/\(userId.uuidString.lowercased())/insights/daily-frame",
            query: [
                URLQueryItem(name: "start_date", value: startDate),
                URLQueryItem(name: "end_date", value: endDate),
                URLQueryItem(name: "granularity", value: granularity),
            ]
        )
    }
}
