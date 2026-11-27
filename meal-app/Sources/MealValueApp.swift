import SwiftUI
import SwiftData

@main
struct MealValueApp: App {
    @StateObject private var health = HealthKitService()
    private let container: ModelContainer

    init() {
        do {
            container = try ModelContainer(for: FoodItem.self, MealEntry.self, BodyProfile.self, WeightLog.self)
        } catch {
            fatalError("无法初始化本地数据库：\(error)")
        }
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(health)
        }
        .modelContainer(container)
    }
}
