// Bexi ana ekrani: ustte durum, ortada kure, altta konusma akisi.
// Tek kolon — ayni kompozisyon Mac penceresi ve iPhone'da calisir.

import SwiftUI

struct ContentView: View {
    @EnvironmentObject var app: AppState
    @State private var showSettings = false

    var body: some View {
        VStack(spacing: 0) {
            header
            OrbView(state: app.state, connected: app.connected)
                .frame(height: 190)
                .padding(.vertical, 8)
            statusLine
            Divider().overlay(Color.white.opacity(0.08)).padding(.top, 12)
            conversation
            toolBar
        }
        .background(Color(red: 0.055, green: 0.06, blue: 0.075))
        .preferredColorScheme(.dark)
        .sheet(isPresented: $showSettings) { settings }
        .onAppear { app.connect() }
    }

    private var header: some View {
        HStack {
            Text("BEXİ")
                .font(.system(size: 13, weight: .semibold))
                .kerning(3)
                .foregroundStyle(.white.opacity(0.85))
            Spacer()
            Button {
                showSettings = true
            } label: {
                Image(systemName: "gearshape")
                    .foregroundStyle(.white.opacity(0.55))
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Ayarlar")
        }
        .padding(.horizontal, 20)
        .padding(.top, 18)
    }

    private var statusLine: some View {
        HStack(spacing: 8) {
            Circle()
                .fill(app.connected ? app.state.tint : .red.opacity(0.8))
                .frame(width: 7, height: 7)
            Text(app.connected ? app.state.label : "Motora bağlanılamadı")
                .font(.system(size: 15, weight: .medium))
                .foregroundStyle(.white.opacity(0.92))
        }
        .animation(.easeOut(duration: 0.2), value: app.state)
        .animation(.easeOut(duration: 0.2), value: app.connected)
    }

    private var conversation: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 14) {
                    if app.entries.isEmpty {
                        emptyState
                    }
                    ForEach(app.entries) { entry in
                        VStack(alignment: .leading, spacing: 3) {
                            Text(entry.role == .user ? "SEN" : "BEXİ")
                                .font(.system(size: 10, weight: .semibold))
                                .kerning(1.2)
                                .foregroundStyle(entry.role == .user
                                    ? Color.white.opacity(0.45)
                                    : app.state.tint.opacity(0.9))
                            Text(entry.text)
                                .font(.system(size: 14))
                                .foregroundStyle(.white.opacity(0.92))
                                .lineSpacing(3)
                                .textSelection(.enabled)
                        }
                        .id(entry.id)
                        .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 16)
            }
            .onChange(of: app.entries) {
                if let last = app.entries.last {
                    withAnimation(.easeOut(duration: 0.2)) {
                        proxy.scrollTo(last.id, anchor: .bottom)
                    }
                }
            }
        }
    }

    private var emptyState: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Henüz konuşma yok")
                .font(.system(size: 14, weight: .medium))
                .foregroundStyle(.white.opacity(0.7))
            Text(app.connected
                 ? "Mikrofona \"Bexi uyan\" de — konuşma burada akacak"
                 : "Mac'te motoru başlat: ./voice/venv/bin/python voice/hands_free.py")
                .font(.system(size: 13))
                .foregroundStyle(.white.opacity(0.45))
        }
        .padding(.top, 8)
    }

    @ViewBuilder
    private var toolBar: some View {
        if let tool = app.toolActivity {
            HStack(spacing: 8) {
                ProgressView().controlSize(.small).tint(.white.opacity(0.5))
                Text(tool)
                    .font(.system(size: 12, design: .monospaced))
                    .foregroundStyle(.white.opacity(0.6))
                Spacer()
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 10)
            .background(Color.white.opacity(0.04))
            .transition(.opacity)
        }
    }

    private var settings: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Motor adresi")
                .font(.system(size: 13, weight: .semibold))
            Text("Mac'te \"localhost\". iPhone'dan bağlanırken Mac'in yerel ağ IP'si (motor terminalde yazdırıyor).")
                .font(.system(size: 12))
                .foregroundStyle(.secondary)
            TextField("ör. 192.168.1.36", text: $app.host)
                .textFieldStyle(.roundedBorder)
                .autocorrectionDisabled()
            Text("Token")
                .font(.system(size: 13, weight: .semibold))
            Text("Mac'te otomatik doldu. iPhone'da Mac'teki ~/.config/bexi/ui_token dosyasının içeriğini yapıştır.")
                .font(.system(size: 12))
                .foregroundStyle(.secondary)
            TextField("token", text: $app.token)
                .textFieldStyle(.roundedBorder)
                .autocorrectionDisabled()
            HStack {
                Spacer()
                Button("Bağlan") {
                    app.connect()
                    showSettings = false
                }
                .keyboardShortcut(.defaultAction)
            }
        }
        .padding(24)
        .frame(minWidth: 320)
    }
}
