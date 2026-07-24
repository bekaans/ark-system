#!/usr/bin/env python3
"""ARK - saatlik Telegram durum notu (tek yonlu, LLM cagrisi YOK - en ucuz yol).

Telegram'dan gelen mesajlari DINLEMEZ / cevap yazmaz - sadece her saat basi
kisa bir not gonderir: bu saat ne tamamlandi, su an ne uzerinde calisiliyor,
chatbot musteri kalitesi (sales_tier sayilari). Tum veriler dogrudan
Supabase REST'ten cekilir - `claude -p` cagrisi yok, token maliyeti yok.

Kullanim:
  nohup python3 ~/ark-system/agents/bexi-telegram/hourly_digest.py \
    > ~/ark-system/agents/bexi-telegram/digest.log 2>&1 &
  disown
"""

import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ARK_DIR = Path(__file__).resolve().parent.parent.parent
INTERVAL_SECONDS = 3600


def _read_env(key: str) -> str:
    env_path = ARK_DIR / "litellm" / ".env"
    for line in env_path.read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return ""


BOT_TOKEN = _read_env("TELEGRAM_BOT_TOKEN")
CHAT_ID = _read_env("TELEGRAM_CHAT_ID")


def _supabase_count(table: str, qs: str) -> int:
    url = _read_env("SUPABASE_URL")
    key = _read_env("SUPABASE_SECRET_KEY")
    req = urllib.request.Request(
        f"{url}/rest/v1/{table}?{qs}",
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


def _supabase_sum(table: str, qs: str, field: str) -> tuple[int, float]:
    # Range 0-9999 ile PostgREST'in varsayilan 1000 satir kesmesinden kacinilir
    # (ajan1/score_leads.py'da daha once tam da bu yuzden lead kaybolmustu).
    url = _read_env("SUPABASE_URL")
    key = _read_env("SUPABASE_SECRET_KEY")
    req = urllib.request.Request(
        f"{url}/rest/v1/{table}?select={field}&{qs}",
        headers={"apikey": key, "Authorization": f"Bearer {key}", "Range": "0-9999"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        rows = json.loads(resp.read())
    total = sum((r.get(field) or 0) for r in rows)
    return len(rows), total


def _fmt_tl(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def send_telegram(text: str) -> None:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    urllib.request.urlopen(url, data=payload, timeout=30)


def build_digest() -> str:
    since_hour = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
    local_midnight = datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    since_day = local_midnight.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    try:
        biz_hour = _supabase_count("businesses", f"select=id&created_at=gte.{since_hour}")
        biz_day = _supabase_count("businesses", f"select=id&created_at=gte.{since_day}")
        leads_hour = _supabase_count("leads", f"select=id&created_at=gte.{since_hour}")
        leads_day = _supabase_count("leads", f"select=id&created_at=gte.{since_day}")
        convos_hour = _supabase_count("conversations", f"select=id&created_at=gte.{since_hour}")
        convos_day = _supabase_count("conversations", f"select=id&created_at=gte.{since_day}")
        scrape_hour = _supabase_count(
            "scrape_progress", f"select=id&status=eq.done&scraped_at=gte.{since_hour}"
        )
        scrape_day = _supabase_count(
            "scrape_progress", f"select=id&status=eq.done&scraped_at=gte.{since_day}"
        )
        scrape_pending = _supabase_count("scrape_progress", "select=id&status=eq.pending")

        leads_total = _supabase_count("leads", "select=id")
        leads_tier_eski = _supabase_count("leads", "select=id&tier=eq.eski_sistem")
        leads_tier_orta = _supabase_count("leads", "select=id&tier=eq.ortalama")
        leads_tier_iyi = _supabase_count("leads", "select=id&tier=eq.iyi")

        count_pm, sum_pm = _supabase_sum("leads", "sales_tier=eq.potansiyel_musteri", "estimated_deal_value")
        count_po, sum_po = _supabase_sum("leads", "sales_tier=eq.potansiyel_olabilir", "estimated_deal_value")
        count_ss, sum_ss = _supabase_sum("leads", "sales_tier=eq.soguk_satis", "estimated_deal_value")
        count_k, sum_k = _supabase_sum("leads", "sales_tier=eq.kararsiz", "estimated_deal_value")
    except Exception as exc:
        return f"ARK saatlik ozet alinamadi: {exc}"

    lines = [f"ARK saatlik ozet - {datetime.now().strftime('%H:%M')}", ""]

    lines.append("Bu saat tamamlanan (bugun toplam):")
    lines.append(f"- Yeni isletme: {biz_hour} (bugun: {biz_day})")
    lines.append(f"- Tamamlanan sektor/sehir taramasi: {scrape_hour} (bugun: {scrape_day})")
    lines.append(f"- Skorlanan lead: {leads_hour} (bugun: {leads_day})")
    lines.append(f"- Yeni chatbot mesaji: {convos_hour} (bugun: {convos_day})")

    lines.append("")
    lines.append("Su an uzerinde calisiliyor:")
    if scrape_pending:
        lines.append(f"- isletme taramasi devam ediyor ({scrape_pending} sektor/sehir kaldi)")
    else:
        lines.append("- planli tarama tamamlandi, yeni dongu bekleniyor")

    lines.append("")
    lines.append(f"Toplam lead (tier'e gore) - {leads_total}:")
    lines.append(f"- Eski sistem: {leads_tier_eski}")
    lines.append(f"- Ortalama: {leads_tier_orta}")
    lines.append(f"- Iyi: {leads_tier_iyi}")

    lines.append("")
    lines.append("Chatbot musteri kalitesi (satisa donerse potansiyel kazanc):")
    lines.append(f"- Yuksek ihtimal alici (potansiyel musteri+olabilir): {count_pm + count_po} musteri - {_fmt_tl(sum_pm + sum_po)} TL")
    lines.append(f"- Isitiliyor (soguk satis): {count_ss} musteri - {_fmt_tl(sum_ss)} TL")
    lines.append(f"- Ilgili (kararsiz): {count_k} musteri - {_fmt_tl(sum_k)} TL")
    lines.append(f"- Toplam potansiyel: {_fmt_tl(sum_pm + sum_po + sum_ss + sum_k)} TL")

    return "\n".join(lines)


def main() -> None:
    print(f"[hourly-digest] baslatildi {time.ctime()}, PID bilgisi log'da tutulmuyor", flush=True)
    while True:
        digest = build_digest()
        try:
            send_telegram(digest)
            print(f"[hourly-digest] {time.ctime()} gonderildi", flush=True)
        except Exception as exc:
            print(f"[hourly-digest] gonderim hatasi: {exc}", flush=True)
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
