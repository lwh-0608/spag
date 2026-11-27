import Foundation
import HealthKit

@MainActor
final class HealthKitService: ObservableObject {
    @Published var isAuthorized = false
    @Published var todayActiveEnergy: Double?
    @Published var todayBasalEnergy: Double?
    @Published var latestWeightKg: Double?
    @Published var statusText = "未连接"
    @Published var isDemo = false

    private let store = HKHealthStore()

    private var readTypes: Set<HKObjectType> {
        var types: Set<HKObjectType> = [
            HKQuantityType(.activeEnergyBurned),
            HKQuantityType(.basalEnergyBurned),
            HKQuantityType(.bodyMass)
        ]
        types.insert(HKObjectType.workoutType())
        return types
    }

    func enableDemo() {
        isDemo = true
        isAuthorized = true
        todayActiveEnergy = 320
        todayBasalEnergy = 1450
        latestWeightKg = 68.0
        statusText = "演示数据（未连接健康 App）"
    }

    func requestAuthorization() async {
        guard HKHealthStore.isHealthDataAvailable() else {
            statusText = "此设备不支持 HealthKit"
            return
        }
        do {
            try await store.requestAuthorization(toShare: [], read: readTypes)
            isAuthorized = true
            statusText = "已连接健康 App"
            await refresh()
        } catch {
            statusText = "授权失败：\(error.localizedDescription)"
        }
    }

    func refresh() async {
        guard HKHealthStore.isHealthDataAvailable(), !isDemo else { return }
        let active = await sumToday(.activeEnergyBurned)
        let basal = await sumToday(.basalEnergyBurned)
        let weight = await latestBodyMass()
        todayActiveEnergy = active
        todayBasalEnergy = basal
        if let weight { latestWeightKg = weight }
        if let active, active > 0 {
            statusText = "今日活动消耗 \(Int(active)) kcal"
        } else if active != nil {
            statusText = "今日暂无活动消耗数据"
        } else {
            statusText = "未读取到今日活动消耗"
        }
        isAuthorized = true
    }

    private func sumToday(_ identifier: HKQuantityTypeIdentifier) async -> Double? {
        let type = HKQuantityType(identifier)
        let predicate = HKQuery.predicateForSamples(
            withStart: Calendar.current.startOfDay(for: Date()),
            end: Date(),
            options: .strictStartDate
        )
        return await withCheckedContinuation { continuation in
            let query = HKStatisticsQuery(quantityType: type, quantitySamplePredicate: predicate,
                                          options: .cumulativeSum) { _, statistics, _ in
                continuation.resume(returning: statistics?.sumQuantity()?.doubleValue(for: .kilocalorie()))
            }
            store.execute(query)
        }
    }

    private func latestBodyMass() async -> Double? {
        let type = HKQuantityType(.bodyMass)
        return await withCheckedContinuation { continuation in
            let query = HKSampleQuery(
                sampleType: type,
                predicate: nil,
                limit: 1,
                sortDescriptors: [NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)]
            ) { _, samples, _ in
                let value = (samples as? [HKQuantitySample])?.first?
                    .quantity.doubleValue(for: .gramUnit(with: .kilo))
                continuation.resume(returning: value)
            }
            store.execute(query)
        }
    }
}
