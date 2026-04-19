import Foundation

enum APIError: LocalizedError {
    case unauthorized
    case forbidden(String)
    case notFound
    case server(statusCode: Int, detail: String?)
    case decoding(Error)
    case network(Error)

    var errorDescription: String? {
        switch self {
        case .unauthorized: "Session expired. Please sign in again."
        case .forbidden(let msg): "Access denied: \(msg)"
        case .notFound: "Resource not found."
        case .server(let code, let detail): "Server error \(code): \(detail ?? "unknown")"
        case .decoding(let err): "Failed to read response: \(err.localizedDescription)"
        case .network(let err): "Network error: \(err.localizedDescription)"
        }
    }
}
