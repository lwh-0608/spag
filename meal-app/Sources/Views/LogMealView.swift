import SwiftUI
import SwiftData

struct LogMealView: View {
    @Environment(\.modelContext) private var context
    @Environment(\.dismiss) private var dismiss
    @Query(sort: \FoodItem.name) private var foods: [FoodItem]
    @Query private var profiles: [BodyProfile]

    let mealType: MealType
    let existingEntry: MealEntry?

    @State private var items: [MealItemSnapshot] = []
    @State private var searchText = ""
    @State private var pricingMode: PricingMode = .homemade
    @State private var takeoutPriceText = ""
    @State private var note = ""
    @State private var didLoad = false

    private var filteredFoods: [FoodItem] {
        if searchText.isEmpty {
            return Array(foods.prefix(40))
        }
        return foods.filter {
            $0.name.localizedCaseInsensitiveContains(searchText)
                || $0.aliases.localizedCaseInsensitiveContains(searchText)
        }
    }

    private var totalKcal: Double { items.reduce(0) { $0 + $1.kcal } }
    private var totalProtein: Double { items.reduce(0) { $0 + $1.protein } }

    private var computedCost: Double {
        if pricingMode == .takeout, let price = Double(takeoutPriceText) {
            return price
        }
        return items.reduce(0) { $0 + $1.pricePer100 * $1.grams / 100 }
    }

    private var targets: DailyTargets {
        NutritionCalculator.targets(profile: profiles.first, activeKcal: 0, intakeKcal: totalKcal)
    }

    private var previewScore: Double {
        let temp = MealEntry(date: Date(), mealType: mealType, items: items)
        temp.priceOverride = pricingMode == .takeout ? Double(takeoutPriceText) : nil
        return CostCalculator.metrics(for: temp, targets: targets).valueScore
    }

    var body: some View {
        NavigationStack {
            List {
                Section {
                    Picker("餐次", selection: .constant(mealType)) {
                        ForEach(MealType.allCases) { type in
                            Text(type.title).tag(type)
                        }
                    }
                    Picker("计价方式", selection: $pricingMode) {
                        ForEach(PricingMode.allCases) { mode in
                            Text(mode.title).tag(mode)
                        }
                    }
                    .pickerStyle(.segmented)
                    if pricingMode == .takeout {
                        TextField("整餐价格（元）", text: $takeoutPriceText)
                            .keyboardType(.decimalPad)
                    }
                }

                Section("已选食物") {
                    if items.isEmpty {
                        Text("还没有添加食物，从下方选择")
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                    }
                    ForEach($items) { $item in
                        HStack(spacing: 8) {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(item.foodName)
                                    .font(.subheadline)
                                Text("\(Int(item.kcal)) kcal · 蛋白 \(String(format: "%.1f", item.protein))g")
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                            }
                            Spacer()
                            TextField("克数", value: Binding(
                                get: { item.grams },
                                set: { newValue in
                                    item = item.scaled(toGrams: max(1, min(2000, newValue)))
                                }
                            ), format: .number)
                            .keyboardType(.numberPad)
                            .multilineTextAlignment(.trailing)
                            .frame(width: 56)
                            Text("g")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            Button {
                                items.removeAll { $0.id == item.id }
                            } label: {
                                Image(systemName: "minus.circle.fill")
                                    .foregroundStyle(.red)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }

                Section("食物库") {
                    ForEach(filteredFoods) { food in
                        Button {
                            add(food)
                        } label: {
                            HStack {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(food.name)
                                        .font(.subheadline)
                                        .foregroundStyle(.primary)
                                    Text("\(Int(food.kcalPer100)) kcal/100g · 蛋白 \(String(format: "%.1f", food.proteinPer100))g · ¥\(String(format: "%.1f", food.pricePer100))/100g")
                                        .font(.caption2)
                                        .foregroundStyle(.secondary)
                                }
                                Spacer()
                                Image(systemName: "plus.circle")
                                    .foregroundStyle(Theme.accent)
                            }
                        }
                        .buttonStyle(.plain)
                    }
                }

                Section("本餐合计") {
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text("\(Int(totalKcal)) kcal")
                                .font(.system(size: 22, weight: .semibold, design: .rounded))
                            Text("蛋白 \(String(format: "%.1f", totalProtein))g · 花费 ¥\(String(format: "%.1f", computedCost))")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                        Spacer()
                        VStack(alignment: .trailing, spacing: 4) {
                            Text("性价比 \(Int(previewScore))")
                                .font(.system(size: 15, weight: .semibold, design: .rounded))
                                .foregroundStyle(previewScore >= 70 ? .green : (previewScore >= 50 ? .orange : .red))
                            Text(CostCalculator.scoreLabel(previewScore))
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                    }
                }

                Section("备注（可选）") {
                    TextField("例如：和朋友聚餐", text: $note)
                }
            }
            .searchable(text: $searchText, placement: .navigationBarDrawer(displayMode: .always), prompt: "搜索食物")
            .navigationTitle(existingEntry == nil ? "记录\(mealType.title)" : "编辑\(mealType.title)")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("取消") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("保存") { save() }
                        .disabled(items.isEmpty)
                }
            }
            .onAppear(perform: loadExisting)
        }
    }

    private func add(_ food: FoodItem) {
        let grams = food.unitGrams > 0 ? food.unitGrams : 100
        items.append(MealItemSnapshot.from(food: food, grams: grams, mode: pricingMode))
    }

    private func loadExisting() {
        guard !didLoad, let entry = existingEntry else {
            didLoad = true
            return
        }
        didLoad = true
        items = entry.items
        pricingMode = entry.pricingMode
        if entry.pricingMode == .takeout, let override = entry.priceOverride {
            takeoutPriceText = String(format: "%.0f", override)
        }
        note = entry.note
    }

    private func save() {
        let entry = existingEntry ?? MealEntry(date: Date(), mealType: mealType)
        if existingEntry == nil {
            context.insert(entry)
        }
        var saved = items
        for index in saved.indices {
            saved[index].pricingMode = pricingMode
            saved[index].price = pricingMode == .takeout
                ? 0
                : saved[index].pricePer100 * saved[index].grams / 100
        }
        entry.mealType = mealType
        entry.items = saved
        entry.priceOverride = pricingMode == .takeout ? Double(takeoutPriceText) : nil
        entry.note = note
        try? context.save()
        dismiss()
    }
}
