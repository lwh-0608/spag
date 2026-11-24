import SwiftUI
import SwiftData

struct RecordView: View {
    @Environment(\.modelContext) private var context
    @Query(sort: \MealEntry.date, order: .reverse) private var allEntries: [MealEntry]
    @Query private var profiles: [BodyProfile]
    @EnvironmentObject private var health: HealthKitService
    @State private var sheetTarget: MealSheetTarget?

    private var todayEntries: [MealEntry] {
        allEntries.filter { Calendar.current.isDateInToday($0.date) }
    }
    private var targets: DailyTargets {
        NutritionCalculator.targets(profile: profiles.first,
                                    activeKcal: health.todayActiveEnergy ?? 0,
                                    intakeKcal: todayEntries.reduce(0) { $0 + $1.totalKcal })
    }

    var body: some View {
        NavigationStack {
            List {
                ForEach(MealType.allCases) { type in
                    let entries = todayEntries.filter { $0.mealType == type }
                    Section {
                        if entries.isEmpty {
                            Text("还没有记录")
                                .font(.footnote)
                                .foregroundStyle(.secondary)
                        }
                        ForEach(entries) { entry in
                            Button {
                                sheetTarget = MealSheetTarget(mealType: type, entry: entry)
                            } label: {
                                entryRow(entry)
                            }
                            .buttonStyle(.plain)
                        }
                        .onDelete { offsets in
                            for index in offsets {
                                context.delete(entries[index])
                            }
                            try? context.save()
                        }
                    } header: {
                        HStack {
                            Label(type.title, systemImage: type.symbol)
                            Spacer()
                            if !entries.isEmpty {
                                let cost = entries.reduce(0) { $0 + $1.totalCost }
                                let kcal = entries.reduce(0) { $0 + $1.totalKcal }
                                Text("\(Int(kcal)) kcal · ¥\(String(format: "%.1f", cost))")
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                            } else {
                                Button {
                                    sheetTarget = MealSheetTarget(mealType: type, entry: nil)
                                } label: {
                                    Image(systemName: "plus.circle.fill")
                                }
                                .buttonStyle(.borderless)
                            }
                        }
                    }
                }

                Section {
                    HStack {
                        MetricColumn(title: "已摄入", value: "\(Int(todayEntries.reduce(0) { $0 + $1.totalKcal })) kcal")
                        MetricColumn(title: "目标", value: "\(Int(targets.kcal)) kcal")
                        MetricColumn(title: "蛋白", value: "\(Int(todayEntries.reduce(0) { $0 + $1.totalProtein })) / \(Int(targets.protein)) g")
                    }
                } header: {
                    Text("今日合计")
                }
            }
            .navigationTitle("记录")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Menu {
                        ForEach(MealType.allCases) { type in
                            Button {
                                sheetTarget = MealSheetTarget(mealType: type, entry: nil)
                            } label: {
                                Label("添加\(type.title)", systemImage: type.symbol)
                            }
                        }
                    } label: {
                        Image(systemName: "plus.circle.fill")
                            .font(.title3)
                    }
                }
            }
            .sheet(item: $sheetTarget) { target in
                LogMealView(mealType: target.mealType, existingEntry: target.entry)
            }
        }
    }

    private func entryRow(_ entry: MealEntry) -> some View {
        let metrics = CostCalculator.metrics(for: entry, targets: targets)
        return HStack(spacing: 12) {
            VStack(alignment: .leading, spacing: 3) {
                Text(entry.items.map { $0.foodName }.joined(separator: "、"))
                    .font(.subheadline)
                    .foregroundStyle(.primary)
                    .lineLimit(1)
                Text("\(entry.items.count) 项 · 蛋白 \(Int(entry.totalProtein))g · ¥\(String(format: "%.1f", entry.totalCost))")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 3) {
                Text("\(Int(entry.totalKcal)) kcal")
                    .font(.system(size: 14, weight: .semibold, design: .rounded))
                ScoreBadge(score: metrics.valueScore)
            }
            Image(systemName: "chevron.right")
                .font(.caption2)
                .foregroundStyle(.tertiary)
        }
        .contentShape(Rectangle())
    }
}
