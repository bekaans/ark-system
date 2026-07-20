#!/bin/bash
# ARK - Tailscale saglik kontrolu / otomatik kurtarma.
#
# Bilinen sorun (tailscale/tailscale GitHub #1134, #17736, #4587): Mac uykudan
# uyaninca Tailscale menu'de "bagli" gorunse de gercekte veri akmiyor -
# macOS soketleri "dinleme" modunda tutuyor ama servis surecini
# canlandirmiyor. Tek cozum uygulamayi yeniden baslatmak. Bu script bunu
# periyodik olarak kontrol edip gerekirse otomatik yapar.
#
# Kullanim (elle test):
#   ./tailscale_watchdog.sh
# Kalici calisma icin launchd StartInterval ile (kurulum yarin Tailscale
# kurulumuyla birlikte yapilacak).

set -u
LOG_FILE="$HOME/ark-system/agents/remote-access/watchdog.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
  echo "[tailscale-watchdog] $(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

if ! command -v tailscale >/dev/null 2>&1; then
  log "tailscale CLI bulunamadi - henuz kurulmamis olabilir, atlaniyor"
  exit 0
fi

# `tailscale status` gercekten veri alisverisi yapabiliyor mu diye kontrol
# eder - sadece menu ikonuna degil, gercek baglantiya bakar.
if timeout 10 tailscale status >/dev/null 2>&1; then
  # Saglikli - sessizce cik (log'u sismesin diye basari mesaji yazmiyoruz).
  exit 0
fi

log "tailscale status basarisiz/zaman asimi - kurtarma deneniyor"

if [ -d "/Applications/Tailscale.app" ]; then
  # GUI uygulama olarak kurulmus: kapat + yeniden ac.
  killall Tailscale >/dev/null 2>&1
  sleep 2
  open -a Tailscale
  log "Tailscale.app yeniden baslatildi"
elif command -v brew >/dev/null 2>&1 && brew services list 2>/dev/null | grep -q "^tailscale"; then
  # Homebrew servisi olarak kurulmus.
  brew services restart tailscale >/dev/null 2>&1
  log "brew services ile tailscale yeniden baslatildi"
else
  log "UYARI: kurtarma yontemi bulunamadi - tailscale ne .app ne brew servisi olarak gorunuyor, elle kontrol gerekli"
fi
