import SwiftUI

struct InvitationCodeView: View {
    @Environment(AppState.self) private var appState
    @State private var viewModel = InvitationCodeViewModel()

    var body: some View {
        NavigationStack {
            VStack(spacing: 32) {
                Spacer()

                VStack(spacing: 8) {
                    Text("Open Wearables")
                        .font(.largeTitle.bold())
                    Text("Enter your invitation code to get started.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }

                TextField("ABCD1234", text: $viewModel.code)
                    .textFieldStyle(.roundedBorder)
                    .font(.title2.monospaced())
                    .multilineTextAlignment(.center)
                    .autocorrectionDisabled()
                    .textInputAutocapitalization(.characters)
                    .padding(.horizontal, 48)
                    .onChange(of: viewModel.code) { _, newValue in
                        if newValue.count > 8 {
                            viewModel.code = String(newValue.prefix(8))
                        }
                    }

                Button {
                    Task { await viewModel.redeem(auth: appState.auth) }
                } label: {
                    if viewModel.isLoading {
                        ProgressView()
                            .frame(maxWidth: .infinity)
                    } else {
                        Text("Redeem")
                            .frame(maxWidth: .infinity)
                    }
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
                .disabled(!viewModel.isValid || viewModel.isLoading)
                .padding(.horizontal, 48)

                if let error = viewModel.errorMessage {
                    Text(error)
                        .font(.caption)
                        .foregroundStyle(.red)
                        .padding(.horizontal)
                }

                Spacer()
                Spacer()
            }
        }
    }
}
