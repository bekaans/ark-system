"""
ARK - calendar_booking.py'daki SAF MANTIK (compute_free_slots, format_slot_offer)
icin regresyon testleri. Gercek Google API/kimlik bilgisi GEREKTIRMEZ - sadece
sentetik busy_periods ile calisir.

Kullanim:
  python agents/ajan2/test_calendar_booking.py
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from calendar_booking import compute_free_slots, format_slot_offer

TZ = ZoneInfo("Europe/Istanbul")
# Sabit bir "simdi": Pazartesi 2026-07-20, saat 08:00 (mesai henuz baslamamis).
NOW = datetime(2026, 7, 20, 8, 0, tzinfo=TZ)


def test_bos_gun_9_slot_uretir():
    # "Bugunku 2-saat-sonrasi" filtresiyle karismamasi icin YARINI kontrol
    # ediyoruz (bugun icin ayri test: test_bugunku_yakin_saatler_atlaniyor).
    slots = compute_free_slots([], NOW, days_ahead=2)
    yarin_slots = [s for s in slots if s.date() == (NOW + timedelta(days=1)).date()]
    assert len(yarin_slots) == 9, f"beklenen 9 slot (09-18 arasi 1'er saat), gelen: {len(yarin_slots)}"
    assert yarin_slots[0].hour == 9
    assert yarin_slots[-1].hour == 17


def test_dolu_saat_atlaniyor():
    yarin = (NOW + timedelta(days=1)).date()
    busy = [(datetime(yarin.year, yarin.month, yarin.day, 11, 0, tzinfo=TZ),
             datetime(yarin.year, yarin.month, yarin.day, 12, 0, tzinfo=TZ))]
    slots = compute_free_slots(busy, NOW, days_ahead=2)
    yarin_slots = [s for s in slots if s.date() == yarin]
    hours = [s.hour for s in yarin_slots]
    assert 11 not in hours, f"11:00 dolu olmasina ragmen slot listesinde: {hours}"
    assert len(yarin_slots) == 8


def test_pazar_gunu_slot_yok():
    # 2026-07-19 bir Pazar (NOW'dan 1 gun ONCE, ama ileriye donuk test icin
    # NOW'u Cumartesi yapip 1 gun sonrasini (Pazar) kontrol edelim.
    cumartesi = datetime(2026, 7, 25, 8, 0, tzinfo=TZ)  # Cumartesi
    assert cumartesi.weekday() == 5
    slots = compute_free_slots([], cumartesi, days_ahead=2)
    pazar_slots = [s for s in slots if s.weekday() == 6]
    assert pazar_slots == [], f"Pazar gunu slot uretilmemeli, gelen: {pazar_slots}"


def test_bugunku_yakin_saatler_atlaniyor():
    # Simdi 08:00, "en az 2 saat sonrasi" kurali -> 09:00 ve 10:00 slotlari
    # ATLANMALI (08:00+2sa=10:00, yani 10:00'a esit slotlar dahil edilir mi
    # kontrolu icin >= degil > kullanildigindan 09:00 kesin, 10:00 sinirda).
    slots_today = [s for s in compute_free_slots([], NOW, days_ahead=1) if s.date() == NOW.date()]
    assert all(s.hour >= 10 for s in slots_today), f"cok yakin saatler filtrelenmemis: {[s.hour for s in slots_today]}"


def test_offer_iki_secenek_formati():
    slots = [datetime(2026, 7, 21, 14, 0, tzinfo=TZ), datetime(2026, 7, 23, 11, 0, tzinfo=TZ)]
    text = format_slot_offer(slots, NOW, n=2)
    assert "veya" in text
    assert "14:00" in text and "11:00" in text
    assert text.endswith("uygun mu?")


def test_offer_tek_secenek_formati():
    slots = [datetime(2026, 7, 21, 14, 0, tzinfo=TZ)]
    text = format_slot_offer(slots, NOW, n=2)
    assert "veya" not in text
    assert "14:00" in text


def test_offer_bos_liste_fallback():
    text = format_slot_offer([], NOW)
    assert "musait bir saat bulamadim" in text


def test_offer_yarin_etiketi():
    yarin = NOW + timedelta(days=1)
    slots = [yarin.replace(hour=14, minute=0)]
    text = format_slot_offer(slots, NOW)
    assert text.startswith("Yarın"), f"beklenen 'Yarın' etiketi, gelen: {text}"


TESTS = [
    test_bos_gun_9_slot_uretir,
    test_dolu_saat_atlaniyor,
    test_pazar_gunu_slot_yok,
    test_bugunku_yakin_saatler_atlaniyor,
    test_offer_iki_secenek_formati,
    test_offer_tek_secenek_formati,
    test_offer_bos_liste_fallback,
    test_offer_yarin_etiketi,
]


def main() -> None:
    failures = 0
    for test in TESTS:
        try:
            test()
            print(f"[OK] {test.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"[HATA] {test.__name__}: {exc}")

    print()
    if failures:
        print(f"{failures}/{len(TESTS)} test BASARISIZ.")
        raise SystemExit(1)
    print(f"Tum {len(TESTS)} test gecti.")


if __name__ == "__main__":
    main()
