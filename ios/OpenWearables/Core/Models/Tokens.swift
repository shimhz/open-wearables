import Foundation

struct TokenResponse: Codable {
    let accessToken: String
    let tokenType: String
    let refreshToken: String?
    let expiresIn: Int?
}

struct InvitationRedeemResponse: Codable {
    let accessToken: String
    let tokenType: String
    let refreshToken: String?
    let expiresIn: Int?
    let userId: UUID
}
