"""
ARK - score_conversations.py'daki gereklilik-tabanli sales_tier algoritmasi
icin regresyon testleri (2026-07-19).

Harici bagimlilik/DB baglantisi gerektirmez - sadece classify_sales_tier()'i
sentetik mesajlarla cagirir. Yeni bir sinyal/regex eklenince bu dosya
calistirilip mevcut senaryolarin kirilmadigi dogrulanmali.

Kullanim:
  python agents/ajan2/test_score_conversations.py
"""

from score_conversations import classify_sales_tier, missing_requirements, _detect

CASES = [
    ("bos mesaj", [], "sadece_merak"),
    ("soguk/ilgisiz", ["ilgilenmiyorum tesekkurler"], "sadece_merak"),
    ("sadece detay sorusu", ["nasil bir sey bu?"], "kararsiz"),
    ("itiraz/tereddut", ["dusunecegim, biraz pahali geldi"], "soguk_satis"),
    ("randevu istegi ama hicbir gereklilik yok", ["randevu alabilir miyiz?"], "potansiyel_olabilir"),
    (
        "randevu + sistemi biliyor + istiyor ama sorun/arayis yok",
        ["evet biliyorum boyle animasyonlu site nasil calisiyor anladim, istiyorum, randevu alalim"],
        "potansiyel_olabilir",
    ),
    (
        "randevu + 3 gereklilik de var (tam potansiyel musteri)",
        [
            "sitem cok eski ve musteri gelmiyor, boyle hareketli bir site istiyorum, "
            "anladim nasil calisiyor, randevu alabilir miyiz?"
        ],
        "potansiyel_musteri",
    ),
    ("dogrudan kapanis sinyali", ["tamam anlastik, iban bilginizi atar misiniz"], "potansiyel_musteri"),
    (
        "daha once yaptirmis bonus sinyali + tam gereklilik",
        [
            "eskiden bir sitem vardi ama cok eskidi, musteri azaldi, boyle bir sey "
            "istiyorum anladim nasil oldugunu, randevu alalim"
        ],
        "potansiyel_musteri",
    ),
    (
        "tam aksanli 'müşteri' (Turkce karakter regresyonu)",
        ["müşteri gelmiyor artık, biraz zayıflık var"],
        "kararsiz",
    ),
    (
        "coklu mesajda soguk sinyal (re.MULTILINE regresyonu)",
        ["merhaba, fiyat bilgisi almak istiyordum", "yok"],
        "sadece_merak",
    ),
]


def main() -> None:
    failures = 0
    for name, messages, expected in CASES:
        tier, _score, _action = classify_sales_tier(messages)
        ok = tier == expected
        failures += 0 if ok else 1
        status = "OK" if ok else f"HATA (beklenen={expected})"
        print(f"[{status}] {name} -> {tier}")
        if messages:
            gaps = missing_requirements(_detect("\n".join(messages)))
            if gaps:
                print(f"    eksik gereklilikler: {gaps}")

    print()
    if failures:
        print(f"{failures}/{len(CASES)} test BASARISIZ.")
        raise SystemExit(1)
    print(f"Tum {len(CASES)} test gecti.")


if __name__ == "__main__":
    main()
