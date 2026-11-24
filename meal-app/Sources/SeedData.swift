import Foundation
import SwiftData

enum DemoMode {
    static var isOn: Bool {
        ProcessInfo.processInfo.arguments.contains("-demoMode")
            || UserDefaults.standard.bool(forKey: "demoMode")
    }
}

// MARK: - 内置食物库

struct FoodSeed: Codable {
    var name: String
    var category: String
    var kcal: Double
    var protein: Double
    var fat: Double
    var carb: Double
    var fiber: Double
    var sodium: Double
    var price: Double
    var unitName: String
    var unitGrams: Double
}

enum FoodSeeder {
    static func seedIfNeeded(context: ModelContext) {
        let descriptor = FetchDescriptor<FoodItem>()
        let count = (try? context.fetchCount(descriptor)) ?? 0
        guard count == 0 else { return }
        guard let url = Bundle.main.url(forResource: "foods", withExtension: "json"),
              let data = try? Data(contentsOf: url) else { return }
        guard let seeds = try? JSONDecoder().decode([FoodSeed].self, from: data) else { return }
        for seed in seeds {
            context.insert(FoodItem(
                name: seed.name,
                category: seed.category,
                kcalPer100: seed.kcal,
                proteinPer100: seed.protein,
                fatPer100: seed.fat,
                carbPer100: seed.carb,
                fiberPer100: seed.fiber,
                sodiumPer100: seed.sodium,
                pricePer100: seed.price,
                unitName: seed.unitName,
                unitGrams: seed.unitGrams
            ))
        }
        try? context.save()
    }
}

// MARK: - 演示数据（用于截图/试用，不含个人真实健康数据）

enum DemoData {
    static func seedIfNeeded(context: ModelContext) {
        guard DemoMode.isOn else { return }
        let profiles = (try? context.fetch(FetchDescriptor<BodyProfile>())) ?? []
        if profiles.isEmpty {
            context.insert(BodyProfile(sex: .male, birthYear: 1995, heightCm: 175,
                                       weightKg: 70, targetWeightKg: 65,
                                       goal: .lightLoss, budgetPerDay: 60))
        }
        let entries = (try? context.fetch(FetchDescriptor<MealEntry>())) ?? []
        if entries.isEmpty {
            for dayOffset in 0..<7 {
                let day = Calendar.current.date(byAdding: .day, value: -dayOffset, to: Date()) ?? Date()
                insertDay(offset: dayOffset, date: day, context: context)
            }
            try? context.save()
        }
        let weights = (try? context.fetch(FetchDescriptor<WeightLog>())) ?? []
        if weights.isEmpty {
            for i in 0..<14 {
                let day = Calendar.current.date(byAdding: .day, value: -i, to: Date()) ?? Date()
                let value = 70.0 - Double(i) * 0.05 - (i % 3 == 0 ? 0.1 : 0)
                context.insert(WeightLog(date: day, weightKg: value))
            }
            try? context.save()
        }
    }

    private static func insertDay(offset: Int, date: Date, context: ModelContext) {
        let breakfast = MealEntry(date: date, mealType: .breakfast, items: [
            item("全麦面包", grams: 80, k: 246, p: 9.9, f: 3.3, c: 41, fib: 6, na: 400, price: 1.5, mode: .homemade),
            item("鸡蛋（水煮）", grams: 100, k: 144, p: 13.3, f: 8.8, c: 2.8, fib: 0, na: 131, price: 1.2, mode: .homemade),
            item("牛奶", grams: 250, k: 54, p: 3.0, f: 3.2, c: 3.4, fib: 0, na: 37, price: 0.5, mode: .homemade)
        ], priceOverride: offset % 2 == 0 ? nil : 9.0)
        context.insert(breakfast)

        let lunchItems: [MealItemSnapshot] = offset % 2 == 0
            ? [
                item("米饭（熟）", grams: 250, k: 116, p: 2.6, f: 0.3, c: 25.9, fib: 0.3, na: 1, price: 0.3, mode: .homemade),
                item("鸡胸肉", grams: 150, k: 133, p: 24, f: 3.6, c: 0.5, fib: 0, na: 60, price: 2.2, mode: .homemade),
                item("西兰花", grams: 150, k: 34, p: 2.8, f: 0.4, c: 6.6, fib: 2.6, na: 18, price: 1.0, mode: .homemade)
            ]
            : [
                item("黄焖鸡米饭（外卖）", grams: 600, k: 155, p: 9.0, f: 6.5, c: 16.5, fib: 1.0, na: 600, price: 3.4, mode: .takeout)
            ]
        let lunch = MealEntry(date: date, mealType: .lunch, items: lunchItems,
                              priceOverride: offset % 2 == 0 ? nil : 24.0)
        context.insert(lunch)

        let dinner = MealEntry(date: date, mealType: .dinner, items: [
            item("米饭（熟）", grams: 150, k: 116, p: 2.6, f: 0.3, c: 25.9, fib: 0.3, na: 1, price: 0.3, mode: .homemade),
            item("番茄炒蛋", grams: 250, k: 90, p: 5.0, f: 6.0, c: 4.5, fib: 0.8, na: 220, price: 2.0, mode: .takeout),
            item("清炒时蔬", grams: 200, k: 45, p: 2.0, f: 2.5, c: 4.0, fib: 1.8, na: 180, price: 1.2, mode: .takeout)
        ], priceOverride: 18.0)
        context.insert(dinner)

        if offset % 2 == 0 {
            let snack = MealEntry(date: date, mealType: .snack, items: [
                item("希腊酸奶", grams: 150, k: 59, p: 10, f: 0.4, c: 3.6, fib: 0, na: 36, price: 3.0, mode: .homemade),
                item("蓝莓", grams: 100, k: 57, p: 0.7, f: 0.3, c: 14.5, fib: 2.4, na: 1, price: 3.0, mode: .homemade)
            ], priceOverride: 12.0)
            context.insert(snack)
        }
    }

    private static func item(_ name: String, grams: Double, k: Double, p: Double, f: Double,
                             c: Double, fib: Double, na: Double, price: Double,
                             mode: PricingMode) -> MealItemSnapshot {
        let ratio = grams / 100.0
        return MealItemSnapshot(foodName: name, grams: grams, unitLabel: "\(Int(grams))g",
                                pricingModeRaw: mode.rawValue,
                                pricePer100: price,
                                price: mode == .takeout ? 0 : price * ratio,
                                kcal: k * ratio, protein: p * ratio, fat: f * ratio,
                                carb: c * ratio, fiber: fib * ratio, sodium: na * ratio)
    }
}
