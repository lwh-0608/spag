import SwiftUI
import SwiftData

struct AvatarPageView: View {
    @Environment(\.modelContext) private var context
    @Query private var profiles: [BodyProfile]
    @EnvironmentObject private var health: HealthKitService

    @State private var params = AvatarParameters()
    @State private var previewWeight: Double = 70
    @State private var showCustomize = false
    @State private var didLoad = false

    private var profile: BodyProfile? { profiles.first }
    private var heightCm: Double { profile?.heightCm ?? 175 }
    private var bmi: Double {
        let h = max(100, heightCm) / 100
        return previewWeight / (h * h)
    }
    private var bodyLabel: String {
        switch bmi {
        case ..<18.5: return "偏瘦"
        case 18.5..<24: return "标准"
        case 24..<28: return "偏胖"
        default: return "肥胖"
        }
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 14) {
                    avatarCard
                    weightCard
                    customizeCard
                }
                .padding(.horizontal, 16)
                .padding(.bottom, 28)
            }
            .background(Theme.background)
            .navigationTitle("形象")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        showCustomize = true
                    } label: {
                        Image(systemName: "paintpalette")
                    }
                    .accessibilityLabel("捏脸")
                }
            }
            .sheet(isPresented: $showCustomize) {
                AvatarCustomizeView(params: $params, onSave: saveAvatar)
            }
            .onAppear(perform: load)
            .onReceive(NotificationCenter.default.publisher(for: .openAvatarCustomize)) { _ in
                showCustomize = true
            }
            .onChange(of: previewWeight) { _, newValue in params.weightKg = newValue }
            .onChange(of: heightCm) { _, newValue in params.heightCm = newValue }
        }
    }

    private var avatarCard: some View {
        ZStack {
            LinearGradient(colors: [Theme.accent.opacity(0.16), Theme.accent.opacity(0.03)],
                           startPoint: .top, endPoint: .bottom)
            AvatarSceneView(parameters: params)
            VStack {
                Spacer()
                HStack {
                    Text("拖动可旋转 · 双指缩放")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                    Spacer()
                    Text(String(format: "%.1f kg", previewWeight))
                        .font(.system(size: 15, weight: .semibold, design: .rounded))
                }
                .padding(.horizontal, 14)
                .padding(.bottom, 10)
            }
        }
        .frame(height: 400)
        .clipShape(RoundedRectangle(cornerRadius: Theme.cardCorner, style: .continuous))
    }

    private var weightCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .firstTextBaseline) {
                Text("体型预览")
                    .font(.headline)
                Spacer()
                Text(String(format: "BMI %.1f · %@", bmi, bodyLabel))
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            Slider(value: $previewWeight, in: 40...120, step: 0.5)
                .tint(Theme.accent)
            HStack {
                Text("预览体重 \(String(format: "%.1f", previewWeight)) kg")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                Spacer()
                Text("记录体重 \(String(format: "%.1f", profile?.weightKg ?? 70)) kg")
                    .font(.footnote)
                    .foregroundStyle(.secondary)
            }
            HStack(spacing: 10) {
                Button {
                    previewWeight = profile?.weightKg ?? 70
                } label: {
                    Label("用记录体重", systemImage: "arrow.counterclockwise")
                }
                .buttonStyle(.bordered)

                if let healthWeight = health.latestWeightKg {
                    Button {
                        previewWeight = healthWeight
                    } label: {
                        Label("用健康 App 体重", systemImage: "heart.text.square")
                    }
                    .buttonStyle(.bordered)
                }
            }
            .font(.footnote)
        }
        .cardStyle()
    }

    private var customizeCard: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("捏脸与外观")
                    .font(.headline)
                Spacer()
                Button("调整") { showCustomize = true }
                    .font(.subheadline)
            }
            Text("肤色、发型、发色、眼睛颜色、脸宽均可调整；身材随体重实时变化。")
                .font(.footnote)
                .foregroundStyle(.secondary)
        }
        .cardStyle()
    }

    private func load() {
        guard !didLoad else { return }
        didLoad = true
        let weight = profile?.weightKg ?? health.latestWeightKg ?? 70
        previewWeight = weight
        params = AvatarParameters(
            weightKg: weight,
            heightCm: profile?.heightCm ?? 175,
            skinHex: profile?.avatarSkinHex ?? "F2C9A0",
            hairStyle: profile?.avatarHairStyle ?? "short",
            hairHex: profile?.avatarHairHex ?? "1C1C1E",
            eyeHex: profile?.avatarEyeHex ?? "5B3A29",
            faceWidth: profile?.avatarFaceWidth ?? 1.0
        )
    }

    private func saveAvatar() {
        let profile: BodyProfile
        if let existing = profiles.first {
            profile = existing
        } else {
            profile = BodyProfile()
            context.insert(profile)
        }
        profile.avatarSkinHex = params.skinHex
        profile.avatarHairStyle = params.hairStyle
        profile.avatarHairHex = params.hairHex
        profile.avatarEyeHex = params.eyeHex
        profile.avatarFaceWidth = params.faceWidth
        profile.updatedAt = Date()
        try? context.save()
    }
}

struct AvatarCustomizeView: View {
    @Binding var params: AvatarParameters
    var onSave: () -> Void
    @Environment(\.dismiss) private var dismiss

    private let skinColors = ["F8D3B5", "F2C9A0", "E8B48A", "D79B6E", "B87A4B", "8D5524"]
    private let hairColors = ["1C1C1E", "2B1B12", "4A2C17", "7B4B2A", "A15C2E", "9E9E9E"]
    private let eyeColors = ["5B3A29", "1C1C1E", "3B6EA8", "4E7B5A", "A67C2E"]
    private let hairStyles: [(String, String)] = [("short", "短发"), ("long", "长发"), ("bun", "丸子头"), ("buzz", "寸头")]

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 18) {
                    AvatarSceneView(parameters: params)
                        .frame(height: 280)
                        .background(
                            LinearGradient(colors: [Theme.accent.opacity(0.14), .clear],
                                           startPoint: .top, endPoint: .bottom),
                            in: RoundedRectangle(cornerRadius: Theme.cardCorner, style: .continuous)
                        )

                    pickerSection(title: "肤色") {
                        colorRow(colors: skinColors, selection: $params.skinHex)
                    }
                    pickerSection(title: "发型") {
                        HStack(spacing: 8) {
                            ForEach(hairStyles, id: \.0) { style in
                                Button {
                                    params.hairStyle = style.0
                                } label: {
                                    Text(style.1)
                                        .font(.footnote)
                                        .padding(.horizontal, 12)
                                        .padding(.vertical, 7)
                                        .background(params.hairStyle == style.0 ? Theme.accent.opacity(0.18) : Color.primary.opacity(0.06),
                                                    in: Capsule())
                                        .foregroundStyle(params.hairStyle == style.0 ? Theme.accent : .primary)
                                }
                                .buttonStyle(.plain)
                            }
                            Spacer()
                        }
                    }
                    pickerSection(title: "发色") {
                        colorRow(colors: hairColors, selection: $params.hairHex)
                    }
                    pickerSection(title: "眼睛颜色") {
                        colorRow(colors: eyeColors, selection: $params.eyeHex)
                    }
                    pickerSection(title: "脸宽") {
                        HStack {
                            Text("窄")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                            Slider(value: $params.faceWidth, in: 0.85...1.2, step: 0.01)
                                .tint(Theme.accent)
                            Text("宽")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
                .padding(16)
            }
            .navigationTitle("捏脸")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("取消") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("保存") {
                        onSave()
                        dismiss()
                    }
                }
            }
        }
    }

    private func pickerSection<Content: View>(title: String, @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title)
                .font(.subheadline.weight(.medium))
                .foregroundStyle(.secondary)
            content()
        }
        .cardStyle()
    }

    private func colorRow(colors: [String], selection: Binding<String>) -> some View {
        HStack(spacing: 12) {
            ForEach(colors, id: \.self) { hex in
                Circle()
                    .fill(Color(uiColor: UIColor(hexString: hex)))
                    .frame(width: 32, height: 32)
                    .overlay(
                        Circle()
                            .stroke(selection.wrappedValue == hex ? Theme.accent : Color.primary.opacity(0.15),
                                    lineWidth: selection.wrappedValue == hex ? 3 : 1)
                    )
                    .onTapGesture { selection.wrappedValue = hex }
            }
            Spacer()
        }
    }
}
