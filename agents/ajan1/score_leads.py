"""
ARK - Ajan 1, gorev 13: Lead puanlama + Tier atamasi.

Sadece ilk 20 sektordeki (weight=1.0) isletmeler degerlendirilir.
lead_score = zayiflik sinyali (sitesi yok/kotu = yuksek firsat) agirlikli
+ buyukluk sinyali (yorum sayisi = gercek/aktif isletme gostergesi).

Esikler: 80+ "eski_sistem", 60-79 "ortalama", altinda "iyi".

(2026-07-19: harf-tabanli Tier A/B/C isimleri KALKTI - website urun tier'i
olan B/A/S/S+ ile karisiyordu. Yeni isimler musterinin MEVCUT durumunu
tanimliyor: "eski_sistem" = su anki sitesi/sistemi eski-kotu (= bizim icin
EN YUKSEK firsat), "ortalama" = orta, "iyi" = su anki sitesi zaten iyi
(= bizim icin EN DUSUK firsat, muhtemelen satmasi en zor grup).)

Tahmini anlasma degeri s3-9'daki gercek fiyat kademelerine gore (2026-07-19
itibariyla B=10-15k/A=15-20k/S=20-25k/S+=25-45k TL, eski 3D/7D isimleri
kalkti) lead-tier basina KARISIK/beklenen deger olarak atanir - hangi
musterinin hangi website tier'ini (B/A/S/S+) alacagi konusma sirasinda
belli oldugu icin bu bir tahmindir, kesin deger degil.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "litellm" / ".env")

# "eski_sistem": en yuksek firsatli isletmeler (su anki siteleri kotu/yok),
# ust website tier'lerine (S/S+) daha yatkin beklenir. "iyi": butce
# hassasiyeti daha yuksek gruptan cok, zaten iyi bir sitesi olan grup -
# satmasi en zor, alt website tier'lerine (B/A) daha yatkin beklenir.
# (2026-07-19: B/A/S/S+ fiyat araliklarinin orta noktalarina gore guncellendi.)
DEFAULT_DEAL_VALUE = {"eski_sistem": 30000, "ortalama": 20000, "iyi": 13000}


def tier_for(score: float) -> str:
    if score >= 80:
        return "eski_sistem"
    if score >= 60:
        return "ortalama"
    return "iyi"


def main() -> None:
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])

    top_sectors = supabase.table("sectors").select("id").eq("weight", 1.0).execute().data
    top_sector_ids = [s["id"] for s in top_sectors]
    print(f"[ARK] {len(top_sector_ids)} sektordeki isletmeler degerlendirilecek.")

    # PostgREST varsayilan olarak tek istekte en fazla 1000 satir donduruyor -
    # .range() ile sayfalamadan tek .execute() cagirmak isletmeleri SESSIZCE
    # kirpiyordu (2243 isletme varken sadece ilk 1000'i islenmisti). Simdi
    # tumunu alana kadar sayfalayarak cekiyoruz.
    businesses = []
    page_size = 1000
    offset = 0
    while True:
        page = (
            supabase.table("businesses")
            .select("id,sector_id,website")
            .in_("sector_id", top_sector_ids)
            .range(offset, offset + page_size - 1)
            .execute()
            .data
        )
        businesses.extend(page)
        if len(page) < page_size:
            break
        offset += page_size
    print(f"[ARK] {len(businesses)} isletme bulundu.")

    # audits'i business_id -> audit eslemesi olarak yukle
    business_ids = [b["id"] for b in businesses]
    audits_raw = []
    batch = 200
    for i in range(0, len(business_ids), batch):
        chunk = business_ids[i : i + batch]
        audits_raw.extend(
            supabase.table("audits")
            .select("business_id,has_animation,seo_score")
            .in_("business_id", chunk)
            .execute()
            .data
        )
    audit_by_business = {a["business_id"]: a for a in audits_raw}

    counts = {"eski_sistem": 0, "ortalama": 0, "iyi": 0}
    rows_to_insert = []

    for biz in businesses:
        audit = audit_by_business.get(biz["id"])
        if audit is None:
            weakness = 100 if not biz.get("website") else 70  # site yok=en yuksek firsat, denetlenmedi ama var=orta
        elif not audit["has_animation"] and (audit["seo_score"] or 0) < 60:
            weakness = 90
        else:
            weakness = 20

        # buyukluk sinyali icin veri yok (review_count import edilmedi), sabit orta deger kullan
        size_signal = 50

        lead_score = round(0.7 * weakness + 0.3 * size_signal, 1)
        tier = tier_for(lead_score)
        counts[tier] += 1

        rows_to_insert.append(
            {
                "business_id": biz["id"],
                "sector_id": biz["sector_id"],
                "lead_score": lead_score,
                "tier": tier,
                "estimated_deal_value": DEFAULT_DEAL_VALUE[tier],
            }
        )

    batch = 200
    for i in range(0, len(rows_to_insert), batch):
        supabase.table("leads").upsert(
            rows_to_insert[i : i + batch], on_conflict="business_id"
        ).execute()

    print(f"[ARK] {len(rows_to_insert)} lead yazildi. Tier dagilimi: {counts}")


if __name__ == "__main__":
    main()
