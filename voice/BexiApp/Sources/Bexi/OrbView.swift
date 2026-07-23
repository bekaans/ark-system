// Bexi'nin durum kuresi — nefes alan cekirdek + halkalar. Durum rengi ve
// ritmi AppState'ten gelir; dekorasyon degil durum gostergesi (product
// register: motion conveys state).

import SwiftUI

struct OrbView: View {
    let state: BexiState
    let connected: Bool

    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        TimelineView(.animation(minimumInterval: 1.0 / 30.0, paused: reduceMotion)) { context in
            let t = context.date.timeIntervalSinceReferenceDate
            // Nefes: 0..1 arasi, durum hizinda
            let phase = reduceMotion ? 0.5 : (sin(t * 2 * .pi * state.pulseHz) + 1) / 2
            let tint = connected ? state.tint : Color(white: 0.35)

            Canvas { canvasContext, size in
                let center = CGPoint(x: size.width / 2, y: size.height / 2)
                let base = min(size.width, size.height) / 2

                // Dis hale — nefesle genisler
                let haloRadius = base * (0.72 + 0.16 * phase)
                let halo = Path(ellipseIn: CGRect(
                    x: center.x - haloRadius, y: center.y - haloRadius,
                    width: haloRadius * 2, height: haloRadius * 2))
                canvasContext.fill(halo, with: .radialGradient(
                    Gradient(colors: [tint.opacity(0.28 + 0.12 * phase), .clear]),
                    center: center, startRadius: 0, endRadius: haloRadius))

                // Ince halka — sabit, kureye cerceve
                let ringRadius = base * 0.55
                let ring = Path(ellipseIn: CGRect(
                    x: center.x - ringRadius, y: center.y - ringRadius,
                    width: ringRadius * 2, height: ringRadius * 2))
                canvasContext.stroke(ring, with: .color(tint.opacity(0.55)), lineWidth: 1.5)

                // Cekirdek — nefesle hafif buyur/kuculur
                let coreRadius = base * (0.34 + 0.05 * phase)
                let core = Path(ellipseIn: CGRect(
                    x: center.x - coreRadius, y: center.y - coreRadius,
                    width: coreRadius * 2, height: coreRadius * 2))
                canvasContext.fill(core, with: .radialGradient(
                    Gradient(colors: [tint.opacity(0.95), tint.opacity(0.35)]),
                    center: CGPoint(x: center.x - coreRadius * 0.25,
                                    y: center.y - coreRadius * 0.3),
                    startRadius: 0, endRadius: coreRadius * 1.4))
            }
        }
        .accessibilityLabel("Bexi durumu: \(connected ? state.label : "Bağlantı yok")")
    }
}
