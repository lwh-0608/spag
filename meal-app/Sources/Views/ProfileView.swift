import SwiftUI
import SwiftData

struct ProfileView: View {
    @Environment(\.modelContext) private var context
    @EnvironmentObject private var health: HealthKitService
    @Query private var profiles: [BodyProfile]
    @Query(sort: \WeightLog.date, order: .reverse) private var weights: [WeightLog]

    @State private var sex: Sex = .male
    @State private var birthYear: Int = 1995
    @State private var heightCm: String = "175"
    @State private var weightKg: String = "70"
    @State private var targetWeightKg: String = "65"
    @State private var goal: Goal = .lightLoss
    @State private var budgetPerDay: String = "60"
    @State private var exportURL: URL?
    @State private var loaded = false
    @State private var statusMessage = ""

    var body: some View {
        NavigationStack {
            Form {
                Section("目标") {
                    Picker("目标", selection: $goal) {
                        ForEach(Goal.allCases) { goal in
                            Text(goal.title).tag(goal)
                        }
                    }
                    HStack {
                        Text("每日餐费预算")
                        Spacer()
                        TextField("元", text: $budgetPerDay)
                            .keyboardType(.decimalPad)
                            .multilineTextAlignment(.trailing)
                    }
                }

                Section("身体数据") {
                    Picker("性别", selection: $sex) {
                        ForEach(Sex.allCases) { sex in
                            Text(sex.title).tag(sex)
                        }
                    }
                    .pickerStyle(.segmented)
                    Stepper(value: $birthYear, in: 1940...2012) {
                        HStack {
                            Text("出生年")
                            Spacer()
                            Text(verbatim: String(birthYear)).foregroundStyle(.secondary)
                        }
                    }
                    HStack {
                        Text("身高 cm")
                        Spacer()
                        TextField("175", text: $heightCm).keyboardType(.decimalPad).multilineTextAlignment(.trailing)
                    }
                    HStack {
                        Text("体重 kg")
                        Spacer()
                        TextField("70", text: $weightKg).keyboardType(.decimalPad).multilineTextAlignment(.trailing)
                    }
                    HStack {
                        Text("目标体重 kg")
                        Spacer()
                        TextField("65", text: $targetWeightKg).keyboardType(.decimalPad).multilineTextAlignment(.trailing)
                    }
                }

                Section("健康数据") {
                    HStack {
                        Image(systemName: "heart.fill").foregroundStyle(.pink)
                        Text(health.statusText)
                            .font(.footnote)
                        Spacer()
                        if let weight = health.latestWeightKg {
                            Text("\(String(format: "%.1f", weight)) kg")
                                .font(.footnote)
                                .foregroundStyle(.secondary)
                        }
                    }
                    Button("连接健康 App") {
                        Task { await health.requestAuthorization() }
                    }
                    Button("刷新健康数据") {
                        Task { await health.refresh() }
                    }
                }

                Section("数据") {
                    if let exportURL {
                        ShareLink(item: exportURL) {
                            Label("分享导出文件", systemImage: "square.and.arrow.up")
                        }
                    }
                    Button("生成导出文件（JSON）") {
                        exportURL = generateExport()
                    }
                }

                Section {
                    Text("数值为根据食物库和身体数据估算，仅用于个人饮食记录，不构成医疗或营养建议。数据仅保存在本机。")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("我的")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("保存") { saveProfile() }
                }
            }
            .onAppear(perform: loadProfile)
            .onDisappear(perform: saveProfile)
        }
    }

    private func loadProfile() {
        guard !loaded else { return }
        loaded = true
        guard let profile = profiles.first else { return }
        sex = profile.sex
        birthYear = profile.birthYear
        heightCm = String(format: "%.0f", profile.heightCm)
        weightKg = String(format: "%.1f", profile.weightKg)
        targetWeightKg = String(format: "%.1f", profile.targetWeightKg)
        goal = profile.goal
        budgetPerDay = String(format: "%.0f", profile.budgetPerDay)
    }

    private func saveProfile() {
        let height = Double(heightCm) ?? 175
        let weight = Double(weightKg) ?? 70
        let target = Double(targetWeightKg) ?? weight
        let budget = Double(budgetPerDay) ?? 60

        if let profile = profiles.first {
            profile.sex = sex
            profile.birthYear = birthYear
            profile.heightCm = height
            profile.weightKg = weight
            profile.targetWeightKg = target
            profile.goal = goal
            profile.budgetPerDay = budget
            profile.updatedAt = Date()
        } else {
            context.insert(BodyProfile(sex: sex, birthYear: birthYear, heightCm: height,
                                       weightKg: weight, targetWeightKg: target,
                                       goal: goal, budgetPerDay: budget))
        }
        if let latest = weights.first {
            if abs(latest.weightKg - weight) > 0.05 {
                context.insert(WeightLog(date: Date(), weightKg: weight))
            }
        } else {
            context.insert(WeightLog(date: Date(), weightKg: weight))
        }
        try? context.save()
        statusMessage = "已保存"
    }

    private func generateExport() -> URL? {
        var payload: [String: Any] = [:]
        if let profile = profiles.first {
            payload["profile"] = [
                "sex": profile.sexRaw,
                "birthYear": profile.birthYear,
                "heightCm": profile.heightCm,
                "weightKg": profile.weightKg,
                "targetWeightKg": profile.targetWeightKg,
                "goal": profile.goalRaw,
                "budgetPerDay": profile.budgetPerDay
            ]
        }
        let entries: [[String: Any]] = (try? context.fetch(FetchDescriptor<MealEntry>()))?.map { entry in
            [
                "date": ISO8601DateFormatter().string(from: entry.date),
                "mealType": entry.mealTypeRaw,
                "kcal": entry.totalKcal,
                "protein": entry.totalProtein,
                "fat": entry.totalFat,
                "carb": entry.totalCarb,
                "cost": entry.totalCost,
                "items": entry.items.map { ["name": $0.foodName, "grams": $0.grams] }
            ]
        } ?? []
        payload["meals"] = entries
        let weightsPayload: [[String: Any]] = (try? context.fetch(FetchDescriptor<WeightLog>()))?.map {
            ["date": ISO8601DateFormatter().string(from: $0.date), "weightKg": $0.weightKg]
        } ?? []
        payload["weights"] = weightsPayload

        guard let data = try? JSONSerialization.data(withJSONObject: payload, options: [.prettyPrinted]) else {
            return nil
        }
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("mealvalue-export.json")
        try? data.write(to: url)
        return url
    }
}
