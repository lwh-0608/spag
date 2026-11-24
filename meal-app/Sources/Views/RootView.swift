import SwiftUI
import SwiftData
import UIKit

struct RootView: View {
    @Environment(\.modelContext) private var context
    @EnvironmentObject private var health: HealthKitService
    @State private var selection = 0

    var body: some View {
        TabView(selection: $selection) {
            TodayView()
                .tabItem { Label("今日", systemImage: "sun.max.fill") }
                .tag(0)
            RecordView()
                .tabItem { Label("记录", systemImage: "list.bullet.rectangle.portrait") }
                .tag(1)
            ReportView()
                .tabItem { Label("报告", systemImage: "chart.bar.xaxis") }
                .tag(2)
            ProfileView()
                .tabItem { Label("我的", systemImage: "person.crop.circle") }
                .tag(3)
        }
        .tint(Theme.accent)
        .task {
            if DemoMode.isOn {
                UIApplication.shared.isIdleTimerDisabled = true
            }
            FoodSeeder.seedIfNeeded(context: context)
            if DemoMode.isOn {
                DemoData.seedIfNeeded(context: context)
            } else {
                purgeDemoData()
            }
            if DemoMode.isOn {
                health.enableDemo()
            } else {
                await health.requestAuthorization()
                await health.refresh()
            }
        }
        .onOpenURL { url in
            guard url.host == "tab" else { return }
            switch url.path {
            case "/today": selection = 0
            case "/record": selection = 1
            case "/report": selection = 2
            case "/profile": selection = 3
            default: break
            }
        }
    }

    /// 正常启动时清除历史演示数据，避免混入真实记录
    private func purgeDemoData() {
        let demoEntries = (try? context.fetch(FetchDescriptor<MealEntry>(predicate: #Predicate { $0.isDemo }))) ?? []
        for entry in demoEntries { context.delete(entry) }
        let demoWeights = (try? context.fetch(FetchDescriptor<WeightLog>(predicate: #Predicate { $0.isDemo }))) ?? []
        for log in demoWeights { context.delete(log) }
        let demoProfiles = (try? context.fetch(FetchDescriptor<BodyProfile>(predicate: #Predicate { $0.isDemo }))) ?? []
        for profile in demoProfiles { context.delete(profile) }
        if !demoEntries.isEmpty || !demoWeights.isEmpty || !demoProfiles.isEmpty {
            try? context.save()
        }
    }
}

struct MealSheetTarget: Identifiable {
    let id = UUID()
    let mealType: MealType
    let entry: MealEntry?
}
