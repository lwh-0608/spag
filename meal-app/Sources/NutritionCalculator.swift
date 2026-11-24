import Foundation

struct DailyTargets {
    var kcal: Double
    var protein: Double
    var fat: Double
    var carb: Double
    var fiber: Double
    var bmr: Double
    var tdee: Double
    var deficit: Double
}

enum NutritionCalculator {
    /// Mifflin-St Jeor 基础代谢
    static func bmr(sex: Sex, weightKg: Double, heightCm: Double, age: Int) -> Double {
        let base = 10 * weightKg + 6.25 * heightCm - 5 * Double(age)
        return base + (sex == .male ? 5 : -161)
    }

    /// 推荐的目标计算：BMR + 健康 App 活动消耗 + 食物热效应（10% 摄入）
    static func tdee(bmr: Double, activeKcal: Double, intakeKcal: Double) -> Double {
        bmr + activeKcal + 0.10 * intakeKcal
    }

    static func targets(profile: BodyProfile?, activeKcal: Double, intakeKcal: Double) -> DailyTargets {
        guard let profile else {
            return DailyTargets(kcal: 1800, protein: 90, fat: 60, carb: 220, fiber: 28,
                                bmr: 1650, tdee: 2200, deficit: 300)
        }
        let bmrValue = bmr(sex: profile.sex, weightKg: profile.weightKg,
                           heightCm: profile.heightCm, age: profile.age)
        let tdeeValue = tdee(bmr: bmrValue, activeKcal: max(0, activeKcal), intakeKcal: max(0, intakeKcal))

        let deficit: Double
        switch profile.goal {
        case .lightLoss: deficit = 350
        case .maintain: deficit = 0
        case .gain: deficit = -250
        }
        let kcal = max(1200, tdeeValue - deficit)

        let proteinPerKg: Double
        switch profile.goal {
        case .lightLoss: proteinPerKg = 1.8
        case .maintain: proteinPerKg = 1.6
        case .gain: proteinPerKg = 2.0
        }
        let protein = profile.weightKg * proteinPerKg
        let fat = profile.weightKg * 0.9
        let carb = max(0, (kcal - protein * 4 - fat * 9) / 4)

        return DailyTargets(kcal: kcal, protein: protein, fat: fat, carb: carb,
                            fiber: 28, bmr: bmrValue, tdee: tdeeValue, deficit: deficit)
    }

    static func remainingKcal(targets: DailyTargets, consumed: Double, activeKcal: Double,
                             addBackRatio: Double = 0.5) -> Double {
        let addBack = max(0, activeKcal) * addBackRatio
        return max(0, targets.kcal + addBack - consumed)
    }
}
