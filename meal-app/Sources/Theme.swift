import SwiftUI

enum Theme {
    static let cardCorner: CGFloat = 18
    static let card = Color(.secondarySystemGroupedBackground)
    static let background = Color(.systemGroupedBackground)
    static let accent = Color.accentColor
}

extension View {
    func cardStyle() -> some View {
        self
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Theme.card, in: RoundedRectangle(cornerRadius: Theme.cardCorner, style: .continuous))
    }
}

struct ScoreBadge: View {
    let score: Double
    var body: some View {
        let color: Color = score >= 70 ? .green : (score >= 50 ? .orange : .red)
        HStack(spacing: 3) {
            Image(systemName: "sparkles")
                .font(.system(size: 10, weight: .semibold))
            Text("\(Int(score))")
                .font(.system(size: 12, weight: .semibold, design: .rounded))
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
        .background(color.opacity(0.15), in: Capsule())
        .foregroundStyle(color)
    }
}

struct MetricColumn: View {
    let title: String
    let value: String
    var tint: Color = .primary
    var body: some View {
        VStack(spacing: 2) {
            Text(title)
                .font(.caption2)
                .foregroundStyle(.secondary)
            Text(value)
                .font(.system(size: 16, weight: .semibold, design: .rounded))
                .foregroundStyle(tint)
        }
        .frame(maxWidth: .infinity)
    }
}
