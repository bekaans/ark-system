// Bexi motoruna (hands_free.py -> ui_bridge.py) SSE ile baglanan istemci
// durumu. Mac'te varsayilan host localhost; iPhone'da Mac'in LAN IP'si
// Ayarlar'dan girilir (UserDefaults'ta saklanir).

import Foundation
import SwiftUI

enum BexiState: String {
    case sleeping, listening, thinking, speaking

    var label: String {
        switch self {
        case .sleeping: return "Uyuyor"
        case .listening: return "Dinliyor"
        case .thinking: return "Düşünüyor"
        case .speaking: return "Konuşuyor"
        }
    }

    var tint: Color {
        switch self {
        case .sleeping: return Color(red: 0.42, green: 0.47, blue: 0.55)
        case .listening: return Color(red: 0.20, green: 0.78, blue: 0.85)
        case .thinking: return Color(red: 0.95, green: 0.70, blue: 0.25)
        case .speaking: return Color(red: 0.62, green: 0.48, blue: 0.98)
        }
    }

    /// Kurenin nefes hizi (Hz) — durum ritmi kureye buradan gecer.
    var pulseHz: Double {
        switch self {
        case .sleeping: return 0.14
        case .listening: return 0.55
        case .thinking: return 0.90
        case .speaking: return 1.60
        }
    }
}

struct ChatEntry: Identifiable, Equatable {
    enum Role { case user, bexi }
    let id = UUID()
    let role: Role
    var text: String
    let ts: Date
}

@MainActor
final class AppState: ObservableObject {
    @Published var state: BexiState = .sleeping
    @Published var entries: [ChatEntry] = []
    @Published var toolActivity: String?
    @Published var connected = false
    @Published var host: String {
        didSet { UserDefaults.standard.set(host, forKey: "bexiHost") }
    }
    // Motor artik token'siz baglantiyi reddediyor (2026-07-24, guvenlik -
    // token yoksa ayni WiFi'daki herkes canli konusmayi izleyebiliyordu).
    // Mac'te token dosyadan otomatik okunur; iPhone'da Ayarlar'dan elle
    // yapistirilir (dosyaya erisimi yok, ayni host alani gibi).
    @Published var token: String {
        didSet { UserDefaults.standard.set(token, forKey: "bexiToken") }
    }

    private var streamTask: Task<Void, Never>?

    init() {
        #if os(macOS)
        let defaultHost = "localhost"
        let defaultToken = (try? String(
            contentsOf: FileManager.default.homeDirectoryForCurrentUser
                .appendingPathComponent(".config/bexi/ui_token"),
            encoding: .utf8
        ))?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        #else
        let defaultHost = ""
        let defaultToken = ""
        #endif
        host = UserDefaults.standard.string(forKey: "bexiHost") ?? defaultHost
        token = UserDefaults.standard.string(forKey: "bexiToken") ?? defaultToken
    }

    func connect() {
        streamTask?.cancel()
        guard !host.isEmpty, !token.isEmpty,
              let url = URL(string: "http://\(host):8123/events?token=\(token)")
        else { return }
        streamTask = Task { [weak self] in
            var backoff: UInt64 = 1
            while !Task.isCancelled {
                do {
                    var request = URLRequest(url: url)
                    request.timeoutInterval = 3600
                    let (bytes, response) = try await URLSession.shared.bytes(for: request)
                    guard (response as? HTTPURLResponse)?.statusCode == 200 else {
                        throw URLError(.badServerResponse)
                    }
                    await MainActor.run { self?.connected = true }
                    backoff = 1
                    for try await line in bytes.lines {
                        guard line.hasPrefix("data: ") else { continue }
                        let payload = String(line.dropFirst(6))
                        await self?.handle(payload)
                    }
                } catch {
                    // baglanti koptu / motor kapali — sessizce yeniden dene
                }
                await MainActor.run { self?.connected = false }
                try? await Task.sleep(nanoseconds: backoff * 1_000_000_000)
                backoff = min(backoff * 2, 10)
            }
        }
    }

    private func handle(_ payload: String) async {
        guard let data = payload.data(using: .utf8),
              let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let type = obj["type"] as? String
        else { return }

        switch type {
        case "hello":
            if let history = obj["history"] as? [[String: Any]] {
                entries = []
                toolActivity = nil
                for event in history { apply(event) }
            }
        default:
            apply(obj)
        }
    }

    private func apply(_ obj: [String: Any]) {
        guard let type = obj["type"] as? String else { return }
        let ts = Date(timeIntervalSince1970: obj["ts"] as? Double ?? Date().timeIntervalSince1970)

        switch type {
        case "state":
            if let raw = obj["value"] as? String, let s = BexiState(rawValue: raw) {
                state = s
                if s != .thinking { toolActivity = nil }
            }
        case "user":
            if let text = obj["text"] as? String {
                entries.append(ChatEntry(role: .user, text: text, ts: ts))
            }
        case "bexi":
            if let text = obj["text"] as? String {
                // Ard arda gelen Bexi cumleleri tek girdide toplanir —
                // motor cumle cumle yayinliyor, UI'da paragraf olur.
                if let last = entries.last, last.role == .bexi,
                   ts.timeIntervalSince(last.ts) < 20 {
                    entries[entries.count - 1].text += " " + text
                } else {
                    entries.append(ChatEntry(role: .bexi, text: text, ts: ts))
                }
            }
        case "tool":
            toolActivity = obj["text"] as? String
        default:
            break
        }

        if entries.count > 300 {
            entries.removeFirst(entries.count - 300)
        }
    }
}
