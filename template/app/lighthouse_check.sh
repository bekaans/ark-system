#!/usr/bin/env bash
# ARK - s2-7 kalite kapisi: Lighthouse mobil performans skoru >= 0.85 zorunlu.
#
# site.config.json'u degistirmez - hangi config public/site.config.json'da
# duruyorsa ONU derleyip test eder (bir vitrin/showcase kontrol etmek icin
# once o config'i public/site.config.json'a kopyalayin).
#
# Kullanim:
#   ./lighthouse_check.sh
#
# Cikis kodu: 0 = gecti (performans skoru >= 0.85), 1 = kaldi veya hata.

set -euo pipefail
cd "$(dirname "$0")"

PORT=4173
THRESHOLD=0.85
REPORT_PATH="/tmp/ark-lighthouse-$$.json"

echo "[ARK] Site derleniyor (npm run build)..."
npm run build --silent

echo "[ARK] vite preview baslatiliyor (port $PORT)..."
npx vite preview --port "$PORT" --strictPort > /tmp/ark-vite-preview-$$.log 2>&1 &
PREVIEW_PID=$!

cleanup() {
  kill "$PREVIEW_PID" 2>/dev/null || true
  rm -f "$REPORT_PATH"
}
trap cleanup EXIT

echo "[ARK] Sunucunun hazir olmasi bekleniyor..."
for _ in $(seq 1 30); do
  if curl -s -o /dev/null "http://localhost:$PORT"; then
    break
  fi
  sleep 0.5
done

# Sistemde kurulu Chrome kullanilir (bu ortamda Google Chrome.app mevcut) -
# ayri bir Chromium indirmeye gerek yok.
if [ -z "${CHROME_PATH:-}" ] && [ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
  export CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
fi

echo "[ARK] Lighthouse calistiriliyor (mobil, sadece performans)..."
npx lighthouse "http://localhost:$PORT" \
  --output=json \
  --output-path="$REPORT_PATH" \
  --only-categories=performance \
  --preset=perf \
  --form-factor=mobile \
  --screenEmulation.mobile=true \
  --throttling-method=simulate \
  --chrome-flags="--headless=new" \
  --quiet

# Skor okuma + esik karsilastirmasi TEK node cagrisinda yapilir (birden
# fazla node -e arasinda deger aktarmak, bu ortamda console.log ciktisina
# karisan ANSI renk kodlari yuzunden kirilgan cikti - NO_COLOR=1 + tek
# script en guvenilir yol).
if NO_COLOR=1 node -e "
  const fs = require('fs');
  const report = JSON.parse(fs.readFileSync(process.argv[1], 'utf8'));
  const score = report.categories.performance.score;
  const pct = Math.round(score * 100);
  const threshold = parseFloat(process.argv[2]);
  console.log('[ARK] Lighthouse mobil performans skoru: ' + pct + '/100 (esik: ' + Math.round(threshold * 100) + ')');
  process.exit(score >= threshold ? 0 : 1);
" "$REPORT_PATH" "$THRESHOLD"; then
  echo "[ARK] GECTI."
  exit 0
else
  echo "[ARK] KALDI - sahne kapsamini (ucgen/parcacik/doku boyutu) kucultup tekrar deneyin."
  exit 1
fi
