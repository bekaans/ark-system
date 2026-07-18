#!/bin/bash
# ARK - Bexi'nin ilk gercek arayuzu: Telegram <-> Claude Code koprusu.
#
# BU SCRIPT BAGIMSIZ CALISIR - herhangi bir Claude Code oturumunun (bu dahil)
# devam etmesine ihtiyac duymaz. Amac: kullanici Telegram'dan mesaj atsin,
# HER MESAJ ICIN TAZE bir `claude -p` cagrisi (buyuk konusma gecmisini tekrar
# okumadan, sadece README.md + yeni mesaj) calissin, cevap Telegram'a gitsin.
#
# Kullanim:
#   nohup ~/ark-system/agents/bexi-telegram/bridge.sh > ~/ark-system/agents/bexi-telegram/bridge.log 2>&1 &
#   disown

set -u

BOT_TOKEN="8958074022:AAGXVpeurvzYIHyTaAe_Fw1H_-K7kWJMcns"
CHAT_ID="7646334437"
ARK_DIR="$HOME/ark-system"
BRIDGE_DIR="$ARK_DIR/agents/bexi-telegram"
OFFSET_FILE="$BRIDGE_DIR/.offset"
PID_FILE="$BRIDGE_DIR/.pid"
PY="${LAST30DAYS_PYTHON:-python3}"

mkdir -p "$BRIDGE_DIR"
[ -f "$OFFSET_FILE" ] || echo 0 > "$OFFSET_FILE"

# Ayni script'in birden fazla kopyasi ayni offset/log dosyasini paylasarak
# calisirsa mesajlar yaris durumunda kayboluyordu (2026-07-18'de yasandi) -
# tek instance garantisi icin PID kilidi.
if [ -f "$PID_FILE" ]; then
  old_pid=$(cat "$PID_FILE")
  if [ -n "$old_pid" ] && kill -0 "$old_pid" 2>/dev/null; then
    echo "[bexi-telegram] $(date) zaten calisiyor (PID $old_pid), cikiliyor"
    exit 1
  fi
fi
echo $$ > "$PID_FILE"
trap 'rm -f "$PID_FILE"' EXIT

echo "[bexi-telegram] baslatildi, $(date), PID $$"

while true; do
  offset=$(cat "$OFFSET_FILE")
  response=$(curl -s --max-time 60 "https://api.telegram.org/bot${BOT_TOKEN}/getUpdates?timeout=50&offset=${offset}")

  # Onceki surum sadece SON mesaji aliyordu (results[-1]) - kullanici arka
  # arkaya birden fazla mesaj yazdiginda aradakiler offset atlanarak sessizce
  # kayboluyordu. Artik gelen tum mesajlar satir satir cikarilip sirayla islenir.
  parsed=$("$PY" - "$response" <<'PYEOF'
import json, sys
try:
    data = json.loads(sys.argv[1])
except Exception:
    sys.exit(0)
for upd in data.get("result", []):
    new_offset = upd["update_id"] + 1
    text = upd.get("message", {}).get("text", "")
    if not text:
        continue
    print(f"{new_offset}|||{text.replace(chr(10), ' ')}")
PYEOF
)

  if [ -z "$parsed" ]; then
    continue
  fi

  while IFS= read -r line; do
    [ -z "$line" ] && continue
    new_offset="${line%%|||*}"
    text="${line#*|||}"
    echo "$new_offset" > "$OFFSET_FILE"
    echo "[bexi-telegram] $(date) yeni mesaj: $text"

    cd "$ARK_DIR" || continue
    reply=$(claude -p "Telegram'dan Bexi'ye (sana, ARK Intelligence Labs'in asistanina) kullanicidan bir mesaj geldi: \"$text\". Once README.md'yi oku, projenin guncel durumunu anla. Mesaj bir soruya cevapsa veya bir islem talebiyse, gerekeni yap (dosya duzenle, script calistir, git commit/push - bu proje icin yerlesik kurallara uy). Cevabini KISA ve NET Turkce yaz, WhatsApp/Telegram mesaji gibi - uzun rapor degil." \
      --permission-mode auto 2>&1)

    if [ -z "$reply" ]; then
      reply="(Bexi bos bir cevap uretti - loga bak: agents/bexi-telegram/bridge.log)"
    fi

    curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
      -d "chat_id=${CHAT_ID}" \
      --data-urlencode "text=${reply}" > /dev/null

    echo "[bexi-telegram] $(date) cevap gonderildi"
  done <<< "$parsed"
done
