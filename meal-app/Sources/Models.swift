import Foundation
import SwiftData

// MARK: - Enums

enum Sex: String, Codable, CaseIterable, Identifiable {
    case male, female
    var id: String { rawValue }
    var title: String { self == .male ? "男" : "女" }
}

enum Goal: String, Codable, CaseIterable, Identifiable {
    case lightLoss, maintain, gain
    var id: String { rawValue }
    var title: String {
        switch self {
        case .lightLoss: return "轻减脂"
        case .maintain: return "维持"
        case .gain: return "增肌"
        }
    }
}

enum MealType: String, Codable, CaseIterable, Identifiable {
    case breakfast, lunch, dinner, snack
    var id: String { rawValue }
    var title: String {
        switch self {
        case .breakfast: return "早餐"
        case .lunch: return "午餐"
        case .dinner: return "晚餐"
        case .snack: return "加餐"
        }
    }
    var symbol: String {
        switch self {
        case .breakfast: return "sunrise"
        case .lunch: return "sun.max"
        case .dinner: return "moon.stars"
        case .snack: return "leaf"
        }
    }
    var sortIndex: Int {
        switch self {
        case .breakfast: return 0
        case .lunch: return 1
        case .dinner: return 2
        case .snack: return 3
        }
    }
}

enum PricingMode: String, Codable, CaseIterable, Identifiable {
    case homemade, takeout
    var id: String { rawValue }
    var title: String { self == .homemade ? "自制" : "外卖" }
}

// MARK: - Food

@Model
final class FoodItem {
    @Attribute(.unique) var id: UUID
    var name: String
    var aliases: String
    var category: String
    var kcalPer100: Double
    var proteinPer100: Double
    var fatPer100: Double
    var carbPer100: Double
    var fiberPer100: Double
    var sodiumPer100: Double
    var pricePer100: Double
    var unitName: String
    var unitGrams: Double
    var isBuiltin: Bool

    init(id: UUID = UUID(), name: String, aliases: String = "", category: String,
         kcalPer100: Double, proteinPer100: Double, fatPer100: Double, carbPer100: Double,
         fiberPer100: Double, sodiumPer100: Double, pricePer100: Double,
         unitName: String = "份", unitGrams: Double = 100, isBuiltin: Bool = true) {
        self.id = id
        self.name = name
        self.aliases = aliases
        self.category = category
        self.kcalPer100 = kcalPer100
        self.proteinPer100 = proteinPer100
        self.fatPer100 = fatPer100
        self.carbPer100 = carbPer100
        self.fiberPer100 = fiberPer100
        self.sodiumPer100 = sodiumPer100
        self.pricePer100 = pricePer100
        self.unitName = unitName
        self.unitGrams = unitGrams
        self.isBuiltin = isBuiltin
    }
}

// MARK: - Meal snapshot

struct MealItemSnapshot: Codable, Identifiable, Hashable {
    var id: UUID = UUID()
    var foodName: String
    var grams: Double
    var unitLabel: String
    var pricingModeRaw: String
    var pricePer100: Double
    var price: Double
    var kcal: Double
    var protein: Double
    var fat: Double
    var carb: Double
    var fiber: Double
    var sodium: Double

    var pricingMode: PricingMode {
        get { PricingMode(rawValue: pricingModeRaw) ?? .homemade }
        set { pricingModeRaw = newValue.rawValue }
    }

    static func from(food: FoodItem, grams: Double, mode: PricingMode) -> MealItemSnapshot {
        let ratio = grams / 100.0
        return MealItemSnapshot(
            foodName: food.name,
            grams: grams,
            unitLabel: "\(Int(grams))g",
            pricingModeRaw: mode.rawValue,
            pricePer100: food.pricePer100,
            price: mode == .takeout ? 0 : food.pricePer100 * ratio,
            kcal: food.kcalPer100 * ratio,
            protein: food.proteinPer100 * ratio,
            fat: food.fatPer100 * ratio,
            carb: food.carbPer100 * ratio,
            fiber: food.fiberPer100 * ratio,
            sodium: food.sodiumPer100 * ratio
        )
    }

    func scaled(toGrams newGrams: Double) -> MealItemSnapshot {
        let ratio = grams > 0 ? newGrams / grams : 0
        var copy = self
        copy.grams = newGrams
        copy.unitLabel = "\(Int(newGrams))g"
        copy.price *= ratio
        copy.kcal *= ratio
        copy.protein *= ratio
        copy.fat *= ratio
        copy.carb *= ratio
        copy.fiber *= ratio
        copy.sodium *= ratio
        return copy
    }
}

// MARK: - Meal entry

@Model
final class MealEntry {
    @Attribute(.unique) var id: UUID
    var date: Date
    var mealTypeRaw: String
    var itemsData: Data
    var priceOverride: Double?
    var note: String
    var createdAt: Date

    init(id: UUID = UUID(), date: Date = Date(), mealType: MealType, items: [MealItemSnapshot] = [],
         priceOverride: Double? = nil, note: String = "") {
        self.id = id
        self.date = date
        self.mealTypeRaw = mealType.rawValue
        self.itemsData = (try? JSONEncoder().encode(items)) ?? Data()
        self.priceOverride = priceOverride
        self.note = note
        self.createdAt = Date()
    }

    var mealType: MealType {
        get { MealType(rawValue: mealTypeRaw) ?? .lunch }
        set { mealTypeRaw = newValue.rawValue }
    }

    var items: [MealItemSnapshot] {
        get { (try? JSONDecoder().decode([MealItemSnapshot].self, from: itemsData)) ?? [] }
        set { itemsData = (try? JSONEncoder().encode(newValue)) ?? Data() }
    }

    var totalKcal: Double { items.reduce(0) { $0 + $1.kcal } }
    var totalProtein: Double { items.reduce(0) { $0 + $1.protein } }
    var totalFat: Double { items.reduce(0) { $0 + $1.fat } }
    var totalCarb: Double { items.reduce(0) { $0 + $1.carb } }
    var totalFiber: Double { items.reduce(0) { $0 + $1.fiber } }
    var totalSodium: Double { items.reduce(0) { $0 + $1.sodium } }
    var itemsCost: Double { items.reduce(0) { $0 + $1.price } }
    var totalCost: Double { priceOverride ?? itemsCost }
    var pricingMode: PricingMode {
        items.first?.pricingMode ?? .homemade
    }
}

// MARK: - Body profile

@Model
final class BodyProfile {
    var sexRaw: String
    var birthYear: Int
    var heightCm: Double
    var weightKg: Double
    var targetWeightKg: Double
    var goalRaw: String
    var budgetPerDay: Double
    var updatedAt: Date

    init(sex: Sex = .male, birthYear: Int = 1995, heightCm: Double = 175,
         weightKg: Double = 70, targetWeightKg: Double = 65,
         goal: Goal = .lightLoss, budgetPerDay: Double = 60) {
        self.sexRaw = sex.rawValue
        self.birthYear = birthYear
        self.heightCm = heightCm
        self.weightKg = weightKg
        self.targetWeightKg = targetWeightKg
        self.goalRaw = goal.rawValue
        self.budgetPerDay = budgetPerDay
        self.updatedAt = Date()
    }

    var sex: Sex {
        get { Sex(rawValue: sexRaw) ?? .male }
        set { sexRaw = newValue.rawValue }
    }
    var goal: Goal {
        get { Goal(rawValue: goalRaw) ?? .lightLoss }
        set { goalRaw = newValue.rawValue }
    }
    var age: Int {
        max(14, Calendar.current.component(.year, from: Date()) - birthYear)
    }
}

// MARK: - Weight log

@Model
final class WeightLog {
    @Attribute(.unique) var id: UUID
    var date: Date
    var weightKg: Double

    init(id: UUID = UUID(), date: Date = Date(), weightKg: Double) {
        self.id = id
        self.date = date
        self.weightKg = weightKg
    }
}
