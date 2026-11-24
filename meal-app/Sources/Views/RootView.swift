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
            DemoData.seedIfNeeded(context: context)
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
}

struct MealSheetTarget: Identifiable {
    let id = UUID()
    let mealType: MealType
    let entry: MealEntry?
}
