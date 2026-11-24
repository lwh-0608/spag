import SwiftUI
import SwiftData
import Charts

struct ReportView: View {
    @Query(sort: \MealEntry.date, order: .reverse) private var allEntries: [MealEntry]
    @Query(sort: \WeightLog.date, order: .reverse) private var weights: [WeightLog]
    @Query private var profiles: [BodyProfile]
    @EnvironmentObject private var health: HealthKitService

    struct DayStat: Identifiable {
        let date: Date
        let kcal: Double
        let cost: Double
        let protein: Double
        var id: Date { date }
    }

    private var last7: [DayStat] {
        (0..<7).reversed().compactMap { offset in
            guard let date = Calendar.current.date(byAdding: .day, value: -offset, to: Date()) else { return nil }
            let entries = allEntries.filter { Calendar.current.isDate($0.date, inSameDayAs: date) }
            return DayStat(date: date,
                           kcal: entries.reduce(0) { $0 + $1.totalKcal },
                           cost: entries.reduce(0) { $0 + $1.totalCost },
                           protein: entries.reduce(0) { $0 + $1.totalProtein })
        }
    }

    private var targetProtein: Double {
        NutritionCalculator.targets(profile: profiles.first,
                                    activeKcal: health.todayActiveEnergy ?? 0,
                                    intakeKcal: 0).protein
    }
    private var totalCost: Double { last7.reduce(0) { $0 + $1.cost } }
    private var avgCost: Double { totalCost / 7 }
    private var avgKcal: Double { last7.reduce(0) { $0 + $1.kcal } / 7 }
    private var adherence: Double {
        guard targetProtein > 0 else { return 0 }
        let hit = last7.filter { $0.protein >= targetProtein * 0.8 }.count
        return Double(hit) / 7 * 100
    }
    private var weightValues: [Double] {
        Array(weights.prefix(14)).reversed().map { $0.weightKg }
    }
    private var weightDomain: ClosedRange<Double> {
        guard let minValue = weightValues.min(), let maxValue = weightValues.max() else {
            return 60...80
        }
        let pad = max(0.8, (maxValue - minValue) * 0.6)
        return (minValue - pad)...(maxValue + pad)
    }
    private var weightChange: Double? {
        guard let first = weights.first?.weightKg, let last = weights.last?.weightKg else { return nil }
        return last - first
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 14) {
                    statGrid
                    costChart
                    proteinSection
                    weightChart
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 28)
            }
            .background(Theme.background)
            .navigationTitle("报告")
        }
    }

    private var statGrid: some View {
        LazyVGrid(columns: [GridItem(.flexible(), spacing: 12), GridItem(.flexible(), spacing: 12)], spacing: 12) {
            statCard(title: "7 天总花费", value: "¥" + String(format: "%.0f", totalCost), caption: "日均 ¥" + String(format: "%.1f", avgCost))
            statCard(title: "日均摄入", value: "\(Int(avgKcal)) kcal", caption: "目标 \(Int(NutritionCalculator.targets(profile: profiles.first, activeKcal: health.todayActiveEnergy ?? 0, intakeKcal: avgKcal).kcal))")
            statCard(title: "蛋白达标率", value: "\(Int(adherence))%", caption: "目标 \(Int(targetProtein))g/天")
            statCard(title: "体重变化", value: weightChange.map { String(format: "%+.1f kg", $0) } ?? "-", caption: "近 \(weights.prefix(14).count) 次记录")
        }
    }

    private func statCard(title: String, value: String, caption: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption2)
                .foregroundStyle(.secondary)
            Text(value)
                .font(.system(size: 22, weight: .semibold, design: .rounded))
            Text(caption)
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .cardStyle()
    }

    private var costChart: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("近 7 天餐费")
                .font(.headline)
            Chart(last7) { day in
                BarMark(
                    x: .value("日期", day.date, unit: .day),
                    y: .value("花费", day.cost)
                )
                .foregroundStyle(Theme.accent.gradient)
                .cornerRadius(6)
            }
            .chartXAxis {
                AxisMarks(values: .stride(by: .day)) { _ in
                    AxisValueLabel(format: .dateTime.month(.defaultDigits).day())
                }
            }
            .frame(height: 170)
        }
        .cardStyle()
    }

    private var proteinSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("近 7 天蛋白质")
                .font(.headline)
            HStack(alignment: .bottom, spacing: 10) {
                ForEach(last7) { day in
                    VStack(spacing: 4) {
                        Text("\(Int(day.protein))")
                            .font(.system(size: 10, weight: .medium, design: .rounded))
                            .foregroundStyle(.secondary)
                        RoundedRectangle(cornerRadius: 4)
                            .fill(day.protein >= targetProtein * 0.8 ? Color.green.opacity(0.75) : Theme.accent.opacity(0.45))
                            .frame(height: max(6, min(80, day.protein / max(targetProtein, 1) * 80)))
                        Text(day.date, format: .dateTime.day())
                            .font(.system(size: 9))
                            .foregroundStyle(.secondary)
                    }
                    .frame(maxWidth: .infinity)
                }
            }
        }
        .cardStyle()
    }

    private var weightChart: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("体重趋势")
                .font(.headline)
            if weights.isEmpty {
                Text("还没有体重记录")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            } else {
                Chart(Array(weights.prefix(14)).reversed()) { log in
                    LineMark(
                        x: .value("日期", log.date),
                        y: .value("体重", log.weightKg)
                    )
                    .foregroundStyle(.pink)
                    PointMark(
                        x: .value("日期", log.date),
                        y: .value("体重", log.weightKg)
                    )
                    .foregroundStyle(.pink)
                }
                .chartXAxis {
                    AxisMarks(values: .stride(by: .day, count: 3)) { _ in
                        AxisValueLabel(format: .dateTime.month(.defaultDigits).day())
                    }
                }
                .chartYScale(domain: weightDomain)
                .frame(height: 150)
            }
        }
        .cardStyle()
    }
}
