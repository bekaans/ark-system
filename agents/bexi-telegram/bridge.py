#!/usr/bin/env python3
"""ARK - Bexi'nin Telegram koprusu (kisa-sureli hafizali).

BAGIMSIZ CALISIR - hicbir Claude Code oturumunun (ana pipeline dahil) devam
etmesine ihtiyac duymaz. Her Telegram mesaji, bu konusmanin BUYUK gecmisini
DEGIL, sadece README.md + son ~10 Telegram mesajlik kisa ozeti okuyan TAZE
bir `claude -p` cagrisi tetikler - bu yuzden ucuz kalir ama yine de kisa
vadeli baglami (orn. "evet" nin neye cevap oldugunu) korur.

Kullanim:
  nohup python3 ~/ark-system/agents/bexi-telegram/bridge.py \
    > ~/ark-system/agents/bexi-telegram/bridge.log 2>&1 &
  disown
"""

import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ARK_DIR = Path(__file__).resolve().parent.parent.parent
BRIDGE_DIR = ARK_DIR / "agents" / "bexi-telegram"
OFFSET_FILE = BRIDGE_DIR / ".offset"
HISTORY_FILE = BRIDGE_DIR / "history.jsonl"
PID_FILE = BRIDGE_DIR / ".pid"
MAX_HISTORY = 10  # son kac mesaj tutulacak (kisa-sureli hafiza, cift sayida iyi olur)


def _read_env(key: str) -> str:
    env_path = ARK_DIR / "litellm" / ".env"
    for line in env_path.read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return ""


BOT_TOKEN = _read_env("TELEGRAM_BOT_TOKEN")
CHAT_ID = _read_env("TELEGRAM_CHAT_ID")


def acquire_lock() -> None:
    # Ayni script'in iki kopyasi ayni offset/history dosyasini paylasarak
    # calisirsa mesajlar yaris durumunda kayboluyor/tekrarlaniyor - tek
    # instance garantisi icin PID kilidi.
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            os.kill(old_pid, 0)  # istisna atmazsa surec hala yasiyor
            print(f"[bexi-telegram] zaten calisiyor (PID {old_pid}), cikiliyor", flush=True)
            sys.exit(1)
        except (ValueError, ProcessLookupError, PermissionError):
            pass  # eski/gecersiz kilit - devam et
    PID_FILE.write_text(str(os.getpid()))


def get_offset() -> int:
    try:
        return int(OFFSET_FILE.read_text().strip())
    except (FileNotFoundError, ValueError):
        return 0


def save_offset(offset: int) -> None:
    OFFSET_FILE.write_text(str(offset))


def load_history() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    lines = HISTORY_FILE.read_text().strip().splitlines()
    return [json.loads(line) for line in lines if line]


def append_history(role: str, text: str) -> list[dict]:
    history = load_history()
    history.append({"role": role, "text": text})
    history = history[-MAX_HISTORY:]
    HISTORY_FILE.write_text("\n".join(json.dumps(h, ensure_ascii=False) for h in history) + "\n")
    return history


def format_history(history: list[dict]) -> str:
    if not history:
        return ""
    lines = ["Bu Telegram sohbetindeki SON birkac mesaj (kisa-sureli hafiza):"]
    for h in history:
        who = "Kullanici" if h["role"] == "user" else "Bexi (sen)"
        lines.append(f"{who}: {h['text']}")
    return "\n".join(lines) + "\n\n"


def poll_telegram(offset: int) -> list[dict]:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?timeout=50&offset={offset}"
    with urllib.request.urlopen(url, timeout=60) as resp:
        data = json.load(resp)
    return data.get("result", [])


def send_telegram(text: str) -> None:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    urllib.request.urlopen(url, data=payload, timeout=30)


def ask_claude(prompt: str) -> str:
    result = subprocess.run(
        ["claude", "-p", prompt, "--permission-mode", "auto"],
        cwd=str(ARK_DIR),
        capture_output=True,
        text=True,
        timeout=300,
    )
    return result.stdout.strip() or result.stderr.strip() or "(bos cevap)"


def _supabase_count(table: str, filter_qs: str = "") -> int:
    url = _read_env("SUPABASE_URL")
    key = _read_env("SUPABASE_SECRET_KEY")
    qs = f"?select=id{('&' + filter_qs) if filter_qs else ''}"
    req = urllib.request.Request(
        f"{url}/rest/v1/{table}{qs}",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Prefer": "count=exact",
            "Range": "0-0",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        content_range = resp.headers.get("Content-Range", "*/0")
    return int(content_range.split("/")[-1])


def generate_agent_status() -> str:
    # "durum nedir" hizli yolu: gercek Supabase verisiyle diger ajanlarin
    # (Ajan 1 pipeline + dm-qualifier sohbetleri) durumunu ANINDA raporlar.
    try:
        businesses = _supabase_count("businesses")
        leads = _supabase_count("leads")
        convos = _supabase_count("conversations")
        tier_pm = _supabase_count("leads", "sales_tier=eq.potansiyel_musteri")
        tier_po = _supabase_count("leads", "sales_tier=eq.potansiyel_olabilir")
        tier_ss = _supabase_count("leads", "sales_tier=eq.soguk_satis")
        tier_sm = _supabase_count("leads", "sales_tier=eq.sadece_merak")
    except Exception as exc:
        return f"Durum sorgulanamadi: {exc}"

    lines = [f"ARK durum - {time.strftime('%d.%m.%Y %H:%M')}"]
    lines.append(f"Ajan 1: {businesses} isletme toplandi, {leads} lead skorlandi (surekli dongu calisiyor)")
    lines.append("")
    if convos == 0:
        lines.append("dm-qualifier: henuz kimseyle konusmadi (WhatsApp/Chatwoot baglantisi bekliyor - s3-1/s3-2)")
    else:
        lines.append(f"dm-qualifier: {convos} mesaj, {tier_pm} satisa donuk (potansiyel musteri), "
                      f"{tier_po} randevu asamasinda (potansiyel olabilir), "
                      f"{tier_ss} isitilmaya calisiliyor (soguk satis), {tier_sm} soguk/sessiz (sadece merak)")
    return "\n".join(lines)


def generate_summary() -> str:
    # Kullanici "1" yazinca agir bir `claude -p` cagrisi (30-60sn) yerine
    # README checklist durumu + son commitleri okuyup ANINDA ozet donduruyoruz.
    readme_lines = (ARK_DIR / "README.md").read_text(encoding="utf-8").splitlines()
    done = sum(1 for l in readme_lines if l.strip().startswith("- [x]"))
    partial = sum(1 for l in readme_lines if l.strip().startswith("- [~]"))
    todo = sum(1 for l in readme_lines if l.strip().startswith("- [ ]"))

    log = subprocess.run(
        ["git", "log", "--oneline", "-5"],
        cwd=str(ARK_DIR),
        capture_output=True,
        text=True,
        timeout=10,
    )
    commits = [c for c in log.stdout.strip().splitlines() if c]

    lines = [f"ARK ozet - {time.strftime('%d.%m.%Y %H:%M')}"]
    lines.append(f"Checklist: {done} tamam, {partial} yarim, {todo} bekliyor")
    if commits:
        lines.append("")
        lines.append("Son commitler:")
        lines.extend(f"- {c}" for c in commits)
    return "\n".join(lines)


def main() -> None:
    acquire_lock()
    try:
        run()
    finally:
        PID_FILE.unlink(missing_ok=True)


def run() -> None:
    print(f"[bexi-telegram] baslatildi {time.ctime()}, PID {os.getpid()}", flush=True)
    offset = get_offset()
    while True:
        try:
            results = poll_telegram(offset)
        except Exception as exc:
            print(f"[bexi-telegram] poll hatasi: {exc}", flush=True)
            time.sleep(5)
            continue

        for update in results:
            offset = update["update_id"] + 1
            save_offset(offset)
            text = update.get("message", {}).get("text", "")
            if not text:
                continue
            print(f"[bexi-telegram] {time.ctime()} yeni mesaj: {text}", flush=True)

            history = append_history("user", text)

            normalized = text.strip().lower()
            if normalized == "1":
                # Hizli yol: agir agentic cagriyi atla, ozet aninda uretilsin.
                reply = generate_summary()
            elif normalized in ("durum nedir", "durum ne", "2"):
                # Hizli yol: diger ajanlarin (Ajan 1 + dm-qualifier) durumunu
                # gercek Supabase verisiyle aninda raporla.
                reply = generate_agent_status()
            else:
                context = format_history(history[:-1])
                prompt = (
                    f"{context}"
                    f'Telegram\'dan Bexi\'ye (ARK Intelligence Labs asistanina) yeni mesaj: "{text}"\n\n'
                    "Once README.md'yi oku, projenin guncel durumunu anla. Yukaridaki kisa-sureli "
                    "sohbet gecmisini dikkate al (orn. 'evet' gibi bir cevap onceki soruya cevaptir). "
                    "Mesaj bir soruya cevapsa veya islem talebiyse geregini yap (dosya duzenle, "
                    "script calistir, git commit/push - projenin yerlesik kurallarina uy). "
                    "Cevabini KISA ve NET Turkce yaz, WhatsApp mesaji gibi - uzun rapor degil."
                )
                reply = ask_claude(prompt)

            append_history("assistant", reply)
            send_telegram(reply)
            print(f"[bexi-telegram] {time.ctime()} cevap gonderildi", flush=True)


if __name__ == "__main__":
    main()
