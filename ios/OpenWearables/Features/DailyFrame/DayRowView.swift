import SwiftUI

struct DayRowView: View {
    let row: DailyFrameRow

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(row.date)
                .font(.headline)

            HStack(spacing: 16) {
                metric(label: "Sleep", value: formatMinutes(row.sleep.totalMinutes))
                metric(label: "Score", value: formatScore(row.sleep.primaryScore))
                metric(label: "RHR", value: formatBpm(row.heartRate.restingBpm))
                metric(label: "Meals", value: "\(row.eating.eventsCount)")
            }
            .font(.subheadline)

            if !row.habits.isEmpty {
                HStack(spacing: 8) {
                    ForEach(row.habits) { habit in
                        HabitChip(habit: habit)
                    }
                }
            }
        }
        .padding(.vertical, 4)
    }

    private func metric(label: String, value: String) -> some View {
        VStack(spacing: 2) {
            Text(value)
                .fontWeight(.medium)
            Text(label)
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
    }

    private func formatMinutes(_ mins: Int?) -> String {
        guard let mins else { return "--" }
        return "\(mins / 60)h \(mins % 60)m"
    }

    private func formatScore(_ score: SleepScore?) -> String {
        guard let score, let value = score.value else { return "--" }
        return String(format: "%.0f", value)
    }

    private func formatBpm(_ bpm: Double?) -> String {
        guard let bpm else { return "--" }
        return String(format: "%.0f", bpm)
    }
}

private struct HabitChip: View {
    let habit: DailyHabit

    var body: some View {
        Text(habit.kind == "boolean" ? (habit.value >= 1 ? habit.name : "") : "\(habit.name): \(String(format: "%.0f", habit.value))")
            .font(.caption)
            .padding(.horizontal, 8)
            .padding(.vertical, 2)
            .background(.fill.tertiary, in: .capsule)
    }
}
