"""
ARK - s3-5: Randevu -> takvim otomasyonu.

Musteri dm-qualifier sohbetinde randevu asamasina (sales_tier=potansiyel_
olabilir/potansiyel_musteri) geldiginde, botun "ne zaman uygunsunuz" gibi
ACIK UCLU bir soru sormak YERINE (turkce-nlp-satis-hitabet SKILL.md'nin
"SPESIFIK bir gun/saat oner" kurali) somut 2-3 musait saat onermesini
saglar. Musteri birini secince, o saat gercekten Google Takvim'e islenir.

Google Calendar API kullanilir (ucretsiz, standart kullanimda faturalama
gerekmez). OAuth giris akisi YOK - bunun yerine bir SERVIS HESABI (service
account) kullanilir: ARK'in "Randevular" adinda ayri bir Google Takvimi
olusturulur, bu takvim servis hesabinin e-postasiyla (Duzenleyebilir
yetkisiyle) PAYLASILIR, script o servis hesabi uzerinden okur/yazar.

Kurulum (bir kereye mahsus, kullanicinin yapmasi gerekir):
  1. https://console.cloud.google.com -> yeni proje (veya mevcut ARK
     projesi) -> "Google Calendar API"yi etkinlestir.
  2. IAM & Admin -> Service Accounts -> yeni servis hesabi olustur ->
     JSON anahtar indir.
  3. Google Takvim'de "Randevular" adinda yeni bir takvim olustur, Ayarlar
     -> "Kisilerle paylas" -> servis hesabinin e-postasini (xxx@xxx.iam.
     gserviceaccount.com) "Etkinlikleri duzenleme ve yonetme" yetkisiyle
     ekle. Takvim ID'sini (Ayarlar sayfasinda "Takvimi Entegre Et"
     altinda) kopyala.
  4. litellm/.env'e ekle:
       GOOGLE_SERVICE_ACCOUNT_JSON=<indirilen JSON dosyasinin TAM icerigi, tek satir>
       GOOGLE_CALENDAR_ID=<3. adimdaki takvim ID'si>

Bu modul PURE MANTIK (compute_free_slots, format_slot_offer) ile GERCEK
API cagrilari (fetch_busy_periods, book_appointment) AYRI tutulacak
sekilde yazildi - boylece gercek Google kimlik bilgisi olmadan da mantik
test_calendar_booking.py ile dogrulanabiliyor.

Kullanim:
  # Musteriye onerilecek 2 saati goster (sohbete yapistirilacak metin)
  python agents/ajan2/calendar_booking.py --action offer

  # Musteri "yarin 14:00 olur" dedikten SONRA o saati kesinlestir
  python agents/ajan2/calendar_booking.py --action book \
    --start "2026-07-21T14:00:00" --customer-name "Ahmet Bey" \
    --customer-phone "+905551234567" --notes "Guven Oto Galeri - S tier gorusme"
"""

import argparse
import os
from datetime import datetime, timedelta, time as dtime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "litellm" / ".env")

TZ = ZoneInfo("Europe/Istanbul")
BUSINESS_HOURS = (9, 18)   # 09:00-18:00
BUSINESS_DAYS = {0, 1, 2, 3, 4, 5}  # Pazartesi(0)-Cumartesi(5), Pazar(6) kapali
SLOT_MINUTES = 60
DAYS_AHEAD = 7


def compute_free_slots(
    busy_periods: list[tuple[datetime, datetime]],
    now: datetime,
    days_ahead: int = DAYS_AHEAD,
    business_hours: tuple[int, int] = BUSINESS_HOURS,
    slot_minutes: int = SLOT_MINUTES,
) -> list[datetime]:
    """SAF MANTIK - gercek API cagrisi yapmaz, test edilebilir.

    busy_periods: [(baslangic, bitis), ...] - takvimde zaten dolu araliklar.
    Donen liste, is saatleri + is gunleri icinde, hicbir busy_period ile
    CAKISMAYAN slot_minutes'lik bosluklarin baslangic zamanlaridir,
    kronolojik sirada.
    """
    free: list[datetime] = []
    start_hour, end_hour = business_hours

    for day_offset in range(days_ahead):
        day = (now + timedelta(days=day_offset)).date()
        if day == now.date() and now.hour >= end_hour:
            continue  # bugunun mesaisi zaten bitmis

        weekday = datetime.combine(day, dtime(0, 0), tzinfo=TZ).weekday()
        if weekday not in BUSINESS_DAYS:
            continue

        slot_start = datetime.combine(day, dtime(start_hour, 0), tzinfo=TZ)
        day_end = datetime.combine(day, dtime(end_hour, 0), tzinfo=TZ)

        while slot_start + timedelta(minutes=slot_minutes) <= day_end:
            slot_end = slot_start + timedelta(minutes=slot_minutes)
            # Bugunse ve saat gecmisse atla (en az 2 saat sonrasini oner).
            if day == now.date() and slot_start < now + timedelta(hours=2):
                slot_start += timedelta(minutes=slot_minutes)
                continue
            overlaps = any(slot_start < b_end and slot_end > b_start for b_start, b_end in busy_periods)
            if not overlaps:
                free.append(slot_start)
            slot_start += timedelta(minutes=slot_minutes)

    return free


_GUN_ADLARI = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]


def _format_tr(dt: datetime, now: datetime) -> str:
    gun = _GUN_ADLARI[dt.weekday()]
    if dt.date() == now.date():
        prefix = "Bugün"
    elif dt.date() == (now + timedelta(days=1)).date():
        prefix = "Yarın"
    else:
        prefix = gun
    return f"{prefix} saat {dt.strftime('%H:%M')}"


def format_slot_offer(slots: list[datetime], now: datetime, n: int = 2) -> str:
    """Musteriye gonderilecek KISA, SPESIFIK 2-3 secenekli teklif metni
    (turkce-nlp-satis-hitabet SKILL.md - acik uclu soru degil, somut
    gun/saat onerisi kurali)."""
    chosen = slots[:n]
    if not chosen:
        return "Onumuzdeki gunlerde musait bir saat bulamadim, birazdan tekrar kontrol edeyim."
    if len(chosen) == 1:
        return f"{_format_tr(chosen[0], now)} sizin icin uygun mu?"
    formatted = " veya ".join(_format_tr(s, now) for s in chosen)
    return f"{formatted} sizin icin uygun mu?"


def _get_calendar_service():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        raise SystemExit(
            "[ARK] GOOGLE_SERVICE_ACCOUNT_JSON litellm/.env'de tanimli degil - "
            "kurulum icin bu dosyanin ustundeki docstring'e bak."
        )
    import json

    info = json.loads(raw)
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/calendar"]
    )
    return build("calendar", "v3", credentials=creds)


def fetch_busy_periods(calendar_id: str, now: datetime, days_ahead: int = DAYS_AHEAD) -> list[tuple[datetime, datetime]]:
    service = _get_calendar_service()
    time_min = now.isoformat()
    time_max = (now + timedelta(days=days_ahead)).isoformat()
    body = {"timeMin": time_min, "timeMax": time_max, "items": [{"id": calendar_id}]}
    result = service.freebusy().query(body=body).execute()
    busy_raw = result["calendars"][calendar_id]["busy"]
    return [
        (datetime.fromisoformat(b["start"]), datetime.fromisoformat(b["end"]))
        for b in busy_raw
    ]


def book_appointment(
    calendar_id: str,
    start: datetime,
    customer_name: str,
    customer_phone: str,
    notes: str = "",
    duration_minutes: int = SLOT_MINUTES,
) -> str:
    """Takvime GERCEK etkinlik yazar, olusturulan etkinligin ID'sini dondurur."""
    service = _get_calendar_service()
    end = start + timedelta(minutes=duration_minutes)
    event = {
        "summary": f"ARK Randevu - {customer_name}",
        "description": f"Telefon: {customer_phone}\n{notes}".strip(),
        "start": {"dateTime": start.isoformat(), "timeZone": "Europe/Istanbul"},
        "end": {"dateTime": end.isoformat(), "timeZone": "Europe/Istanbul"},
    }
    created = service.events().insert(calendarId=calendar_id, body=event).execute()
    return created["id"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--action", required=True, choices=["offer", "book"])
    parser.add_argument("--start", help="book icin: ISO tarih-saat, orn. 2026-07-21T14:00:00")
    parser.add_argument("--customer-name")
    parser.add_argument("--customer-phone")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    calendar_id = os.environ.get("GOOGLE_CALENDAR_ID")
    if not calendar_id:
        print("[ARK] GOOGLE_CALENDAR_ID litellm/.env'de tanimli degil.")
        raise SystemExit(1)

    now = datetime.now(TZ)

    if args.action == "offer":
        busy = fetch_busy_periods(calendar_id, now)
        slots = compute_free_slots(busy, now)
        print(format_slot_offer(slots, now))
    else:
        if not args.start or not args.customer_name or not args.customer_phone:
            print("[ARK] --action book icin --start, --customer-name, --customer-phone zorunlu.")
            raise SystemExit(1)
        start = datetime.fromisoformat(args.start).replace(tzinfo=TZ)
        event_id = book_appointment(calendar_id, start, args.customer_name, args.customer_phone, args.notes)
        print(f"[ARK] Randevu olusturuldu: {event_id}")


if __name__ == "__main__":
    main()
