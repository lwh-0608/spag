import Foundation

struct MealMetrics {
    var cost: Double
    var costPer100kcal: Double
    var costPer10gProtein: Double
    var nutritionScore: Double
    var priceScore: Double
    var valueScore: Double
}

enum CostCalculator {
    /// 参考价：6 元 / 100 kcal（约 30 元 / 500 kcal 的一餐）
    static let benchmarkCostPer100kcal: Double = 6.0

    static func metrics(for entry: MealEntry, targets: DailyTargets) -> MealMetrics {
        let kcal = entry.totalKcal
        let protein = entry.totalProtein
        let cost = entry.totalCost
        let costPer100 = kcal > 1 ? cost / kcal * 100 : 0
        let costPer10Protein = protein > 0.5 ? cost / protein * 10 : 0
        return MealMetrics(
            cost: cost,
            costPer100kcal: costPer100,
            costPer10gProtein: costPer10Protein,
            nutritionScore: nutritionScore(entry: entry, targets: targets),
            priceScore: priceScore(costPer100kcal: costPer100),
            valueScore: combine(nutrition: nutritionScore(entry: entry, targets: targets),
                                price: priceScore(costPer100kcal: costPer100))
        )
    }

    /// 营养质量分 0–100：按「每 100 kcal 提供的蛋白/纤维相对每日目标密度」打分，钠超标扣分。
    static func nutritionScore(entry: MealEntry, targets: DailyTargets) -> Double {
        let kcal = max(entry.totalKcal, 1)
        let targetKcal = max(targets.kcal, 1)
        let proteinPer100 = entry.totalProtein / kcal * 100
        let fiberPer100 = entry.totalFiber / kcal * 100
        let sodiumPer100 = entry.totalSodium / kcal * 100
        let targetProteinPer100 = targets.protein / targetKcal * 100
        let targetFiberPer100 = targets.fiber / targetKcal * 100
        let sodiumLimitPer100 = 2000.0 / targetKcal * 100

        let proteinDensity = min(1.6, proteinPer100 / max(targetProteinPer100, 0.1))
        let fiberDensity = min(1.6, fiberPer100 / max(targetFiberPer100, 0.1))
        let sodiumPenalty = min(1.0, sodiumPer100 / max(sodiumLimitPer100, 0.1))

        let score = 100 * (0.65 * min(1.0, proteinDensity / 1.2)
                           + 0.25 * min(1.0, fiberDensity / 1.2)
                           + 0.10 * (1 - sodiumPenalty))
        return min(100, max(0, score))
    }

    /// 价格分 0–100：越便宜越高，按参考价线性折减
    static func priceScore(costPer100kcal: Double) -> Double {
        guard costPer100kcal > 0.1 else { return 100 }
        let score = 100 * benchmarkCostPer100kcal / costPer100kcal
        return min(100, max(0, score))
    }

    static func combine(nutrition: Double, price: Double) -> Double {
        min(100, max(0, 0.6 * nutrition + 0.4 * price))
    }

    static func scoreLabel(_ score: Double) -> String {
        switch score {
        case 80...: return "很划算"
        case 60..<80: return "不错"
        case 40..<60: return "一般"
        default: return "偏贵"
        }
    }
}
