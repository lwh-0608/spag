import SwiftUI
import SwiftData

struct TodayView: View {
    @Query(sort: \MealEntry.date, order: .reverse) private var allEntries: [MealEntry]
    @Query private var profiles: [BodyProfile]
    @EnvironmentObject private var health: HealthKitService
    @State private var sheetTarget: MealSheetTarget?

    private var calendar: Calendar { Calendar.current }
    private var todayEntries: [MealEntry] {
        allEntries.filter { calendar.isDateInToday($0.date) }
    }
    private var profile: BodyProfile? { profiles.first }

    private var consumedKcal: Double { todayEntries.reduce(0) { $0 + $1.totalKcal } }
    private var consumedProtein: Double { todayEntries.reduce(0) { $0 + $1.totalProtein } }
    private var consumedFat: Double { todayEntries.reduce(0) { $0 + $1.totalFat } }
    private var consumedCarb: Double { todayEntries.reduce(0) { $0 + $1.totalCarb } }
    private var consumedCost: Double { todayEntries.reduce(0) { $0 + $1.totalCost } }
    private var budget: Double { profile?.budgetPerDay ?? 60 }

    private var targets: DailyTargets {
        NutritionCalculator.targets(profile: profile,
                                    activeKcal: health.todayActiveEnergy ?? 0,
                                    intakeKcal: consumedKcal)
    }
    private var addBackKcal: Double { (health.todayActiveEnergy ?? 0) * 0.5 }
    private var remainingKcal: Double {
        NutritionCalculator.remainingKcal(targets: targets, consumed: consumedKcal,
                                         activeKcal: health.todayActiveEnergy ?? 0)
    }

    private var dateTitle: String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "zh_CN")
        formatter.dateFormat = "M月d日 EEEE"
        return formatter.string(from: Date())
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 14) {
                    ringCard
                    macroCard
                    costCard
                    healthCard
                    mealsSection
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 28)
            }
            .background(Theme.background)
            .navigationTitle(dateTitle)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Menu {
                        ForEach(MealType.allCases) { type in
                            Button {
                                sheetTarget = MealSheetTarget(mealType: type, entry: entry(for: type))
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
                LogMealView(mealType: target.mealType, existingEntry: target.entry,
                            previewItems: target.previewItems)
            }
            .onReceive(NotificationCenter.default.publisher(for: .openLogMeal)) { note in
                guard let raw = note.object as? String, let type = MealType(rawValue: raw) else { return }
                let preview = (note.userInfo?["preview"] as? Bool) ?? false
                sheetTarget = MealSheetTarget(mealType: type, entry: nil, previewItems: preview)
            }
        }
    }

    private func entry(for type: MealType) -> MealEntry? {
        todayEntries.first { $0.mealType == type }
    }

    private var ringCard: some View {
        VStack(spacing: 6) {
            ZStack {
                Circle()
                    .stroke(Color.primary.opacity(0.07), lineWidth: 14)
                Circle()
                    .trim(from: 0, to: min(1, consumedKcal / max(targets.kcal, 1)))
                    .stroke(
                        AngularGradient(colors: [Theme.accent, .green], center: .center),
                        style: StrokeStyle(lineWidth: 14, lineCap: .round)
                    )
                    .rotationEffect(.degrees(-90))
                    .animation(.easeInOut(duration: 0.4), value: consumedKcal)
                VStack(spacing: 2) {
                    Text("\(Int(consumedKcal))")
                        .font(.system(size: 42, weight: .semibold, design: .rounded))
                    Text("/ \(Int(targets.kcal)) kcal")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text("还能吃 \(Int(remainingKcal)) kcal")
                        .font(.caption2.weight(.medium))
                        .foregroundStyle(Theme.accent)
                }
            }
            .frame(width: 200, height: 200)
            .padding(.top, 8)

            Text(consumedKcal > targets.kcal
                 ? "已超出今日目标"
                 : "目标 \(Int(targets.kcal)) kcal + 运动加回 \(Int(addBackKcal)) kcal")
                .font(.footnote)
                .foregroundStyle(.secondary)
        }
        .cardStyle()
    }

    private var macroCard: some View {
        HStack(spacing: 16) {
            macroColumn(title: "蛋白质", consumed: consumedProtein, target: targets.protein, tint: .blue)
            macroColumn(title: "脂肪", consumed: consumedFat, target: targets.fat, tint: .orange)
            macroColumn(title: "碳水", consumed: consumedCarb, target: targets.carb, tint: .purple)
        }
        .cardStyle()
    }

    private func macroColumn(title: String, consumed: Double, target: Double, tint: Color) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.caption2)
                .foregroundStyle(.secondary)
            Text("\(Int(consumed))g")
                .font(.system(size: 18, weight: .semibold, design: .rounded))
            ProgressView(value: min(1, consumed / max(target, 1)))
                .tint(tint)
            Text("目标 \(Int(target))g")
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private var costCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Label("今日花费", systemImage: "yensign.circle.fill")
                    .font(.subheadline.weight(.medium))
                Spacer()
                Text("¥\(costText(consumedCost)) / 预算 ¥\(costText(budget))")
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(consumedCost > budget ? .orange : .primary)
            }
            ProgressView(value: min(1, consumedCost / max(budget, 1)))
                .tint(consumedCost > budget ? .orange : .green)
            HStack {
                MetricColumn(title: "元 / 100kcal", value: consumedKcal > 0 ? String(format: "%.1f", consumedCost / consumedKcal * 100) : "-")
                MetricColumn(title: "元 / 10g蛋白", value: consumedProtein > 0 ? String(format: "%.1f", consumedCost / consumedProtein * 10) : "-")
                MetricColumn(title: "剩余预算", value: "¥" + costText(max(0, budget - consumedCost)))
            }
        }
        .cardStyle()
    }

    private var healthCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Label("健康 App 运动消耗", systemImage: "heart.fill")
                    .font(.subheadline.weight(.medium))
                    .foregroundStyle(.pink)
                Spacer()
                Text(health.todayActiveEnergy.map { "\(Int($0)) kcal" } ?? "未连接")
                    .font(.subheadline.weight(.semibold))
            }
            Text(health.statusText)
                .font(.caption2)
                .foregroundStyle(.secondary)
            Text("目标已计入运动消耗的 50%（加回比例可后续在设置里调整）")
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .cardStyle()
    }

    private var mealsSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("今日餐次")
                .font(.headline)
                .padding(.leading, 4)
            ForEach(MealType.allCases) { type in
                mealRow(type: type)
            }
        }
    }

    private func mealRow(type: MealType) -> some View {
        let entries = todayEntries.filter { $0.mealType == type }
        let kcal = entries.reduce(0) { $0 + $1.totalKcal }
        let cost = entries.reduce(0) { $0 + $1.totalCost }
        let protein = entries.reduce(0) { $0 + $1.totalProtein }
        let score = entries.isEmpty ? 0 : entries.reduce(0) { sum, entry in
            sum + CostCalculator.metrics(for: entry, targets: targets).valueScore
        } / Double(entries.count)

        return Button {
            sheetTarget = MealSheetTarget(mealType: type, entry: entries.first)
        } label: {
            HStack(spacing: 12) {
                Image(systemName: type.symbol)
                    .font(.system(size: 18, weight: .medium))
                    .foregroundStyle(Theme.accent)
                    .frame(width: 34, height: 34)
                    .background(Theme.accent.opacity(0.12), in: Circle())

                VStack(alignment: .leading, spacing: 3) {
                    HStack(spacing: 6) {
                        Text(type.title)
                            .font(.subheadline.weight(.semibold))
                            .foregroundStyle(.primary)
                        if !entries.isEmpty {
                            ScoreBadge(score: score)
                        }
                    }
                    if entries.isEmpty {
                        Text("点击记录这一餐")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    } else {
                        Text(entries.flatMap { $0.items }.map { $0.foodName }.joined(separator: "、"))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                    }
                }
                Spacer()
                if entries.isEmpty {
                    Image(systemName: "plus")
                        .font(.caption.weight(.bold))
                        .foregroundStyle(Theme.accent)
                } else {
                    VStack(alignment: .trailing, spacing: 2) {
                        Text("\(Int(kcal)) kcal")
                            .font(.system(size: 14, weight: .semibold, design: .rounded))
                        Text("¥\(costText(cost)) · 蛋白\(Int(protein))g")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                    Image(systemName: "chevron.right")
                        .font(.caption2)
                        .foregroundStyle(.tertiary)
                }
            }
            .cardStyle()
        }
        .buttonStyle(.plain)
    }

    private func costText(_ value: Double) -> String {
        String(format: value >= 100 ? "%.0f" : "%.1f", value)
    }
}
