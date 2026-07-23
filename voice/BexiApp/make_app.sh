#!/usr/bin/env bash
# Bexi.app uretimi — swift build ciktisini gercek bir Mac uygulama
# bundle'ina cevirir (dock ikonu, cift-tiklanabilir, Applications'a
# tasinabilir). Tam Xcode GEREKMEZ, CommandLineTools yeterli.
#
# Kullanim: ./make_app.sh
# Cikti:    voice/BexiApp/Bexi.app

set -euo pipefail
cd "$(dirname "$0")"

echo "[Bexi] Derleniyor (release)..."
swift build -c release --quiet

APP="Bexi.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS"

cp .build/release/Bexi "$APP/Contents/MacOS/Bexi"

cat > "$APP/Contents/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Bexi</string>
    <key>CFBundleIdentifier</key>
    <string>com.arkintelligencelabs.bexi</string>
    <key>CFBundleName</key>
    <string>Bexi</string>
    <key>CFBundleDisplayName</key>
    <string>Bexi</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>14.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSAppTransportSecurity</key>
    <dict>
        <!-- Motor http://localhost:8123 uzerinden konusuyor (yerel ag,
             TLS yok) — ATS'in yerel ag istisnasi acik olmali. -->
        <key>NSAllowsLocalNetworking</key>
        <true/>
    </dict>
</dict>
</plist>
PLIST

# Ad-hoc imza — kendi Mac'inde calismasi icin yeterli (dagitim degil).
codesign --force --sign - "$APP" 2>/dev/null || true

echo "[Bexi] Hazir: $(pwd)/$APP"
echo "[Bexi] Calistir: open $(pwd)/$APP"
