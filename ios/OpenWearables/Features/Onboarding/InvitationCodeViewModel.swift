import Foundation

@Observable
final class InvitationCodeViewModel {
    var code = ""
    var isLoading = false
    var errorMessage: String?

    var isValid: Bool {
        let charset = CharacterSet(charactersIn: "ABCDEFGHJKLMNPQRSTUVWXYZ23456789")
        return code.count == 8 && code.uppercased().unicodeScalars.allSatisfy { charset.contains($0) }
    }

    func redeem(auth: AuthService) async {
        isLoading = true
        errorMessage = nil
        do {
            try await auth.redeemCode(code)
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
