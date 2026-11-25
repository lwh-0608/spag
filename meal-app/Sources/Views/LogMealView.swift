import SwiftUI
import SwiftData

struct LogMealView: View {
    @Environment(\.modelContext) private var context
    @Environment(\.dismiss) private var dismiss
    @Query(sort: \FoodItem.name) private var foods: [FoodItem]
    @Query private var profiles: [BodyProfile]

    let mealType: MealType
    let existingEntry: MealEntry?
    var previewItems: Bool = false

    @State private var items: [MealItemSnapshot] = []
    @State private var searchText = ""
    @State private var pricingMode: PricingMode = .homemade
    @State private var takeoutPriceText = ""
    @State private var note = ""
    @State private var didLoad = false
    @State private var showCustomFood = false
    @FocusState private var gramsFocused: UUID?

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

                Section {
                    if items.isEmpty {
                        Text("还没有添加食物，从下方选择或自定义")
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                    }
                    ForEach($items) { $item in
                        VStack(alignment: .leading, spacing: 7) {
                            HStack(spacing: 8) {
                                Text(item.foodName)
                                    .font(.subheadline)
                                Spacer()
                                Button {
                                    items.removeAll { $0.id == item.id }
                                } label: {
                                    Image(systemName: "minus.circle.fill")
                                        .foregroundStyle(.red)
                                }
                                .buttonStyle(.plain)
                            }
                            HStack(spacing: 6) {
                                TextField("克数", value: Binding(
                                    get: { item.grams },
                                    set: { newValue in
                                        item = item.scaled(toGrams: max(1, min(3000, newValue)))
                                    }
                                ), format: .number)
                                .keyboardType(.numberPad)
                                .multilineTextAlignment(.trailing)
                                .textFieldStyle(.roundedBorder)
                                .frame(width: 72)
                                .focused($gramsFocused, equals: item.id)
                                Text("g")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                Button("−10") {
                                    item = item.scaled(toGrams: max(1, item.grams - 10))
                                }
                                .buttonStyle(.bordered)
                                .controlSize(.mini)
                                Button("+10") {
                                    item = item.scaled(toGrams: min(3000, item.grams + 10))
                                }
                                .buttonStyle(.bordered)
                                .controlSize(.mini)
                                if let unit = item.unitGrams, unit > 0, abs(unit - item.grams) > 0.5 {
                                    Button("1份\(Int(unit))g") {
                                        item = item.scaled(toGrams: unit)
                                    }
                                    .buttonStyle(.bordered)
                                    .controlSize(.mini)
                                }
                                Spacer()
                                Text("\(Int(item.kcal)) kcal · 蛋白 \(String(format: "%.1f", item.protein))g")
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        .padding(.vertical, 2)
                    }
                } header: {
                    Text("已选食物（克数可直接改）")
                }

                Section {
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
                } header: {
                    HStack {
                        Text("食物库（\(foods.count) 种）")
                        Spacer()
                        Button {
                            showCustomFood = true
                        } label: {
                            Label("自定义", systemImage: "plus.circle")
                                .font(.footnote)
                        }
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
                ToolbarItemGroup(placement: .keyboard) {
                    Spacer()
                    Button("完成") { gramsFocused = nil }
                }
            }
            .scrollDismissesKeyboard(.interactively)
            .sheet(isPresented: $showCustomFood) {
                CustomFoodView { food in
                    add(food)
                }
            }
            .onAppear(perform: loadExisting)
            .onReceive(NotificationCenter.default.publisher(for: .openCustomFood)) { _ in
                showCustomFood = true
            }
        }
    }

    private func add(_ food: FoodItem) {
        let grams = food.unitGrams > 0 ? food.unitGrams : 100
        items.append(MealItemSnapshot.from(food: food, grams: grams, mode: pricingMode))
    }

    private func loadExisting() {
        if previewItems && DemoMode.isOn && items.isEmpty {
            for food in foods.prefix(2) {
                items.append(MealItemSnapshot.from(food: food,
                                                   grams: food.unitGrams > 0 ? food.unitGrams : 100,
                                                   mode: pricingMode))
            }
        }
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


struct CustomFoodView: View {
    @Environment(\.modelContext) private var context
    @Environment(\.dismiss) private var dismiss
    var onAdd: (FoodItem) -> Void

    @State private var name = ""
    @State private var category = "其他"
    @State private var kcal = ""
    @State private var protein = ""
    @State private var fat = ""
    @State private var carb = ""
    @State private var fiber = ""
    @State private var sodium = ""
    @State private var price = ""
    @State private var unitGrams = "100"
    @FocusState private var focused: Bool

    private let categories = ["主食", "蛋白质", "蔬菜", "水果", "乳品", "坚果", "饮品", "外卖", "零食", "调味", "其他"]

    var body: some View {
        NavigationStack {
            Form {
                Section("名称") {
                    TextField("例如：妈妈做的红烧肉", text: $name)
                        .focused($focused)
                }
                Section("分类") {
                    Picker("分类", selection: $category) {
                        ForEach(categories, id: \.self) { Text($0).tag($0) }
                    }
                }
                Section("每 100g 营养（按包装或食物库查询填写）") {
                    numberField("热量 kcal", text: $kcal)
                    numberField("蛋白质 g", text: $protein)
                    numberField("脂肪 g", text: $fat)
                    numberField("碳水 g", text: $carb)
                    numberField("膳食纤维 g", text: $fiber)
                    numberField("钠 mg", text: $sodium)
                }
                Section("价格与份量") {
                    numberField("单价 元/100g", text: $price)
                    numberField("常用一份的克数", text: $unitGrams)
                }
                Section {
                    Text("自定义食物会保存到食物库，下次可直接搜索。")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("自定义食物")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("取消") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("保存并添加") { save() }
                        .disabled(name.trimmingCharacters(in: .whitespaces).isEmpty)
                }
                ToolbarItemGroup(placement: .keyboard) {
                    Spacer()
                    Button("完成") { focused = false }
                }
            }
            .scrollDismissesKeyboard(.interactively)
        }
    }

    private func numberField(_ title: String, text: Binding<String>) -> some View {
        HStack {
            Text(title)
            Spacer()
            TextField("0", text: text)
                .keyboardType(.decimalPad)
                .multilineTextAlignment(.trailing)
                .focused($focused)
                .frame(width: 90)
        }
    }

    private func save() {
        let trimmed = name.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty else { return }
        let food = FoodItem(
            name: trimmed,
            category: category,
            kcalPer100: Double(kcal) ?? 0,
            proteinPer100: Double(protein) ?? 0,
            fatPer100: Double(fat) ?? 0,
            carbPer100: Double(carb) ?? 0,
            fiberPer100: Double(fiber) ?? 0,
            sodiumPer100: Double(sodium) ?? 0,
            pricePer100: Double(price) ?? 0,
            unitName: "份",
            unitGrams: Double(unitGrams) ?? 100,
            isBuiltin: false
        )
        context.insert(food)
        try? context.save()
        onAdd(food)
        dismiss()
    }
}
