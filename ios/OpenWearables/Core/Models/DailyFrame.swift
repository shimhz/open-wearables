import Foundation

struct DailyFrameResponse: Codable {
    let userId: UUID
    let startDate: String
    let endDate: String
    let granularity: String
    let rows: [DailyFrameRow]
}

struct DailyFrameRow: Codable, Identifiable {
    var id: String { date }
    let date: String
    let bucket: String
    let sleep: DailySleep
    let heartRate: DailyHeartRate
    let eating: DailyEating
    let habits: [DailyHabit]
}

struct SleepScore: Codable {
    let provider: String
    let value: Double?
}

struct DailySleep: Codable {
    let primaryScore: SleepScore?
    let allScores: [SleepScore]
    let totalMinutes: Int?
    let deepMinutes: Int?
    let remMinutes: Int?
    let lightMinutes: Int?
    let awakeMinutes: Int?
    let efficiency: Double?
    let source: String?
}

struct DailyHeartRate: Codable {
    let restingBpm: Double?
    let avgBpm: Double?
    let minBpm: Double?
    let maxBpm: Double?
    let source: String?
}

struct DailyEating: Codable {
    let firstBiteAt: String?
    let lastBiteAt: String?
    let eatingHours: Double?
    let fastingHours: Double?
    let eventsCount: Int
    let lastBiteToSleepStartMinutes: Int?
}

struct DailyHabit: Codable, Identifiable {
    let id: UUID
    let name: String
    let kind: String
    let value: Double
}
