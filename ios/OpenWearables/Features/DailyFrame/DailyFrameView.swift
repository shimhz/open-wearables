import SwiftUI

struct DailyFrameView: View {
    @Environment(AppState.self) private var appState
    @State private var viewModel = DailyFrameViewModel()

    var body: some View {
        NavigationStack {
            Group {
                if viewModel.isLoading && viewModel.rows.isEmpty {
                    ProgressView("Loading...")
                } else if let error = viewModel.errorMessage, viewModel.rows.isEmpty {
                    ContentUnavailableView("Failed to load", systemImage: "exclamationmark.triangle", description: Text(error))
                } else if viewModel.rows.isEmpty {
                    ContentUnavailableView("No data yet", systemImage: "chart.bar", description: Text("Connect a wearable and wait for data to sync."))
                } else {
                    List(viewModel.rows) { row in
                        DayRowView(row: row)
                    }
                    .refreshable {
                        await loadData()
                    }
                }
            }
            .navigationTitle("Daily Frame")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Sign Out") {
                        appState.auth.signOut()
                    }
                }
            }
            .task {
                await loadData()
            }
        }
    }

    private func loadData() async {
        guard let userId = appState.auth.userId else { return }
        await viewModel.load(api: appState.api, userId: userId)
    }
}
