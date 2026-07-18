"""
ARK - Ajan 1, gorev 10 (tamamlama): dijital gerilik orani + opportunity_score.

Her sektor icin audits tablosundan "zayif site" oranini hesaplar
(animasyonsuz VEYA SEO skoru dusuk), business_volume ile carpip
opportunity_score uretir, sirali ilk 20'yi yazdirir.

CPC adimi (Google Ads) ertelendi - formul bu ikisiyle ilerliyor.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "litellm" / ".env")


def _fetch_all(supabase, table: str, select: str) -> list[dict]:
    # PostgREST sunucu tarafinda sayfa basina azami 1000 satirla siniirli -
    # Range basligina ne yazilirsa yazilsin. business_id icin .in_() kullanip
    # yuzlerce UUID'yi URL'ye gomen onceki yaklasim (score_sectors.py'da kalabalik
    # sektorlerde "JSON could not be generated" 400 hatasina yol aciyordu -
    # proxy katmani asiri uzun URL'yi reddedip JSON olmayan govde donduruyordu)
    # bu yuzden butun tabloyu sayfalayip Python tarafinda birlestiriyoruz.
    rows: list[dict] = []
    offset = 0
    page_size = 1000
    while True:
        page = (
            supabase.table(table)
            .select(select)
            .range(offset, offset + page_size - 1)
            .execute()
            .data
        )
        rows.extend(page)
        if len(page) < page_size:
            break
        offset += page_size
    return rows


def main() -> None:
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])

    sectors = supabase.table("sectors").select("id,nace_code,name,business_volume").execute().data
    businesses = _fetch_all(supabase, "businesses", "id,sector_id")
    audits = _fetch_all(supabase, "audits", "business_id,has_animation,seo_score")

    business_to_sector = {b["id"]: b["sector_id"] for b in businesses if b["sector_id"]}
    audits_by_sector: dict[str, list[dict]] = {}
    for a in audits:
        sector_id = business_to_sector.get(a["business_id"])
        if sector_id:
            audits_by_sector.setdefault(sector_id, []).append(a)

    results = []
    for sector in sectors:
        sector_audits = audits_by_sector.get(sector["id"], [])
        if not sector_audits:
            continue

        weak_count = sum(
            1 for a in sector_audits if not a["has_animation"] and (a["seo_score"] or 0) < 60
        )
        weakness_ratio = weak_count / len(sector_audits)
        volume = sector["business_volume"] or 0
        # basit skor: hacim (normalize, /100) x zayiflik orani x 100
        opportunity_score = round((volume / 100) * weakness_ratio * 100, 1)

        results.append(
            {
                "id": sector["id"],
                "nace_code": sector["nace_code"],
                "name": sector["name"],
                "audited": len(sector_audits),
                "weakness_ratio": round(weakness_ratio, 2),
                "volume": volume,
                "opportunity_score": opportunity_score,
            }
        )

        supabase.table("sectors").update(
            {
                "digital_weakness_ratio": round(weakness_ratio, 2),
                "opportunity_score": opportunity_score,
            }
        ).eq("id", sector["id"]).execute()

    results.sort(key=lambda r: r["opportunity_score"], reverse=True)

    print(f"[ARK] {len(results)} sektor puanlandi. Ilk 20:\n")
    print(f"{'kod':6} {'skor':>6} {'gerilik':>8} {'hacim':>6} {'denetim':>8}  isim")
    for r in results[:20]:
        print(
            f"{r['nace_code']:6} {r['opportunity_score']:>6} {r['weakness_ratio']:>8} "
            f"{r['volume']:>6} {r['audited']:>8}  {r['name']}"
        )


if __name__ == "__main__":
    main()
