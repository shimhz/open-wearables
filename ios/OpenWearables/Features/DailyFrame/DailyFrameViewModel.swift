import Foundation

@Observable
final class DailyFrameViewModel {
    var rows: [DailyFrameRow] = []
    var isLoading = false
    var errorMessage: String?

    func load(api: APIClient, userId: UUID) async {
        isLoading = true
        errorMessage = nil

        let end = Date()
        let start = Calendar.current.date(byAdding: .day, value: -13, to: end)!
        let fmt = DateFormatter()
        fmt.dateFormat = "yyyy-MM-dd"

        let endpoint = Endpoints.dailyFrame(
            userId: userId,
            startDate: fmt.string(from: start),
            endDate: fmt.string(from: end)
        )

        do {
            let response: DailyFrameResponse = try await api.send(endpoint)
            rows = response.rows
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
